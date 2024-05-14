from dotenv import load_dotenv
load_dotenv()

import uvicorn
import os, asyncio
from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from jose import jwt
import time
from fastapi.middleware.cors import CORSMiddleware
from submitter import run_submitter
from utils import crypto
from env import DEBUG, CORS_ALLOW, JWT_ALGORITHM, JWT_EXPIRE_H
from fastapi.responses import FileResponse
from db import *
from models import *
from utils import APP_SECRET
from fasteners import InterProcessLock

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)
app = FastAPI(debug=DEBUG, redoc_url=None, lifespan=lifespan)

def create_lock(name:str):
    base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".locks")
    if not os.path.exists(base_path): os.makedirs(base_path)
    return InterProcessLock(os.path.join(base_path, name+".lock"))

config_lock = create_lock("config")

async def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = int(time.time() + JWT_EXPIRE_H*60*60) #3h
    encoded_jwt = jwt.encode(to_encode, await APP_SECRET(), algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def is_loggined(token: str = Depends(oauth2_scheme)):
    
    #App status checks
    config = await Configuration.get_from_db()

    if not config.login_enabled:
        return True
    
    #If the app is running and requires login
    if not token:
        return None
    try:
        payload = jwt.decode(token, await APP_SECRET(), algorithms=[JWT_ALGORITHM])
        authenticated: bool = payload.get("authenticated", False)
        return authenticated
    except Exception:
        return False

async def check_login(token: str = Depends(oauth2_scheme)):
    status = is_loggined(token)
    if status is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif status:
        return True
    else:
        raise HTTPException(
            status_code=401,
            detail="Token is expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

api = APIRouter(prefix="/api", dependencies=[Depends(check_login)])
def assert_setup_or_login(is_loggined: bool = Depends(is_loggined)):
    return not is_loggined

@app.post("/login", tags=["auth"])
async def login_api(form: OAuth2PasswordRequestForm = Depends()):
    """Get a login token to use the firegex api"""
    if form.password == "" or form.username == "":
        raise HTTPException(400,"Cannot insert an empty value!")
    await asyncio.sleep(0.3) # No bruteforce :)
    user = None# search user
    if not user:
        raise HTTPException(406,"User not found!")
    if not crypto.verify(form.password, user.password):
        raise HTTPException(406,"Wrong password!")
    return {"access_token": await create_access_token({"authenticated":True}), "token_type": "bearer"}

@app.get("/api/status", response_model=StatusAPI, tags=["status"])
async def get_status(is_loggined: bool = Depends(is_loggined)):
    """ This will return the application status, and the configuration if the user is allowed to see it """
    config = await Configuration.get_from_db()
    loggined = not config.login_enabled or is_loggined
    return StatusAPI(status=config.SETUP_STATUS, loggined=loggined, config=(config if loggined else None))

@api.post("setup", response_model=MessageResponse, tags=["status"])
@dbtransaction()
async def set_status(data: Dict[str, str|int|None]):
    with config_lock:
        config = await Configuration.get_from_db()
        queries = []
        for key, value in data.items():
            if key not in Configuration.keys():
                raise HTTPException(400, f"Invalid key {key}")
            
            if key == "SETUP_STATUS" and config.SETUP_STATUS != SetupStatus.SETUP:
                raise HTTPException(400, "Setup status cannot be changed back to setup")
            setattr(config, key, value)
            queries.append(Env.objects.update_or_create(key=key, value=value))
        config.model_validate()
        await asyncio.gather(*queries)
    return {"status": ResponseStatus.OK, "message": "The configuration has been updated"}

app.include_router(api)

if not DEBUG:
    @app.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path:str):
        file_request = os.path.join("frontend", full_path)
        if not os.path.isfile(file_request):
            return FileResponse("frontend/index.html", media_type='text/html')
        else:
            return FileResponse(file_request)

if DEBUG or CORS_ALLOW:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if __name__ == '__main__':
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    os.environ["TIMEOUT"] = "30"
    init_db()
    submitter = run_submitter()
    try:
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8080,
            reload=DEBUG,
            access_log=True,
            workers=3
        )
    finally:
        submitter.terminate()
        submitter.join()
