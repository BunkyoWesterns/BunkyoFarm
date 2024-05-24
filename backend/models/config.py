
from pydantic import BaseModel, AwareDatetime
from enum import Enum
from pydantic import BaseModel, model_validator
from typing_extensions import Self
from functools import cache
from pydantic import NonNegativeInt, PositiveInt
from models.submitter import SubmitterDTO
import asyncio, re
from db import *
from models.teams import TeamDTO
from models.response import *
from typing import List

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
    SUBMITTER: SubmitterID|None = None
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
            re.compile(self.FLAG_REGEX)
        except re.error as e:
            raise ValueError('invalid flag regex', str(e))
        if self.SETUP_STATUS == SetupStatus.RUNNING: #Checks only on running set
            if not self.FLAG_REGEX:
                raise ValueError('flag regex must be set')
            if self.SUBMITTER is None:
                raise ValueError('a submitter must be set')
            if self.ATTACK_MODE == AttackMode.WAIT_FOR_TIME_TICK:
                if self.START_TIME is None or self.END_TIME is None:
                    raise ValueError('start and end time must be set')
                if self.TICK_DURATION is None:
                    raise ValueError('tick duration must be set')
            elif self.ATTACK_MODE == AttackMode.TICK_DELAY:
                if self.TICK_DURATION is None:
                    raise ValueError('tick duration must be set')
            if self.AUTHENTICATION_REQUIRED and self.PASSWORD_HASH is None:
                raise ValueError('password hash must be set')
        return self

    @staticmethod
    @cache
    def keys():
        return list(Configuration().model_dump().keys())

    async def write_on_db(self):
        await dbconf.database.execute("LOCK TABLE envs IN ACCESS EXCLUSIVE MODE")
        values = self.model_dump(mode="json")
        async def key_create_or_update(k, v):
            value = None if v is None else str(v)
            await create_or_update_env(k, value)
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
    auth_key: str|None = None
    submitter: None|SubmitterDTO = None
    teams: list[TeamDTO]|None = None
    messages: List[MessageInfo]|None
    version: str = env.VERSION
    whoami: str = "exploitfarm"
    
