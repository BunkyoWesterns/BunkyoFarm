
import os, secrets
from aiocache import cached

VERSION = "{{VERSION_PLACEHOLDER}}"
DEBUG = os.getenv("DEBUG", "").lower() in ["true", "1", "t"]
CORS_ALLOW = os.getenv("CORS_ALLOW", "").lower() in ["true", "1", "t"]

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_H = 3

POSTGRES_USER = os.getenv("POSTGRES_USER", "exploitfarm")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "exploitfarm")
POSTGRES_DB = os.getenv("POSTGRES_DB", "exploitfarm")

@cached()
async def APP_SECRET():
    secret = None # Get from maybe env or db secret
    secret = secret.value if secret else None
    if secret is None:
        secret = secrets.token_hex(32)
        #... Write permanently the secret
    return secret