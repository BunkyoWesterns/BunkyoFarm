
import asyncio
import uvloop
from db import close_db, redis_conn
from db import connect_db, redis_channels
from db import dbtransaction, sqla
import math
from asyncio import Queue
from dateutil import parser as dtparser
from dataclasses import dataclass
from datetime import timedelta, datetime
from exploitfarm.models.enums import AttackMode
from exploitfarm.models.groups import JoinRequest, GroupEventRequestType, GroupRequestEvent
from exploitfarm.models.response import ResponseStatus
from exploitfarm.models.groups import GroupResponseEvent, GroupEventResponseType
from db import Team
from utils import json_like, datetime_now
import time
from models.config import Configuration
from workers.skio import sio_server
import logging
import traceback
from multiprocessing import Process
from utils.redis_pipe import RedisCallHandler
from exploitfarm.models.teams import TeamDTO

class StopLoop(Exception):
    pass

rpc_redis = RedisCallHandler(redis_conn)

class g:
    group_attack_managers: dict[str, "GroupAttackManager"] = {}
    configuration: Configuration = None
    teams: list[Team] = []
    task_list = []

async def disconnect_client(group_id: str, client: str):
    if isinstance(group_id, bytes):
        group_id = group_id.decode()
    if isinstance(client, bytes):
        client = client.decode()
    sid = await redis_conn.get(f"group:{group_id}:client:{client}:sid")
    if isinstance(sid, bytes):
        sid = sid.decode()
    if sid:
        await sio_server.disconnect(sid)

@dataclass
class ClinetAttackerStatus:
    client_id: str
    sid: str
    queue_size: int
    used_queues: int = 0
    attack_start_time: datetime|None = None
    
    def prio_assign(self, min_factor: int) -> float:
        return (self.queue_size - self.used_queues) / min_factor

    def assign(self, target: "AttackTargetStatus"):
        self.used_queues += 1
        target.assigned_to = self.client_id
        self.attack_start_time = datetime_now()
    
    def end(self, target: "AttackTargetStatus"):
        self.used_queues -= 1
        target.executed = True
    
    def reset(self):
        self.used_queues = 0
        self.attack_start_time = None
        
    def delta_from_start(self):
        if self.attack_start_time:
            return datetime_now() - self.attack_start_time
        return timedelta(seconds=0)

@dataclass
class AttackTargetStatus:
    target: str
    data: dict
    executed: bool = False
    assigned_to: str|None = None
    
    def reset(self):
        self.executed = False
        self.assigned_to = None

def current_tick_calc():
    this_time = datetime_now()
    start_time = g.configuration.START_TIME
    if start_time > this_time:
        raise Exception("Attack not started yet")
    return math.floor((this_time - start_time).total_seconds() / g.configuration.TICK_DURATION)

def calc_round_time_available():
    #Needed to calculate the initial time based on attack schedule logic
    this_time = datetime_now()
    match g.configuration.ATTACK_MODE:
        case AttackMode.TICK_DELAY:
            return g.configuration.TICK_DURATION
        case AttackMode.WAIT_FOR_TIME_TICK:
            start_time = g.configuration.START_TIME
            next_tick = current_tick_calc() + 1
            next_time = start_time + timedelta(seconds=g.configuration.TICK_DURATION * next_tick) + timedelta(seconds=g.configuration.ATTACK_TIME_TICK_DELAY)
            return (next_time - this_time).total_seconds()
        case AttackMode.LOOP_DELAY:
            return g.configuration.LOOP_ATTACK_DELAY

