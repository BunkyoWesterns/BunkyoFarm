
from models.response import *
from utils import *
from models.flags import *
from models.config import *
from fastapi import APIRouter
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
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
from utils.query import get_stats
from db import UnHashedClientID, Flag, sqla, AttackExecution, DBSession
from stats import complete_stats
from sqlalchemy.orm import selectinload

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
    db: DBSession,
    id: FlagID|None = Query(None, description="Flag ID"),
    flag_status: FlagStatus|None = Query(None, description="Flag status"),
    attack_status: AttackExecutionStatus|None = Query(None, description="Attack status"),
    target: TeamID|None = Query(None, description="Target team"),
    exploit: ExploitID|None = Query(None, description="Exploit"),
    executed_by: UnHashedClientID|ClientID|None = Query(None, description="Client"),
    reversed: bool = Query(False, description="Reverse order"),
):
    filters = []
    if id is not None:
        filters.append(Flag.id == id)
    if flag_status is not None:
        filters.append(Flag.status == flag_status)
    if attack_status is not None:
        filters.append(AttackExecution.status == attack_status)
    if target is not None:
        filters.append(AttackExecution.target_id == target)
    if exploit is not None:
        filters.append(AttackExecution.exploit_id == exploit)
    if executed_by is not None:
        filters.append(AttackExecution.executed_by_id == executed_by)
            
    query = (
        sqla.select(Flag)
        .outerjoin(AttackExecution, Flag.attack_id == AttackExecution.id)
        .where(*filters)
        .options(selectinload(Flag.attack).defer(AttackExecution.output))
    )

    if reversed:
        query = query.order_by(AttackExecution.received_at.asc()).order_by(Flag.id.asc())
    else:
        query = query.order_by(AttackExecution.received_at.desc()).order_by(Flag.id.desc())
    
    return await paginate(db, query)

@router.get("/attacks", response_model=CustomPage[AttackExecutionDTO] )
async def get_attacks(
    db: DBSession,
    id: AttackExecutionID|None = Query(None, description="Attack ID"),
    status: AttackExecutionStatus|None = Query(None, description="Attack status"),
    target: TeamID|None = Query(None, description="Target team"),
    exploit: ExploitID|None = Query(None, description="Exploit"),
    executed_by: UnHashedClientID|ClientID|None = Query(None, description="Client"),
    reversed: bool = Query(False, description="Reverse order"),
):  
    filters = []
    if id is not None:
        filters.append(AttackExecution.id == id)
    if status is not None:
        filters.append(AttackExecution.status == status)
    if target is not None:
        filters.append(AttackExecution.target_id == target)
    if exploit is not None:
        filters.append(AttackExecution.exploit_id == exploit)
    if executed_by is not None:
        filters.append(AttackExecution.executed_by_id == executed_by)
    
    query = (
        sqla.select(AttackExecution)
        .options(selectinload(AttackExecution.flags))
        .where(*filters)
    )
    
    if reversed:
        query = query.order_by(AttackExecution.received_at.asc()).order_by(AttackExecution.id.asc())
    else:
        query = query.order_by(AttackExecution.received_at.desc()).order_by(AttackExecution.id.desc())
    
    return await paginate(db, query)

add_pagination(router)

@router.get("/stats", response_model=FlagStats)
async def get_flag_stats():
    stats = await get_stats()
    return stats if stats else {"ticks":[], "globals":complete_stats()}


