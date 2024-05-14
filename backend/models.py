from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, model_validator
from typing_extensions import Self
from db import *
import asyncio
from functools import cache

class AttackMode(Enum):
    WAIT_FOR_TIME_TICK = "wait-for-time-tick"
    LOOP = "loop"
    TICK_TIMEOUT = "tick-timeout"
    CUSTOM_TIMEOUT = "custom-timeout"

class SetupStatus(Enum):
    SETUP = "setup"
    RUNNING = "running"

class Configuration(BaseModel):
    FLAG_REGEX: str = ""
    
    START_TIME: datetime|None = None
    END_TIME: datetime|None = None
    TICK_DURATION: int = 120
    
    CUSTOM_ATTACK_TIMEOUT: int|None = None 
    ATTACK_MODE: AttackMode = AttackMode.WAIT_FOR_TIME_TICK
    
    FLAG_SUBMIT_LIMIT: int|None = None
    SUBMIT_TIMEOUT: int|None = None
    
    AUTHENTICATION_REQUIRED: bool = False
    PASSWORD_HASH: str|None = None
    
    SETUP_STATUS: SetupStatus = SetupStatus.SETUP
    
    SUBMITTER: int|None = None
    
    @property
    def login_enabled(self):
        return self.AUTHENTICATION_REQUIRED and self.SETUP_STATUS != SetupStatus.SETUP
    
    @model_validator(mode='after')
    def check_logical_integrity(self) -> Self:
        if self.SETUP_STATUS == SetupStatus.RUNNING: #Checks only on running set
            if self.SUBMITTER is None:
                raise ValueError('a submitter must be set')
            if self.RUN_MODE == AttackMode.WAIT_FOR_TIME_TICK:
                if self.START_TIME is None or self.END_TIME is None:
                    raise ValueError('start and end time must be set')
                if self.TICK_DURATION is None:
                    raise ValueError('tick duration must be set')
            elif self.RUN_MODE == AttackMode.TICK_TIMEOUT:
                if self.TICK_DURATION is None:
                    raise ValueError('tick duration must be set')
            elif self.RUN_MODE == AttackMode.CUSTOM_TIMEOUT:
                if self.CUSTOM_ATTACK_TIMEOUT is None:
                    raise ValueError('custom timeout must be set')
            if self.AUTHENTICATION_REQUIRED and self.PASSWORD_HASH is None:
                raise ValueError('password hash must be set')
        return self

    @staticmethod
    @cache
    def keys():
        return list(Configuration().model_dump().keys())
    
    @staticmethod
    @cache
    def default_options():
        return Configuration().model_dump()

    async def write_on_db(self):
        keys = Configuration.keys()
        await asyncio.gather(*[Env.objects.update_or_create(key=k, value=str(getattr(self, k)))for k in keys])
    
    @classmethod
    async def get_from_db(cls) -> Self:
        default_object = Configuration.default_options()
        keys = default_object.keys()
        result = await asyncio.gather(*[Env.objects.get_or_none(key=k) for k in keys])
        result = [(k, v) for k, v in zip(keys, result)]
        result = dict([(k, v.value if v is not None else default_object[k]) for k, v in result ])
        return cls(**result)

class StatusAPI(BaseModel):
    status: SetupStatus
    loggined: bool
    config: Configuration|None = None

class ResponseStatus(Enum):
    OK = "ok"
    ERROR = "error"
    INVALID = "invalid"
    
class MessageResponse(BaseModel):
    status: ResponseStatus
    message: str|None = None
    response: dict|None = None
    

