import socketio
import asyncio
import uvloop
import traceback
import logging
from env import DEBUG
from multiprocessing import Process
from db import close_db, redis_conn, REDIS_CHANNEL_PUBLISH_LIST, connect_db, redis_channels
from utils.auth import login_validation, AuthStatus
from socketio.exceptions import ConnectionRefusedError
from exploitfarm.models.groups import JoinRequest
from exploitfarm.models.response import MessageResponse
from exploitfarm.models.groups import JoinRequestResponse, GroupResponseEvent
from utils import register_event
import time
from utils.redis_pipe import redis_call

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
    group, client = await redis_conn.mget(f"sid:{sid}:group", f"sid:{sid}:client")
    if isinstance(group, bytes):
        group = group.decode()
    if isinstance(client, bytes):
        client = client.decode()
    await redis_conn.lrem("sid_list", 0, sid)
    if group and client:
        await redis_call(redis_conn, "leave-group", sid, group, client)

@register_event(sio_server, "event-group", GroupResponseEvent, MessageResponse)
async def event_group(sid: str, response_req: GroupResponseEvent):
    return await redis_call(redis_conn, "event-group", sid, response_req)
    
@register_event(sio_server, "join-group", JoinRequest, MessageResponse[JoinRequestResponse])
async def join_group(sid, join_req: JoinRequest):
    return await redis_call(redis_conn, "join-group", sid, join_req)

async def disconnect_all():
    while True:
        sids = await redis_conn.lpop("sid_list", count=100)
        if sids is None or len(sids) == 0:
            break
        for sid in sids:
            if isinstance(sid, bytes):
                sid = sid.decode()
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


async def tasks_init():
    try:
        await connect_db()
        await generate_listener_tasks()
        pwd_change = asyncio.create_task(password_change_listener())
        logging.info("SocketIO manager started")
        await asyncio.gather(*g.task_list, pwd_change)
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