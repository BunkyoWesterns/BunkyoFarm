from pydantic import BaseModel
from db import ServiceID

###-- Services Models --###

class ServiceDTO(BaseModel):
    id: ServiceID
    name: str

class ServiceAddForm(BaseModel):
    name: str

class ServiceEditForm(BaseModel):
    name: str|None = None