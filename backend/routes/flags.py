
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
from utils import get_stats
from db import UnHashedClientID, Flag, sqla, AttackExecution
from sqlalchemy.orm import defer, selectinload
from stats import complete_stats

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
    id: FlagID|None = Query(None, description="Flag ID"),
    flag_status: FlagStatus|None = Query(None, description="Flag status"),
    attack_status: AttackExecutionStatus|None = Query(None, description="Attack status"),
    target: TeamID|None = Query(None, description="Target team"),
    exploit: ExploitID|None = Query(None, description="Exploit"),
    executed_by: UnHashedClientID|ClientID|None = Query(None, description="Client"),
    reversed: bool = Query(False, description="Reverse order"),
):
    equalities = [
        [id, Flag.id],
        [flag_status.value if flag_status is not None else None, Flag.status],
        [attack_status.value if attack_status is not None else None, Flag.attack.status],
        [target, Flag.attack.target.id],
        [exploit, Flag.attack.exploit.id],
        [executed_by, Flag.attack.executed_by.id],
    ]
    
    filters = [ele[0] == ele[1] for ele in equalities if ele[0] is not None]
            
    query = (
        sqla.select(Flag)
        .join(Flag.attack)
        .join(AttackExecution.target)
        .join(AttackExecution.exploit)
        .join(AttackExecution.executed_by)
        .options(defer(AttackExecution.error, raiseload=True), selectinload(Flag.attack))
    )
    
    if len(filters) > 0:
        query = query.where(*filters)
    
    if reversed:
        query = query.order_by(Flag.attack.received_at.asc()).order_by(Flag.id.asc())
    else:
        query = query.order_by(Flag.attack.received_at.desc()).order_by(Flag.id.desc())
    
    return await paginate(query)

@router.get("/attacks", response_model=CustomPage[AttackExecutionDTO] )
async def get_attacks(
    id: AttackExecutionID|None = Query(None, description="Attack ID"),
    status: AttackExecutionStatus|None = Query(None, description="Attack status"),
    target: TeamID|None = Query(None, description="Target team"),
    exploit: ExploitID|None = Query(None, description="Exploit"),
    executed_by: UnHashedClientID|ClientID|None = Query(None, description="Client"),
    reversed: bool = Query(False, description="Reverse order"),
):
    equalities = [
        [id, AttackExecution.id],
        [status.value if status is not None else None, AttackExecution.status],
        [target, AttackExecution.target.id],
        [exploit, AttackExecution.exploit.id],
        [executed_by, AttackExecution.executed_by.id],
    ]
    
    filters = [ele[0] == ele[1] for ele in equalities if ele[0] is not None]
    
    query = (
        sqla.select(AttackExecution)
        .join(AttackExecution.target)
        .join(AttackExecution.exploit)
        .join(AttackExecution.executed_by)
        .options(selectinload(AttackExecution.flags))
    )
    
    if len(filters) > 0:
        query = query.where(*filters)
    
    if reversed:
        query = query.order_by(AttackExecution.received_at.asc()).order_by(AttackExecution.id.asc())
    else:
        query = query.order_by(AttackExecution.received_at.desc()).order_by(AttackExecution.id.desc())
    
    return await paginate(query)


@router.get("/stats", response_model=FlagStats)
async def get_flag_stats():
    stats = get_stats()
    return stats if stats else {"ticks":[], "globals":complete_stats()}

add_pagination(router)
