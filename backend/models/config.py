
from pydantic import BaseModel, AwareDatetime
from pydantic import BaseModel, model_validator
from typing_extensions import Self
from functools import cache
from pydantic import NonNegativeInt, PositiveInt
from models.submitter import SubmitterDTO
import asyncio, re, env
from models.teams import TeamDTO
from models.service import ServiceDTO
from models.response import *
from typing import List
from models.enums import AttackMode, SetupStatus
from fasteners import InterProcessLock
from db import SubmitterID, Env, dbtransaction, create_or_update_env, sqla, AttackExecution, AttackExecutionStatus

_config_write_lock = InterProcessLock("./.xfarm_server_config_write.lock")

class Configuration(BaseModel):
    FLAG_REGEX: str = ""
    
    START_TIME: AwareDatetime|None = None
    END_TIME: AwareDatetime|None = None
    TICK_DURATION: PositiveInt = 120
    
    ATTACK_MODE: AttackMode = AttackMode.TICK_DELAY
    LOOP_ATTACK_DELAY: NonNegativeInt = 60
    ATTACK_TIME_TICK_DELAY: NonNegativeInt = 0
    
    FLAG_TIMEOUT: PositiveInt|None = None
    FLAG_SUBMIT_LIMIT: PositiveInt|None = None
    SUBMIT_DELAY: NonNegativeInt = 0
    SUBMITTER: SubmitterID|None = None
    SUBMITTER_TIMEOUT: PositiveInt|None = 30
    
    AUTHENTICATION_REQUIRED: bool = False
    PASSWORD_HASH: str|None = None
    
    SETUP_STATUS: SetupStatus = SetupStatus.SETUP    
    
    __start_time = None
    __end_time = None
    
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
            if self.TICK_DURATION is None:
                raise ValueError('tick duration must be set')
            if self.ATTACK_MODE == AttackMode.WAIT_FOR_TIME_TICK:
                if self.ATTACK_TIME_TICK_DELAY >= self.TICK_DURATION:
                    raise ValueError('attack time tick delay must be less than tick duration')
                if self.START_TIME is None or self.END_TIME is None:
                    raise ValueError('start and end time must be set')
                if self.START_TIME >= self.END_TIME:
                    raise ValueError('start time must be before end time')
                if abs((self.END_TIME - self.START_TIME).total_seconds()) <= self.TICK_DURATION:
                    raise ValueError('end time must be at least one tick duration after start time')
            if self.AUTHENTICATION_REQUIRED and self.PASSWORD_HASH is None:
                raise ValueError('password hash must be set')
        return self

    @staticmethod
    @cache
    def keys():
        return list(Configuration().model_dump().keys())

    async def write_on_db(self):
        with _config_write_lock:
            values = self.model_dump(mode="json")
            async def key_create_or_update(k, v):
                value = None if v is None else str(v)
                await create_or_update_env(k, value)
            await asyncio.gather(*[key_create_or_update(k, v) for k, v in values.items()])
    
    @classmethod
    async def get_from_db(cls) -> Self:
        keys = Configuration.keys()
        async with dbtransaction() as db:
            result = (await db.scalars(sqla.select(Env).where(Env.key.in_(keys)))).all()
        result = {ele.key:ele.value for ele in result}
        res = cls(**result)
        await res.__get_times()
        return res

    @property
    def start_time(self):
        return self.__start_time
    
    @property
    def end_time(self):
        return self.__end_time
    
    async def __get_times(self):
        from utils import datetime_now
        now = datetime_now()
        start_time = self.START_TIME
        end_time = self.END_TIME if not self.END_TIME is None and self.END_TIME > now else None
        done_query = sqla.select(AttackExecution.received_at).where(AttackExecution.status == AttackExecutionStatus.done)
        async with dbtransaction() as db:
            if not start_time:
                start_time = (await db.scalars(done_query.order_by(AttackExecution.received_at.asc()).limit(1))).one_or_none()
            if start_time and not end_time:
                end_time = (await db.scalars(done_query.order_by(AttackExecution.received_at.desc()).limit(1))).one_or_none()
        self.__start_time = start_time
        self.__end_time = end_time
        return start_time, end_time

class StatusAPI(BaseModel):
    status: SetupStatus
    loggined: bool
    config: Configuration|None = None
    server_time: AwareDatetime
    submitter: None|SubmitterDTO = None
    teams: List[TeamDTO]|None = None
    messages: List[MessageInfo]|None
    services: List[ServiceDTO]|None
    start_time: AwareDatetime|None = None
    end_time: AwareDatetime|None = None
    version: str = env.VERSION
    server_id: str = None
    whoami: str = "exploitfarm"