class GroupAttackManager:
    
    TIMEOUT_SEND_INTERVAL = 5
    
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.queue = Queue()
        self.running = False
        self.timeout = 0
        self.deadline = datetime_now()
        self.tot_time_available = 0
        self.task = asyncio.create_task(self.__task())
        
        self.last_timeout_sent = 0
        self.last_timeout_value_sent = 0
        
        self.client_table: dict[str, ClinetAttackerStatus] = {}
        self.attack_target_table: dict[str, AttackTargetStatus] = {}
        self.__generate_attack_targets()
        
        self.current_virtual_time = 0
    
    def __generate_attack_targets(self):
        for ele in g.teams:
            self.attack_target_table[ele.host] = AttackTargetStatus(
                target=ele.host,
                data=TeamDTO.model_dump(ele, mode="python", exclude_unset=False)
            )
    
    def time_to_wait_for_next_timeout(self) -> int:
        return max(0, self.TIMEOUT_SEND_INTERVAL - (time.time() - self.last_timeout_sent))
    
    def time_to_wait_for_next_loop(self) -> int:
        return max(0, self.deadline.timestamp() - time.time())
    
    async def timeout_update_handle(self):
        if self.time_to_wait_for_next_timeout() <= 0:
            if self.last_timeout_value_sent != self.timeout:
                await sio_server.send(
                    json_like(GroupRequestEvent(
                        event=GroupEventRequestType.DYNAMIC_TIMEOUT,
                        group_id=self.group_id,
                        data={ "timeout": self.timeout }
                    )),
                    room=f"group:{self.group_id}:room"
                )
                self.last_timeout_value_sent = self.timeout
            self.last_timeout_sent = time.time()       
    
    async def send_deadline_update(self):
        await sio_server.send(
            json_like(GroupRequestEvent(
                event=GroupEventRequestType.DEADLINE_TIMOEOUT,
                group_id=self.group_id,
                data={ "deadline": self.deadline.isoformat() }
            )),
            room=f"group:{self.group_id}:room"
        )
    
    async def send_running_status(self):
        await sio_server.send(
            json_like(GroupRequestEvent(
                event=GroupEventRequestType.RUNNING_STATUS,
                group_id=self.group_id,
                data={ "running": self.running }
            )),
            room=f"group:{self.group_id}:room"
        )
    
    async def send_killall_request(self):
        await sio_server.send(
            json_like(GroupRequestEvent(
                event=GroupEventRequestType.KILLALL_ATTACKS,
                group_id=self.group_id
            )),
            room=f"group:{self.group_id}:room"
        )
    
    async def wait_next_loop(self):
        timeout = min(
            self.time_to_wait_for_next_timeout(),
            self.time_to_wait_for_next_loop()
        ) if self.running else None
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except TimeoutError:
            return None
    
    async def trigger_attack_start(self, client_id: str, target: dict):
        await sio_server.send(
            json_like(GroupRequestEvent(
                event=GroupEventRequestType.ATTACK_REQUEST,
                group_id=self.group_id,
                data={ "target": target }
            )),
            to=self.client_table[client_id].sid
        )
    
    async def recalculate_timeout(self, trigger_skio_update: bool = False, update_on_redis: bool = True, reset_virtual_time: bool = False):
        if reset_virtual_time:
            self.current_virtual_time = sum(ele.queue_size*self.tot_time_available for ele in self.client_table.values())
        if len(g.teams) == 0:
            self.timeout = 0
        else:
            self.timeout = min(math.ceil(self.current_virtual_time / len(g.teams)), g.configuration.TICK_DURATION)
        if update_on_redis:
            await self.write_data()
        if trigger_skio_update:
            self.last_timeout_sent = 0
            await self.timeout_update_handle()
    
    def calc_client_status(self) -> list[tuple[float, ClinetAttackerStatus]]:
        if len(self.client_table) == 0:
            return []
        min_factor = min([ele.queue_size for ele in self.client_table.values()])
        client_status = [(ele.prio_assign(min_factor), ele) for ele in self.client_table.values()]
        client_status.sort(key=lambda x: x[0], reverse=True)
        return client_status
    
    async def handle_attack_run_managment(self):
        #handle starting of next attack loop
        if self.time_to_wait_for_next_loop() <= 0:
            # Kill all eventually running attacks
            await self.send_killall_request()
            # Reset all attack targets info
            for ele in self.attack_target_table.values():
                ele.reset()
            # Reset all client info
            for ele in self.client_table.values():
                ele.reset()
            # Recalculate deadline and send it to clients
            self.tot_time_available = calc_round_time_available()
            self.deadline = datetime_now() + timedelta(seconds=self.tot_time_available)
            await self.send_deadline_update()
            # Recalculate timeout and send it to clients
            await self.recalculate_timeout(trigger_skio_update=True, reset_virtual_time=True)
        
        teams_to_exec = [ele for ele in self.attack_target_table.values() if not ele.executed and ele.assigned_to is None]
        
        if len(teams_to_exec) == 0:
            return
        
        client_status = self.calc_client_status()
        
        if len(client_status) == 0:
            if self.running:
                self.running = False
                await self.write_data()
            return # No client available, need someone to join
        
        if client_status[0][0] == 0:
            return # No more client available, waiting

        # 1st assign phase: multiple attack assignment
        for prio, client in client_status:
            if prio < 1:
                break # Will be eventually handled in the next assign phase
            for _ in range(math.floor(prio)):
                team_to_attack = teams_to_exec.pop()
                client.assign(team_to_attack)
                await self.trigger_attack_start(client.client_id, team_to_attack.data)
                if len(teams_to_exec) == 0:
                    return
        
        client_status = self.calc_client_status()
        
        # 2nd assign phase: single attack assignment
        
        for prio, client in client_status:
            if prio == 0:
                break # No more client available
            team_to_attack = teams_to_exec.pop()
            client.assign(team_to_attack)
            await self.trigger_attack_start(client.client_id, team_to_attack.data)
            if len(teams_to_exec) == 0:
                return
        
        # Can't assign all the attacks, waiting for attacks to end
        
    async def __task(self):
        await self.write_data()
        while True:
            try:
                await self.fetch_data()
                if self.running:
                    await self.timeout_update_handle()
                    await self.handle_attack_run_managment()
                await self.wait_next_loop()
            except Exception as e:
                logging.exception(f"Error in group task for group {self.group_id}: {e}")
                traceback.print_exc()
                await asyncio.sleep(5)
    
    def trigger_next_loop(self, data="trigger"):
        self.queue.put_nowait(data)
    
    async def write_data(self):
        await redis_conn.mset({
            f"group:{self.group_id}:running": 1 if self.running else 0,
            f"group:{self.group_id}:timeout": self.timeout,
            f"group:{self.group_id}:deadline": self.deadline.isoformat(),
            f"group:{self.group_id}": 1
        })
    
    async def fetch_data(self):
        running, timeout, deadline = await redis_conn.mget(
            f"group:{self.group_id}:running",
            f"group:{self.group_id}:timeout",
            f"group:{self.group_id}:deadline"
        )
        self.running = int(running) != 0
        self.timeout = int(timeout)
        self.deadline = dtparser.parse(deadline)
    
    async def handle_request(self, request: GroupResponseEvent):
        match request.event:
            case GroupEventResponseType.SET_RUNNING_STATUS:
                self.running = request.data["running"]
                await self.write_data()
                await self.send_running_status()
                self.trigger_next_loop()
            case GroupEventResponseType.ATTACK_ENDED:
                # Get the client and target
                target = self.attack_target_table[request.data["target"]]
                client = self.client_table[request.client]
                # End the attack
                client.end(target)
                # Add the earned time to the virtual time
                time_used = client.delta_from_start()
                self.current_virtual_time += self.timeout - time_used.total_seconds()
                # Recalculate timeout
                await self.recalculate_timeout()
                # Trigger new assignment
                self.trigger_next_loop()
    
    def delta_until_deadline(self) -> int:
        return self.deadline.timestamp() - time.time()
    
    async def handle_join(self, client_id: str, sid:str, queue_size: int):
        self.client_table[client_id] = ClinetAttackerStatus(
            client_id=client_id,
            sid=sid,
            queue_size=queue_size
        )
        # Insert Join time to virtual time
        self.current_virtual_time += self.delta_until_deadline() * queue_size
        await self.recalculate_timeout(trigger_skio_update=True)
        self.trigger_next_loop()
    
    async def handle_leave(self, client_id: str):
        await disconnect_client(self.group_id, client_id)
        self.current_virtual_time -= self.delta_until_deadline() * self.client_table[client_id].queue_size
        for data in self.attack_target_table.values():
            if not data.executed and data.assigned_to == client_id:
                data.reset()
        del self.client_table[client_id]
        self.trigger_next_loop()
    
    def loop_reset(self):
        self.deadline = datetime_now()
        self.last_timeout_sent = 0
        self.last_timeout_value_sent = 0
        self.current_virtual_time = 0
        self.trigger_next_loop()
    
    async def handle_config_changed(self):
        self.loop_reset()
    
    async def handle_teams_changed(self):
        self.attack_target_table = {}
        self.__generate_attack_targets()
        self.loop_reset()
    
    async def cancel(self):
        self.task.cancel()
        members = await redis_conn.smembers(f"group:{self.group_id}:members")
        group_keys = await redis_conn.keys(f"group:{self.group_id}:*")
        await asyncio.gather(*[disconnect_client(self.group_id, member) for member in members])
        await redis_conn.delete(*group_keys, f"group:{self.group_id}")

