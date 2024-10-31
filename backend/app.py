import uvicorn
import os, asyncio, env
from asyncpg import UniqueViolationError, ForeignKeyViolationError
from fastapi import FastAPI, HTTPException, Depends, APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
import time, jwt
from fastapi.middleware.cors import CORSMiddleware
from submitter import run_submitter_daemon
from stats import run_stats_daemon
from skio import run_skio_daemon
from utils import *
from env import DEBUG, CORS_ALLOW, JWT_ALGORITHM, EXPLOIT_SOURCES_DIR
from fastapi.responses import FileResponse
from models.all import *
from utils import datetime_now, load_routers
from typing import Dict
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from db import connect_db, close_db, init_db, APP_SECRET, SERVER_ID, DBSession, Service, Team, Submitter, sqla, redis_conn, redis_channels
from skio import sio_app

os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.makedirs(EXPLOIT_SOURCES_DIR, exist_ok=True)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    load_routers(api) #Dynamic loading of routers in ./routes folder
    app.include_router(api)
    app.include_router(router)
    yield
    await close_db()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)
app = FastAPI(
    debug=DEBUG,
    redoc_url=None,
    docs_url="/api/docs",
    lifespan=lifespan,
    version=env.VERSION,
    responses={ 422: {"description": "Validation error", "model": MessageResponse[Any]} }
)

async def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    #to_encode["exp"] = int(time.time() + JWT_EXPIRE_H*60*60) #3h
    encoded_jwt = jwt.encode(to_encode, await APP_SECRET(), algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def is_loggined(token: str = Depends(oauth2_scheme)) -> None|bool:
    
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

async def check_login(status: bool|None = Depends(is_loggined)) -> None:
    if status is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif status:
        return None
    else:
        raise HTTPException(
            status_code=401,
            detail="Token is expired or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.exception_handler(UniqueViolationError)
async def unique_violation_error_handler(request, exc: UniqueViolationError):
    error_str = "Some values are already used in this datastructure and cannot be duplicated"
    try:
        if exc.detail:
            details = str(exc.detail)
            key, value = details.split("Key (")[1].split(")=(")[0], details.split(")=(")[1].split(")")[0]
            error_str = f"The value '{value}' is already used in the field '{key}' (unique constraint)"
    except Exception:
        pass
    raise HTTPException(400, error_str)

@app.exception_handler(ForeignKeyViolationError)
async def unique_violation_error_handler(request, exc: ForeignKeyViolationError):
    error_str = "Some references to other datastructures are not valid"
    try:
        if exc.detail:
            details = str(exc.detail)
            key, value = details.split("Key (")[1].split(")=(")[0], details.split(")=(")[1].split(")")[0]
            error_str = f"The value '{value}' is not a valid reference in the field '{key}' or it's value it's used and can't be deleted! (foreign key constraint)"
    except Exception:
        pass
    raise HTTPException(400, error_str)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc:StarletteHTTPException):
    return JSONResponse(json_like(
        MessageResponse(
            status=ResponseStatus.ERROR,
            message=exc.detail,
            response=exc.status_code
        )
    ), status_code=exc.status_code)

@app.exception_handler(MessageResponseInvalidError)
async def message_response_exception_handler(request, exc: MessageResponseInvalidError):
    return JSONResponse(json_like(MessageResponse(
        status=ResponseStatus.INVALID,
        message=exc.message,
        response=exc.response,    
    )), status_code=400)

@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: RequestValidationError|ValidationError):
    if DEBUG:
        traceback.print_exc()
    errors = list(exc.errors())
    for ele in errors:
        if "ctx" in ele:
            del ele["ctx"]
    return JSONResponse(json_like(
        MessageResponse(
            status=ResponseStatus.ERROR,
            message=errors[0]["msg"] if errors else "Invalid request",
            response=errors
        )
    ), status_code=422)

class TrailingSlashMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if  request.url.path.endswith("/") and len(request.url.path) > 1:
            request.scope["path"] = request.url.path[:-1]
        return await call_next(request)

app.add_middleware(TrailingSlashMiddleware)
router = APIRouter()
api = APIRouter(prefix="/api", dependencies=[Depends(check_login)])

