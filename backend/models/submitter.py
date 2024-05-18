from typing import Any, Dict
from pydantic import BaseModel, Field, AwareDatetime
from db import SubmitterID

###-- Submitter Models --###

class SubmitterDTO(BaseModel):
    id: SubmitterID
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