async def group_delete(group_id: str):
    await g.group_attack_managers[group_id].cancel()
    del g.group_attack_managers[group_id]

async def generate_group_task(group_id: str) -> GroupAttackManager:
    if isinstance(group_id, bytes):
        group_id = group_id.decode()
    group_id = str(group_id)
    g.group_attack_managers[group_id] = GroupAttackManager(group_id)
    return g.group_attack_managers[group_id]

async def group_changes_listener():
    async with redis_conn.pubsub() as pubsub:
        await pubsub.subscribe(redis_channels.attack_group)
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message:
                message = message["data"].decode()
                if message.startswith("add:"):
                    group_id = message.split(":")[1]
                    await generate_group_task(group_id)
                if message.startswith("delete:"):
                    group_id = message.split(":")[1]
                    await group_delete(group_id)

async def update_config_info():
    g.configuration = await Configuration.get_from_db()
    await asyncio.gather(*[ele.handle_config_changed() for ele in g.group_attack_managers.values()])

async def update_teams_info():
    async with dbtransaction() as db:
        g.teams = list((await db.scalars(sqla.select(Team))).all())
    await asyncio.gather(*[ele.handle_teams_changed() for ele in g.group_attack_managers.values()])

@rpc_redis.call_handler("leave-group")
async def leave_group(sid:str, group: str, client: str):
    keys_to_delete = await redis_conn.keys(f"group:{group}:client:{client}:*")
    sid_associated_keys = await redis_conn.keys(f"sid:{sid}:*")
    await asyncio.gather(
        redis_conn.delete(*keys_to_delete, *sid_associated_keys),
        redis_conn.srem(f"group:{group}:members", client),
        sio_server.leave_room(sid, f"group:{group}:room"),
    )
    await g.group_attack_managers[group].handle_leave(client)
    await redis_conn.publish(redis_channels.attack_group, "leave")

