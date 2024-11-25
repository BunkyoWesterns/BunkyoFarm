from pydantic import BaseModel, AwareDatetime, Field, AliasChoices
from db import AttackGroupID, UnHashedClientID, ExploitID
from utils import json_like
from models.enums import GroupStatus
from typing import Literal
from pydantic import PositiveInt

class AddGroupForm(BaseModel):
    name: str
    exploit: str
    created_by: UnHashedClientID
    def db_data(self):
        return json_like(self, convert_keys={
            "created_by": "created_by_id",
            "exploit": "exploit_id"
        })

class EditGroupForm(BaseModel):
    name: str

class GroupDTO(BaseModel):
    id: AttackGroupID
    name: str
    exploit: ExploitID = Field(validation_alias=AliasChoices('exploit_id'))
    last_attack_at: AwareDatetime|None = None
    status: GroupStatus = GroupStatus.unactive
    members: set[str] = set()
    commit: str|Literal["latest"]|None = None

class JoinRequest(BaseModel):
    client: UnHashedClientID
    group_id: AttackGroupID
    queue_size: PositiveInt

class LeaveRequest(BaseModel):
    client: UnHashedClientID
    group_id: AttackGroupID