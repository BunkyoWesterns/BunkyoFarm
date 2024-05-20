from pydantic import BaseModel
from typing import TypeVar, Generic
from models.enums import ResponseStatus, MessageStatusLevel

ResponseType = TypeVar('ResponseType', bound="MessageResponse")

class MessageResponse(BaseModel, Generic[ResponseType]):
    status: ResponseStatus = ResponseStatus.OK
    message: str|None = None
    response: ResponseType|None = None

class MessageInfo(BaseModel):
    level: MessageStatusLevel = MessageStatusLevel.warning
    title: str
    message: str
    