@router.post("/api/login", tags=["Auth"])
async def login_api(form: OAuth2PasswordRequestForm = Depends()):
    """Get a login token to use the apis"""
    if form.password == "":
        raise HTTPException(400,"Cannot insert an empty value!")
    await asyncio.sleep(0.3) # No bruteforce :)
    config = await Configuration.get_from_db()
    if not crypto.verify(form.password, config.PASSWORD_HASH):
        raise HTTPException(406,"Wrong password!")
    return {"access_token": await create_access_token({"authenticated":True}), "token_type": "bearer"}

@router.get("/api/status", response_model=StatusAPI, tags=["Status"])
async def get_status(db: DBSession, loggined: bool|None = Depends(is_loggined)):
    """ This will return the application status, and the configuration if the user is allowed to see it """
    config = await Configuration.get_from_db()
    if config.PASSWORD_HASH: config.PASSWORD_HASH = "********"  
    messages = await get_messages_array()
    
    teams_response = None
    services_response = None
    submitter_response = None
    if loggined:
        teams_response = json_like(
            (await db.scalars(sqla.select(Team))).all()
            , unset=True
        )
        services_response = json_like(
            list((await db.scalars(sqla.select(Service))).all())
            , unset=True
        )
        if config.SUBMITTER is not None:
            result = (await db.scalars(sqla.select(Submitter).where(Submitter.id == config.SUBMITTER))).one_or_none()
            submitter_response = json_like(result, unset=True) if result else None

    return StatusAPI(
        status=config.SETUP_STATUS,
        loggined=bool(loggined),
        config=config if loggined else None,
        server_id=await SERVER_ID(),
        server_time=datetime_now(),
        teams = teams_response,
        submitter=submitter_response,
        messages= messages if loggined else None,
        services=services_response,
        start_time=config.start_time,
        end_time=config.end_time
    )

@api.post("/setup", response_model=MessageResponse[Configuration], tags=["Status"])
async def set_status(data: Dict[str, str|int|None], db: DBSession):
    """ Set some configuration values, you can set the values to change only """
    config = await Configuration.get_from_db()
    for key in data.keys():
        if key not in Configuration.keys():
            raise HTTPException(400, f"Invalid key {key}")
        if key == "SETUP_STATUS" and config.SETUP_STATUS != SetupStatus.SETUP and data[key] == SetupStatus.SETUP.value:
            raise HTTPException(400, "Setup status cannot be changed back to setup")
        if key == "SUBMITTER":
            sub_count = (await db.scalars(
                sqla.select(sqla.func.count(Submitter.id)).where(Submitter.id == data[key])
            )).one_or_none()
            if sub_count == 0:
                raise HTTPException(400, "Submitter not found")
        if key == "PASSWORD_HASH" and not data[key] is None:
            if len(str(data[key])) < 8:
                raise HTTPException(400, "Password too short (at least 8 chars)")
            data[key] = crypto.hash(data[key])

    config = Configuration.model_validate(config.model_dump() | data)
    await config.write_on_db()
    config.PASSWORD_HASH = "********" if config.PASSWORD_HASH else None
    await redis_conn.publish(redis_channels.config, "update")
    return {"status": ResponseStatus.OK, "message": "The configuration has been updated", "response": config.model_dump()}


if not DEBUG:
    @router.get("/{full_path:path}", include_in_schema=False)
    async def catch_all(full_path:str):
        if full_path.startswith('api/'): 
            raise HTTPException(400, "Invalid API route")
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

app.mount("/sock", app=sio_app)

if __name__ == '__main__':
    #DO NOT ADD IN lifecycle of FastAPI, it will be spawned more times
    os.environ["TIMEOUT"] = "30"
    os.environ["TZ"] = "Etc/UTC"
    time.tzset()
    asyncio.run(init_db())
    procs = [
        run_submitter_daemon(),
        run_stats_daemon(),
        run_skio_daemon()
    ]
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5050,
        reload=DEBUG,
        access_log=True,
        workers=env.NTHREADS
    )
    for proc in procs:
        proc.terminate()
        proc.join()
        
