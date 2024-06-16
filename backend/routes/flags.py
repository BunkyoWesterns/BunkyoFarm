
from models.response import *
from utils import *
from models.flags import *
from models.config import *
from db import Flag, UnHashedClientID
from fastapi import APIRouter
from fastapi_pagination import Page, add_pagination, paginate
from fastapi_pagination.ext.ormar import paginate
from typing import Any, Generic
from fastapi import Query
from pydantic import BaseModel
from fastapi_pagination.bases import AbstractParams, RawParams

from math import ceil
from typing import Any, Generic, Optional, Sequence, TypeVar
from fastapi import Query
from pydantic import BaseModel
from fastapi_pagination.bases import AbstractParams, BasePage, RawParams
from fastapi_pagination.types import GreaterEqualOne, GreaterEqualZero
from fastapi_pagination.utils import create_pydantic_model
from utils import get_db_stats

T = TypeVar("T")

class CustomParams(BaseModel, AbstractParams):
    page: int = Query(1, ge=1, description="Page number")
    size: int = Query(500, ge=1, le=10000, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size if self.size is not None else None,
            offset=self.size * (self.page - 1) if self.page is not None and self.size is not None else None,
        )

class CustomPage(BasePage[T], Generic[T]):
    page: Optional[GreaterEqualOne]
    size: Optional[GreaterEqualOne]
    pages: Optional[GreaterEqualZero] = None

    __params_type__ = CustomParams

    @classmethod
    def create(
        cls,
        items: Sequence[T],
        params: AbstractParams,
        *,
        total: Optional[int] = None,
        **kwargs: Any,
    ) -> Page[T]:
        if not isinstance(params, CustomParams):
            raise TypeError("Page should be used with Params")

        size = params.size if params.size is not None else (total or None)
        page = params.page if params.page is not None else 1

        if size in {0, None}:
            pages = 0
        elif total is not None:
            pages = ceil(total / size)
        else:
            pages = None

        return create_pydantic_model(
            cls,
            total=total,
            items=items,
            page=page,
            size=size,
            pages=pages,
            **kwargs,
        )

router = APIRouter(prefix="/flags", tags=["Flags"])

@router.get("", response_model=CustomPage[FlagDTO] )
async def get_flags(
    flag_status: FlagStatus|None = Query(None, description="Flag status"),
    attack_status: AttackExecutionStatus|None = Query(None, description="Attack status"),
    target: TeamID|None = Query(None, description="Target team"),
    exploit: ExploitID|None = Query(None, description="Exploit"),
    executed_by: UnHashedClientID|ClientID|None = Query(None, description="Client"),
    reversed: bool = Query(False, description="Reverse order"),
):
    equalities = [
        [flag_status.value if flag_status is not None else None, Flag.status],
        [attack_status.value if attack_status is not None else None, Flag.attack.status],
        [target, Flag.attack.target.id],
        [exploit, Flag.attack.exploit.id],
        [executed_by, Flag.attack.executed_by.id],
    ]
    filter = None
    
    for ele in equalities:
        if ele[0] is not None:
            equality = ele[0] == ele[1]
            if filter is None: filter = equality
            else: filter = filter & equality
    query = Flag.objects
    
    if filter:
        query = query.filter(filter)
    
    query = query.select_related(Flag.attack).exclude_fields("attack__error")
    
    if reversed:
        query = query.order_by(Flag.attack.recieved_at.asc()).order_by(Flag.id.asc())
    else:
        query = query.order_by(Flag.attack.recieved_at.desc()).order_by(Flag.id.desc())
    
    return await paginate(query)

@router.get("/attacks", response_model=CustomPage[AttackExecutionDTO] )
async def get_attacks(
    status: AttackExecutionStatus|None = Query(None, description="Attack status"),
    target: TeamID|None = Query(None, description="Target team"),
    exploit: ExploitID|None = Query(None, description="Exploit"),
    executed_by: UnHashedClientID|ClientID|None = Query(None, description="Client"),
    reversed: bool = Query(False, description="Reverse order"),
):
    equalities = [
        [status.value if status is not None else None, AttackExecution.status],
        [target, AttackExecution.target.id],
        [exploit, AttackExecution.exploit.id],
        [executed_by, AttackExecution.executed_by.id],
    ]
    filter = None
    
    for ele in equalities:
        if ele[0] is not None:
            equality = ele[0] == ele[1]
            if filter is None: filter = equality
            else: filter = filter & equality
    query = AttackExecution.objects
    
    if filter:
        query = query.filter(filter)
    
    if reversed:
        query = query.order_by(AttackExecution.recieved_at.asc()).order_by(AttackExecution.id.asc())
    else:
        query = query.order_by(AttackExecution.recieved_at.desc()).order_by(AttackExecution.id.desc())
    
    return await paginate(query)


@router.get("/stats", response_model=FlagStats)
#@cache(expire=5)
async def get_flags():
    data = await get_db_stats()
    if not data:
        from stats import complete_stats
        return {"ticks":[], "globals":complete_stats()}
    return data

add_pagination(router)
