from pydantic import BaseModel
from models.enums import FlagStatus, AttackExecutionStatus
from pydantic import AwareDatetime
from db import FlagID, AttackExecutionID, TeamID, ExploitID, ClientID, FkType

class AttackExecutionDTO(BaseModel):
    id: AttackExecutionID
    start_time: AwareDatetime|None = None
    end_time: AwareDatetime|None = None
    status: AttackExecutionStatus
    output: str|None
    received_at: AwareDatetime
    target: FkType[TeamID]|None = None,
    exploit: FkType[ExploitID]|None = None
    executed_by: FkType[ClientID]|None = None
    flags: list[FkType[FlagID]]

class FlagDTOAttackDetails(BaseModel):
    id: AttackExecutionID
    start_time: AwareDatetime|None = None
    end_time: AwareDatetime|None = None
    status: AttackExecutionStatus
    received_at: AwareDatetime
    target: FkType[TeamID]|None = None,
    exploit: FkType[ExploitID]|None = None
    executed_by: FkType[ClientID]|None = None

class FlagDTO(BaseModel):
    id: FlagID
    flag: str
    status: FlagStatus
    last_submission_at: AwareDatetime|None
    status_text: str|None = None
    submit_attempts: int = 0
    attack: FlagDTOAttackDetails

class TickStats(BaseModel):
    tick: int
    start_time: AwareDatetime
    end_time: AwareDatetime
    globals: dict = {}
    exploits: dict = {}
    services: dict = {}
    teams: dict = {}
    clients: dict = {}

class FlagStats(BaseModel):
    ticks: list[TickStats] = []
    globals: dict = {}
