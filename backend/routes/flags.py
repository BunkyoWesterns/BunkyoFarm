
from models.response import *
from utils import *
from models.flags import *
from db import Flag, transactional
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

@router.get("/", response_model=CustomPage[FlagDTO] )
@transactional
async def get_flags() -> Any:
    return await paginate(
        Flag.objects
        .select_related(Flag.attack)
        .order_by(Flag.attack.recieved_at.desc())
        .order_by(Flag.id.desc())
    )

add_pagination(router)
