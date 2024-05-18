from pydantic import BaseModel
from pydantic import IPvAnyAddress
from pydantic import AwareDatetime
from db import TeamID

###-- Teams Models --###

class TeamDTO(BaseModel):
    id: TeamID
    name: str|None
    short_name: str|None
    host: IPvAnyAddress
    created_at: AwareDatetime

class TeamAddForm(BaseModel):
    name: str|None = None
    short_name: str|None = None
    host: IPvAnyAddress

class TeamEditForm(BaseModel):
    id: TeamID
    name: str|None = None
    short_name: str|None = None
    host: IPvAnyAddress|None = None