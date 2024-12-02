from pydantic import BaseModel, AwareDatetime, Field, AliasChoices
from db import AttackGroupID, UnHashedClientID, ExploitID, ExploitSourceID
from utils import json_like
from models.enums import GroupStatus
from typing import Literal
from pydantic import PositiveInt
from uuid import UUID
from pydantic import field_validator

class AddGroupForm(BaseModel):
    name: str
    exploit: str
    created_by: UnHashedClientID
    commit: ExploitSourceID|Literal["latest"] = "latest"
    def db_data(self):
        d = json_like(self, convert_keys={
            "created_by": "created_by_id",
            "exploit": "exploit_id",
            "commit": "commit_id"
        })
        if d["commit_id"] == "latest":
            d["commit_id"] = None
        return d

class EditGroupForm(BaseModel):
    name: str

class GroupDTO(BaseModel):
    id: AttackGroupID
    name: str
    exploit: ExploitID = Field(validation_alias=AliasChoices('exploit_id'))
    last_attack_at: AwareDatetime|None = None
    status: GroupStatus = GroupStatus.unactive
    members: set[str] = set()
    commit: UUID|Literal["latest"] = Field("latest", validation_alias=AliasChoices('commit_id'))
    
    class Config:
        validate_assignment = True

    @field_validator('commit', mode='before')
    def commit_none_default(cls, commit):
        return commit or 'latest'
    
class JoinRequest(BaseModel):
    client: UnHashedClientID
    group_id: AttackGroupID
    queue_size: PositiveInt

class LeaveRequest(BaseModel):
    client: UnHashedClientID
    group_id: AttackGroupID