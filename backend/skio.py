import socketio
import asyncio
import uvloop
import traceback
import logging
from env import DEBUG
from multiprocessing import Process
from db import close_db, redis_conn, REDIS_CHANNEL_PUBLISH_LIST, connect_db, dbtransaction, redis_channels
from utils.query import get_exploits_with_latest_attack, detailed_exploit_status
from models.config import Configuration
from exploitfarm.models.enums import ExploitStatus
from utils.auth import login_validation, AuthStatus
from socketio.exceptions import ConnectionRefusedError
from exploitfarm.models.groups import JoinRequest, LeaveRequest
from exploitfarm.models.response import MessageResponse, ResponseStatus
from db import AttackGroup, sqla
from utils import register_event
import time

class StopLoop(Exception):
    pass

redis_mgr = socketio.AsyncRedisManager(
    url="redis://localhost:6379/0" if DEBUG else "redis://redis:6379/0",
)
sio_server = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[],
    client_manager=redis_mgr,
    transports=["websocket"],
)

"""
TODO list:
- Capire come gesire i processi che devono gestire il gruppo:
    - come li avvio? - start-group:group_id
    - come li termino? - stop-group:group_id
- Gestione di client:
    - al join inviamo una richiesta al client con le specifiche per l'attacco (timeout e commit)
    - quando questi si aggiornano mandiamo un boradcast delle stesse informazioni nella room associata
- Gestione cambio dimensione queue:
    - ???
- Gestione cambio source:
    - ???
- Gestione messaggi di conclusione degli exploit
- Gestione messaggi di reject per l'avvio di un attacco
- Gestione messaggi di errore (generici)
-     

"""

class g:
    task_list = []
    room_task_list = []
    
async def check_login(token: str) -> None:
    status = await login_validation(token)
    if status == AuthStatus.ok:
        return None
    if status == AuthStatus.nologin:
        raise ConnectionRefusedError("Authentication required")
    raise ConnectionRefusedError("Unauthorized")

@sio_server.on("connect")
async def sio_connect(sid, environ, auth):
    await check_login(auth.get("token"))
    await redis_conn.lpush("sid_list", sid)

@sio_server.on("disconnect")
async def sio_disconnect(sid):
    await redis_conn.lrem("sid_list", 0, sid)

@register_event(sio_server, "leave-group", LeaveRequest, MessageResponse)
async def leave_group(sid, leave_req: LeaveRequest):
    await asyncio.gather(
        redis_conn.delete(*(await redis_conn.keys(f"group:{leave_req.group_id}:client:{leave_req.client}:*"))),
        redis_conn.srem(f"group:{leave_req.group_id}:members", leave_req.client),
        sio_server.leave_room(sid, f"group:{leave_req.group_id}:room")
    )
    return {"message": "left", "status": ResponseStatus.OK}
    
@register_event(sio_server, "join-group", JoinRequest, MessageResponse)
async def join_group(sid, join_req: JoinRequest):
    if not await redis_conn.get(f"group:{join_req.group_id}"):
        return {"status": ResponseStatus.ERROR, "message": "Group not found"}
    await asyncio.gather(
        redis_conn.set(f"group:{join_req.group_id}:client:{join_req.client}:sid", sid),
        redis_conn.set(f"group:{join_req.group_id}:client:{join_req.client}:queue", join_req.queue_size),
        sio_server.enter_room(sid, f"group:{join_req.group_id}:room")
    )
    return {"message": "joined", "status": ResponseStatus.OK}

async def disconnect_all():
    while True:
        sids = await redis_conn.lpop("sid_list", count=100)
        if sids is None or len(sids) == 0:
            break
        for sid in sids:
            await sio_server.disconnect(sid)

async def generate_listener_tasks():
    for chann in REDIS_CHANNEL_PUBLISH_LIST:
        async def listener(chann=chann):
            await sio_server.emit(chann, "init")
            async with redis_conn.pubsub() as pubsub:
                await pubsub.subscribe(chann)
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
                    if message:
                        await sio_server.emit(chann, message)
        g.task_list.append(asyncio.create_task(listener()))

async def password_change_listener():
    async with redis_conn.pubsub() as pubsub:
        await pubsub.subscribe(redis_channels.password_change)
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message:
                await disconnect_all()

async def check_exploits_disabled():
    disabled_exploits = set([])
    async with dbtransaction() as db:
        while True:
            trigger_update = False
            data = await get_exploits_with_latest_attack(db)
            config = await Configuration.get_from_db()
            for ele in data:
                expl, attack = ele.tuple()
                current_status, reason = await detailed_exploit_status(config, attack)
                if current_status == ExploitStatus.disabled and expl.id not in disabled_exploits:
                    disabled_exploits.add(expl.id)
                    trigger_update = reason != "stopped"
                elif current_status != ExploitStatus.disabled and expl.id in disabled_exploits:
                    disabled_exploits.remove(expl.id)
            if trigger_update:
                await db.commit()
                await redis_conn.publish(redis_channels.exploit, "update")
            await asyncio.sleep(5)

async def group_task(group_id: str):
    while True:
        await asyncio.sleep(5)

def generate_group_task(group_id: str):
    task = asyncio.create_task(group_task(group_id))
    g.room_task_list.append({
        "group_id": group_id,
        "task": asyncio.create_task(group_task(group_id))
    })
    return task

async def group_changes_listener():
    async with dbtransaction() as db:
        pre_existing_groups = (await db.scalars(sqla.select(AttackGroup))).all()
        for ele in pre_existing_groups:
            await redis_conn.set(f"group:{ele.id}", 1)
            generate_group_task(ele.id)
        async with redis_conn.pubsub() as pubsub:
            await pubsub.subscribe(redis_channels.attack_group)
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
                if message:
                    message = message["data"].decode()
                    if message.startswith("add:"):
                        group_id = message.split(":")[1]
                        generate_group_task(group_id)
                    if message.startswith("delete:"):
                        group_id = message.split(":")[1]
                        for ele in list(filter(lambda ele: ele["group_id"] == group_id, g.room_task_list)):
                            ele["task"].cancel()
                            g.room_task_list.remove(ele)

async def tasks_init():
    try:
        await connect_db()
        await generate_listener_tasks()
        pwd_change = asyncio.create_task(password_change_listener())
        check_disab = asyncio.create_task(check_exploits_disabled())
        cng_listener = asyncio.create_task(group_changes_listener())
        logging.info("SocketIO manager started")
        await asyncio.gather(*g.task_list, check_disab, pwd_change, cng_listener)
        await asyncio.gather(*g.room_task_list)
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

def run_skio_daemon() -> Process:
    p = Process(target=inital_setup)
    p.start()
    return p