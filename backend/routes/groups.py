from models.groups import GroupDTO, AddGroupForm, EditGroupForm
from models.response import MessageResponse
from models.enums import GroupStatus
from typing import List
from fastapi import APIRouter, HTTPException
from utils import json_like
from db import DBSession, sqla
from db import redis_channels, redis_conn, AttackGroupID
from db import AttackGroup
from typing import Tuple
from utils.query import get_groups_with_latest_attack
import asyncio
from db import AttackExecution

router = APIRouter(prefix="/groups", tags=["Attack Groups"])

@router.get("", response_model=List[GroupDTO])
async def group_get(db: DBSession):
    groups = await get_groups_with_latest_attack(db)
    async def result(result: sqla.Row[Tuple[AttackGroup, AttackExecution]]):
        group, latest_attack = result.tuple()
        memebers = await redis_conn.smembers(f"group:{group.id}:members")
        status = GroupStatus.active
        if memebers is None or len(memebers) == 0:
            status = GroupStatus.unactive
            memebers = set()
        return GroupDTO(
            **json_like(group, mode="python", unset=True),
            last_attack_at=latest_attack.received_at if latest_attack else None,
            memebers=memebers,
            status=status
        )
    return await asyncio.gather(*[result(ele) for ele in groups])

@router.post("", response_model=MessageResponse[GroupDTO])
async def new_group(data: AddGroupForm, db: DBSession):
    group = (await db.scalars(
        sqla.insert(AttackGroup)
            .values(data.db_data())
            .returning(AttackGroup)
    )).one()
    await redis_conn.set(f"group:{group.id}", 1)
    await db.commit()
    await redis_conn.publish(redis_channels.attack_group, f"add:{group.id}")
    return { "message": "Group created successfully", "response": json_like(group, unset=True) }

@router.delete("/{group_id}", response_model=MessageResponse[GroupDTO])
async def delete_group(group_id: AttackGroupID, db: DBSession):
    result = (await db.scalars(
        sqla.delete(AttackGroup)
            .where(AttackGroup.id == group_id)
            .returning(AttackGroup)
    )).one_or_none()
    if not result:
        raise HTTPException(404, "Group not found")
    to_delete = await redis_conn.keys(f"group:{result.id}:*")
    if len(to_delete) > 0:
        await redis_conn.delete(*to_delete)
    await db.commit()
    await redis_conn.publish(redis_channels.attack_group, f"delete:{result.id}")
    return { "message": "Client deleted successfully", "response": json_like(result, unset=True) }

@router.put("/{group_id}", response_model=MessageResponse[GroupDTO])
async def client_edit(group_id: AttackGroupID, data: EditGroupForm, db: DBSession):
    group = (await db.scalars(
        sqla.update(AttackGroup)
        .values(json_like(data))
        .where(AttackGroup.id == group_id)
        .returning(AttackGroup)
    )).one_or_none()
    if not group:
        raise HTTPException(404, "Group not found")
    await db.commit()
    await redis_conn.publish(redis_channels.attack_group, f"update:{group.id}")
    return { "message": "Group updated successfully", "response": json_like(group, unset=True) }