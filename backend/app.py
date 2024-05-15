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
from utils import *
from env import DEBUG, CORS_ALLOW, JWT_ALGORITHM, JWT_EXPIRE_H
from fastapi.responses import FileResponse
from db import *
from models import *
from utils import APP_SECRET
from typing import Dict, Literal
from pydantic import ValidationError
import orjson as json
from typing import List


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)
app = FastAPI(debug=DEBUG, redoc_url=None, lifespan=lifespan)

"""
from fasteners import InterProcessLock
def create_lock(name:str):
    base_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".locks")
    if not os.path.exists(base_path): os.makedirs(base_path)
    return InterProcessLock(os.path.join(base_path, name+".lock"))
"""

async def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = int(time.time() + JWT_EXPIRE_H*60*60) #3h
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

async def check_login(status: bool|None = Depends(is_loggined)) -> Literal[True]:
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

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc: ValidationError):
    raise HTTPException(400, json.loads(exc.json()))

api = APIRouter(prefix="/api", dependencies=[Depends(check_login)])

@app.post("/api/login", tags=["auth"])
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
async def get_status(loggined: None|bool = Depends(is_loggined)):
    """ This will return the application status, and the configuration if the user is allowed to see it """
    config = await Configuration.get_from_db()
    if config.PASSWORD_HASH: config.PASSWORD_HASH = "********"
    return StatusAPI(status=config.SETUP_STATUS, loggined=loggined, config=(config if loggined else None))

@api.post("/setup", response_model=MessageResponse, tags=["status"])
async def set_status(data: Dict[str, str|int|None]):
    """ Set some configuration values, you can set the values to change only """
    config = await Configuration.get_from_db()
    
    for key in data.keys():
        if key not in Configuration.keys():
            raise HTTPException(400, f"Invalid key {key}")
        if key == "SETUP_STATUS" and config.SETUP_STATUS != SetupStatus.SETUP:
            raise HTTPException(400, "Setup status cannot be changed back to setup")
        if key == "SUBMITTER":
            if not await Submitter.objects.get_or_none(id=data[key]):
                raise HTTPException(400, "Submitter not found")
        if key == "PASSWORD_HASH":
            data[key] = crypto.hash(data[key])

    await Configuration.model_validate(config.model_dump() | data).write_on_db()
    return {"status": ResponseStatus.OK, "message": "The configuration has been updated"}

@api.post("/submitters", response_model=MessageResponse, tags=["status"])
async def new_submitter(data: SubmitterForm):
    """ Set the submitter code """
    submit_function, error = extract_submit(data.code)
    
    if not submit_function:
        raise HTTPException(400, error)
    
    valid_sig, msg = has_submit_signature(submit_function)
    if not valid_sig: raise HTTPException(400, msg)
    
    kwargs = get_additional_args(submit_function)
    
    #Set custom kwargs
    if data.kwargs:
        for k,v in data.kwargs.items():
            if k not in kwargs.keys():
                raise HTTPException(400, f"Invalid key {k}")
            kwargs[k]["value"] = v
            
    #Check enforced type for kwargs
    for k,v in kwargs.items():
        if not type_check_annotation(v["value"], v["type"]):
            raise HTTPException(400, f"Invalid type for {k} ({v['value']} is not of type {v['type']})")
    
    await Submitter(name=data.name, code=data.code, kargs=kwargs).save()
    
    return {"status": ResponseStatus.OK, "message": "The submitter has been created"}
    
@api.get("/submitters", response_model=List[Submitter], tags=["status"])
async def get_submitters():
    """ Get all the submitters """
    return await Submitter.objects.all()

@api.put("/submitters/{submitter_id}", response_model=MessageResponse, tags=["status"])
async def update_submitter(submitter_id: int, data: SubmitterEditForm):
    if not data.name and not data.kwargs:
        raise HTTPException(400, "You must provide at least one field to update")
    submitter = await Submitter.objects.get_or_none(id=submitter_id)
    if not submitter:
        raise HTTPException(404, "Submitter not found")
    if data.name:
        submitter.name = data.name
    if data.kwargs:
        for k,v in data.kwargs.items():
            if k not in submitter.kargs.keys():
                raise HTTPException(400, f"Invalid key {k}")
            if type_check_annotation(v, submitter.kargs[k]["type"]):
                submitter.kargs[k] = v
            else:
                raise HTTPException(400, f"Invalid type for {k} ({v} is not of type {submitter.kargs[k]['type']})")
    await submitter.update()
    return {"status": ResponseStatus.OK, "message": "The submitter has been updated", "response": submitter.model_dump()}
    

@api.delete("/submitters/{submitter_id}", response_model=MessageResponse, tags=["status"])
async def delete_submitter(submitter_id: int):
    """ Delete a submitter """
    config = await Configuration.get_from_db()
    if config.SUBMITTER == submitter_id:
        raise HTTPException(400, "Cannot delete the currently selected submitter (change it in configuration first)")
    submitter = await Submitter.objects.get_or_none(id=submitter_id)
    if not submitter:
        raise HTTPException(404, "Submitter not found")
    await submitter.delete()
    return {"status": ResponseStatus.OK, "message": "The submitter has been deleted"}

"""
Next Steps:
- Create the submitter process
- Flag submit API (+ attack execution)
- Create/Edit/Delete Services
- Flag GetFlags API / STATS
- Teams Create/Edit/Delete
- AuthKey Gen and Revoke

//more client than web data
- Create/Edit/Delete Exploits
- Client Create/Edit/Delete

Notes:
- managment of output (sending, to server, compression, send only if no flag is submitted)
- client side: exclude some teams
- warning if time is wrong on client
"""


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
