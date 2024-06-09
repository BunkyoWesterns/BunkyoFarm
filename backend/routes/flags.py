
from models.response import *
from utils import *
from models.flags import *
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
import asyncio

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
    executed_by: UnHashedClientID|ClientID|None = Query(None, description="Client")
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
    return await paginate(
        query.select_related(Flag.attack)
        .order_by(Flag.attack.recieved_at.desc())
        .order_by(Flag.id.desc())
    )
@router.get("/stats", response_model=FlagStats)
async def get_flags():
    results = await asyncio.gather(
        Flag.objects.filter(Flag.status == FlagStatus.timeout.value).count(),
        Flag.objects.filter(Flag.status == FlagStatus.wait.value).count(),
        Flag.objects.filter(Flag.status == FlagStatus.invalid.value).count(),
        Flag.objects.filter(Flag.status == FlagStatus.ok.value).count(),
    )
    return FlagStats(
        timeout_flags=results[0],
        wait_flags=results[1],
        invalid_flags=results[2],
        ok_flags=results[3]
    )

add_pagination(router)
