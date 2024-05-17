from pydantic import BaseModel, AwareDatetime
from enum import Enum
from pydantic import BaseModel, model_validator
from typing_extensions import Self
from db import *
from functools import cache
from pydantic import NonNegativeInt, PositiveInt, Field, IPvAnyAddress, validator
from typing import Any, Dict, TypeVar, Generic
import asyncio, re2

class AttackMode(Enum):
    WAIT_FOR_TIME_TICK = "wait-for-time-tick"
    TICK_DELAY = "tick-delay"
    LOOP_DELAY = "loop-delay"

class SetupStatus(Enum):
    SETUP = "setup"
    RUNNING = "running"

class Configuration(BaseModel):
    FLAG_REGEX: str = ""
    
    START_TIME: AwareDatetime|None = None
    END_TIME: AwareDatetime|None = None
    TICK_DURATION: PositiveInt = 120
    
    ATTACK_MODE: AttackMode = AttackMode.TICK_DELAY
    LOOP_ATTACK_DELAY: NonNegativeInt = 0
    ATTACK_TIME_TICK_DELAY: NonNegativeInt = 0
    
    FLAG_TIMEOUT: PositiveInt|None = None
    FLAG_SUBMIT_LIMIT: PositiveInt|None = None
    SUBMIT_DELAY: NonNegativeInt = 0
    SUBMITTER: NonNegativeInt|None = None
    SUBMITTER_TIMEOUT: PositiveInt|None = 30
    
    AUTHENTICATION_REQUIRED: bool = False
    PASSWORD_HASH: str|None = None
    
    SETUP_STATUS: SetupStatus = SetupStatus.SETUP    
    
    @property
    def login_enabled(self):
        return self.AUTHENTICATION_REQUIRED and self.SETUP_STATUS != SetupStatus.SETUP

    @model_validator(mode='after')
    def __model_checking(self) -> Self:
        try:
            re2.compile(self.FLAG_REGEX)
        except re2.error as e:
            raise ValueError('invalid flag regex', str(e))
        if self.SETUP_STATUS == SetupStatus.RUNNING: #Checks only on running set
            if not self.FLAG_REGEX:
                raise ValueError('flag regex must be set')
            if self.SUBMITTER is None:
                raise ValueError('a submitter must be set')
            if self.RUN_MODE == AttackMode.WAIT_FOR_TIME_TICK:
                if self.START_TIME is None or self.END_TIME is None:
                    raise ValueError('start and end time must be set')
                if self.TICK_DURATION is None:
                    raise ValueError('tick duration must be set')
            elif self.RUN_MODE == AttackMode.TICK_DELAY:
                if self.TICK_DURATION is None:
                    raise ValueError('tick duration must be set')
            if self.AUTHENTICATION_REQUIRED and self.PASSWORD_HASH is None:
                raise ValueError('password hash must be set')
        return self

    @staticmethod
    @cache
    def keys():
        return list(Configuration().model_dump().keys())

    @transactional
    async def write_on_db(self):
        await dbconf.database.execute("LOCK TABLE envs IN ACCESS EXCLUSIVE MODE")
        values = self.model_dump(mode="json")
        async def key_create_or_update(k, v):
            value = None if v is None else str(v)
            try:
                await Env.objects.update_or_create(key=k, value=value)
            except ormar.NoMatch:
                await Env(key=k, value=value).save()
        await asyncio.gather(*[key_create_or_update(k, v) for k, v in values.items()])
    
    @classmethod
    async def get_from_db(cls) -> Self:
        keys = Configuration.keys()
        result = await Env.objects.filter(Env.key << keys).all()
        result = {ele.key:ele.value for ele in result}
        return cls(**result)

class StatusAPI(BaseModel):
    status: SetupStatus
    loggined: bool
    config: Configuration|None = None
    server_time: AwareDatetime

class ResponseStatus(Enum):
    OK = "ok"
    ERROR = "error"
    INVALID = "invalid"

ResponseType = TypeVar('ResponseType', bound="MessageResponse")

class MessageResponse(BaseModel, Generic[ResponseType]):
    status: ResponseStatus = ResponseStatus.OK
    message: str|None = None
    response: ResponseType|None = None

###-- Submitter Models --###

class SubmitterDTO(BaseModel):
    id: int
    name: str
    code: bytes
    kargs: Dict[str, Dict[str, Any]] = {}
    created_at: AwareDatetime

class SubmitterAddForm(BaseModel):
    name: str = Field("", min_length=1)
    code: bytes
    kwargs: Dict[str, Any]|None = None

class SubmitterEditForm(BaseModel):
    name: str|None = Field(None, min_length=1)
    kwargs: Dict[str, Any]|None = None

###-- Services Models --###

class ServiceDTO(BaseModel):
    id: int
    name: str

class ServiceAddForm(BaseModel):
    name: str

class ServiceEditForm(BaseModel):
    name: str|None = None

###-- Teams Models --###

class TeamDTO(BaseModel):
    id: int
    name: str|None
    short_name: str|None
    host: IPvAnyAddress
    created_at: AwareDatetime

class TeamAddForm(BaseModel):
    name: str|None = None
    short_name: str|None = None
    host: IPvAnyAddress

class TeamEditForm(BaseModel):
    id: int
    name: str|None = None
    short_name: str|None = None
    host: IPvAnyAddress|None = None

###-- Client Models --###

class ClientDTO(BaseModel): #Client id will be hashed before returning to make it secret (it's a soft secret, not a real one)
    id: str                 #Using the hash we can only delete the client, but not edit it
    name: str|None = None
    address: IPvAnyAddress|None = None
    created_at: AwareDatetime
    
class ClientAddForm(BaseModel):
    id: UUID
    name: str|None = None
    address: IPvAnyAddress|None = None

class ClientEditForm(BaseModel):
    name: str|None = None
    address: IPvAnyAddress|None = None
