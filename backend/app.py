from dotenv import load_dotenv
load_dotenv()

import uvicorn
import os, asyncio
from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from jose import jwt
from models import *
import time
from fastapi.middleware.cors import CORSMiddleware
from submitter import run_submitter

from utils import crypto
from env import DEBUG, CORS_ALLOW, JWT_ALGORITHM, APP_SECRET, JWT_EXPIRE_H
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    #Init actions
    yield
    #Shutdown actions

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)
app = FastAPI(debug=DEBUG, redoc_url=None, lifespan=lifespan)

async def create_access_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = int(time.time() + JWT_EXPIRE_H*60*60) #3h
    encoded_jwt = jwt.encode(to_encode, await APP_SECRET(), algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def check_login(token: str = Depends(oauth2_scheme)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, await APP_SECRET(), algorithms=[JWT_ALGORITHM])
        userid: str|None = payload.get("userid", None)
        if not userid:
            raise HTTPException(
                status_code=401,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        return None
    raise HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

def mongo_dict_update(base:str, target:dict):
    res = {}
    for k, v in target.items():
        res[base+"."+k] = v
    return res

api = APIRouter(prefix="/api", dependencies=[Depends(check_login)])

@api.post("/login", tags=["auth"])
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
    return {"access_token": await create_access_token({"userid": user.id.binary.hex(), "role": user.role}), "token_type": "bearer"}

@api.get("/example", response_model=list[str], tags=["example"])
async def get_example():
    """ Example api """
    return ["Hello", "World"]

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
