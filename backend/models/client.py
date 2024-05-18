from pydantic import BaseModel
from pydantic import AwareDatetime
from pydantic import IPvAnyAddress
from db import ClientID, GenericClientID

###-- Client Models --###

class ClientDTO(BaseModel): #Client id will be hashed before returning to make it secret (it's a soft secret, not a real one)
    id: GenericClientID     #Using the hash we can only delete the client, but not edit it
    name: str|None = None
    address: IPvAnyAddress|None = None
    created_at: AwareDatetime
    
class ClientAddForm(BaseModel):
    id: ClientID
    name: str|None = None
    address: IPvAnyAddress|None = None

class ClientEditForm(BaseModel):
    name: str|None = None
    address: IPvAnyAddress|None = None