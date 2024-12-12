from redis.asyncio import Redis
from functools import wraps
import pickle
import asyncio
from typing import Callable
import traceback

async def redis_call(redis_conn: Redis, func_name: str, *args, **kwargs):
    params = pickle.dumps({
        "args": args,
        "kwargs": kwargs
    })
    await redis_conn.publish(f"redis-pipe:call:{func_name}", params)
    async with redis_conn.pubsub() as pubsub:
        await pubsub.subscribe(f"redis-pipe:recv-call:{func_name}")
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
            if message:
                data = pickle.loads(message["data"])
                if data["ok"]:
                    return data["result"]
                raise Exception(data["error"])

class RedisCallHandler:
    def __init__(self, redis_conn: Redis):
        self.__redis_pipe_tasks = []
        self.tasks = []
        self.redis_conn = redis_conn
    
    def call_handler(self, func_name: str):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            self.__redis_pipe_tasks.append(
                (func_name, func)
            )
            return wrapper
        return decorator
    
    async def __redis_call_handler(self, func_name: str, handle: Callable):
        async with self.redis_conn.pubsub() as pubsub:
            await pubsub.subscribe(f"redis-pipe:call:{func_name}")
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=None)
                if message:
                    data = pickle.loads(message["data"])
                    try:
                        result = await handle(*data["args"], **data["kwargs"])
                        await self.redis_conn.publish(f"redis-pipe:recv-call:{func_name}", pickle.dumps({
                            "ok": True,
                            "result": result
                        }))
                    except Exception as e:
                        await self.redis_conn.publish(f"redis-pipe:recv-call:{func_name}", pickle.dumps({
                            "ok": False,
                            "error": e
                        }))
                        traceback.print_exc()
    
    def create_tasks(self):
        self.tasks = [asyncio.create_task(self.__redis_call_handler(func_name, func)) for func_name, func in self.__redis_pipe_tasks]
        return self.tasks


