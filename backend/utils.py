from passlib.context import CryptContext
from aiocache import cached
import secrets
from db import Env
crypto = CryptContext(schemes=["bcrypt"], deprecated="auto")

@cached()
async def APP_SECRET():
    secret = await Env.objects.get_or_none(key="APP_SECRET")
    secret = secret.value if secret else None
    if secret is None:
        secret = secrets.token_hex(32)
        await Env.objects.update_or_create(key="APP_SECRET", value=secret)
    return secret