@rpc_redis.call_handler("event-group")
async def event_group(sid: str, response_req: GroupResponseEvent):
    await g.group_attack_managers[str(response_req.group_id)].handle_request(response_req)
    return {"message": "left", "status": ResponseStatus.OK}

@rpc_redis.call_handler("join-group")
async def join_group(sid, join_req: JoinRequest):
    if not await redis_conn.get(f"group:{join_req.group_id}"):
        return {"status": ResponseStatus.ERROR, "message": "Group not found"}
    await asyncio.gather(
        redis_conn.mset({
            f"group:{join_req.group_id}:client:{join_req.client}:queue": int(join_req.queue_size),
            f"group:{join_req.group_id}:client:{join_req.client}:sid": sid,
            f"sid:{sid}:group": str(join_req.group_id),
            f"sid:{sid}:client": join_req.client
        }),
        redis_conn.sadd(f"group:{join_req.group_id}:members", join_req.client),
        sio_server.enter_room(sid, f"group:{join_req.group_id}:room"),
    )
    if g.group_attack_managers.get(str(join_req.group_id)) is None:
        await generate_group_task(join_req.group_id)
    await g.group_attack_managers[str(join_req.group_id)].handle_join(str(join_req.client), sid, join_req.queue_size)
    timeout, deadline, running = await redis_conn.mget(
        f"group:{join_req.group_id}:timeout",
        f"group:{join_req.group_id}:deadline",
        f"group:{join_req.group_id}:running"
    )
    await redis_conn.publish(redis_channels.attack_group, "join")
    return {"message": "joined", "status": ResponseStatus.OK, "response": {
        "timeout": timeout,
        "deadline": deadline,
        "running": running
    }}

async def generate_config_update_tasks():
    await update_config_info()
    await update_teams_info()
    async def listener_config_update():
        async with redis_conn.pubsub() as pubsub:
            await pubsub.subscribe(redis_channels.config)
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
                if message:
                    await update_config_info()
    async def listener_teams_update():
        async with redis_conn.pubsub() as pubsub:
            await pubsub.subscribe(redis_channels.team)
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
                if message:
                    await update_teams_info()
        g.task_list.extend([
            asyncio.create_task(listener_config_update()),
            asyncio.create_task(listener_teams_update())
        ])

async def tasks_init():
    try:
        await connect_db()
        await generate_config_update_tasks()
        redis_tasks = rpc_redis.create_tasks()
        cng_listener = asyncio.create_task(group_changes_listener())
        logging.info("SocketIO manager started")
        await asyncio.gather(cng_listener, *redis_tasks)
        await asyncio.gather(*g.group_attack_managers.items())
    except KeyboardInterrupt:
        pass
    finally:
        await close_db()

def inital_setup():
    try:
        while True:
            try:
                g.task_list = []
                with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
                    runner.run(tasks_init())
            except Exception as e:
                traceback.print_exc()
                logging.exception(f"SocketIO loop failed: {e}, restarting loop")
                time.sleep(10)
    except (KeyboardInterrupt, StopLoop):
        logging.info("SocketIO stopped by KeyboardInterrupt")

def run_group_manager_daemon() -> Process:
    p = Process(target=inital_setup)
    p.start()
    return p
