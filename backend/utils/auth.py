from models.config import Configuration
from db import APP_SECRET
from env import JWT_ALGORITHM
import jwt
from models.enums import AuthStatus

async def login_validation(token: str|None) -> AuthStatus:
    
    #App status checks
    config = await Configuration.get_from_db()

    if not config.login_enabled:
        return AuthStatus.ok
    
    #If the app is running and requires login
    if not token:
        return AuthStatus.nologin
    
    try:
        payload = jwt.decode(token, await APP_SECRET(), algorithms=[JWT_ALGORITHM])
        authenticated: bool = payload.get("authenticated", False)
        if authenticated:
            return AuthStatus.ok
        else:
            return AuthStatus.wrong
    except Exception:
        return AuthStatus.invalid