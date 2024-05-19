from pydantic import BaseModel
from models.enums import FlagStatus, AttackExecutionStatus
from pydantic import AwareDatetime
from db import FlagID, AttackExecutionID, TeamID, ExploitID, ClientID, FkType

class FlagDTOAttackDetails(BaseModel):
    id: AttackExecutionID
    start_time: AwareDatetime|None = None
    end_time: AwareDatetime|None = None
    status: AttackExecutionStatus
    error: bytes|None
    recieved_at: AwareDatetime
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

