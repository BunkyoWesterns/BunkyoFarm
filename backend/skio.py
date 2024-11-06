import socketio
import asyncio
import uvloop
import traceback
import logging
from env import DEBUG
from multiprocessing import Process
from db import close_db, redis_conn, REDIS_CHANNEL_LIST, connect_db, dbtransaction, redis_channels
from utils.query import get_exploits_with_latest_attack, detailed_exploit_status
from models.config import Configuration
from models.enums import ExploitStatus

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

class g:
    task_list = []

@sio_server.on("connect")
async def sio_connect(sid, environ): pass

@sio_server.on("disconnect")
async def sio_disconnect(sid): pass

async def generate_listener_tasks():
    for chann in REDIS_CHANNEL_LIST:
        async def listener(chann=chann):
            await sio_server.emit(chann, "init")
            async with redis_conn.pubsub() as pubsub:
                await pubsub.subscribe(chann)
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
                    await sio_server.emit(chann, message)
        g.task_list.append(asyncio.create_task(listener()))

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

async def tasks_init():
    try:
        await connect_db()
        await generate_listener_tasks()
        check_disabled_exploits = asyncio.create_task(check_exploits_disabled())
        logging.info("SocketIO manager started")
        await asyncio.gather(*g.task_list, check_disabled_exploits)
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
    except (KeyboardInterrupt, StopLoop):
        logging.info("SocketIO stopped by KeyboardInterrupt")

def run_skio_daemon() -> Process:
    p = Process(target=inital_setup)
    p.start()
    return p