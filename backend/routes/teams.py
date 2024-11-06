from typing import List
from fastapi import APIRouter
import asyncio
from db import Team, DBSession, sqla, TeamID, redis_channels, redis_conn
from models.teams import TeamDTO, TeamAddForm, TeamEditForm
from utils import json_like
from models.response import MessageResponse

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("", response_model=List[TeamDTO])
async def team_get(db: DBSession):
    stmt = sqla.select(Team)
    return json_like((await db.scalars(stmt)).all(), unset=True)

@router.post("", response_model=MessageResponse[List[TeamEditForm]])
async def team_new(data: List[TeamAddForm], db: DBSession):
    stmt = sqla.insert(Team).values([json_like(ele) for ele in data]).returning(Team)
    teams = (await db.scalars(stmt)).all()
    await redis_conn.publish(redis_channels.submitter, "update")
    return { "message": "Teams created successfully", "response": json_like(teams, unset=True) }

@router.post("/delete", response_model=MessageResponse[List[TeamDTO]])
async def team_delete_list(data: List[TeamID], db: DBSession):
    stsm = sqla.delete(Team).where(Team.id.in_(data)).returning(Team)
    teams = (await db.scalars(stsm)).all()
    await redis_conn.publish(redis_channels.submitter, "update")
    return { "message": "Teams deleted successfully", "response": json_like(teams, unset=True) }

@router.delete("/{team_id}", response_model=MessageResponse[TeamDTO])
async def team_delete(team_id: TeamID, db: DBSession):
    stmt = sqla.delete(Team).where(Team.id == team_id).returning(Team)
    team = (await db.scalars(stmt)).one()
    await redis_conn.publish(redis_channels.submitter, "update")
    return { "message": "Team deleted successfully", "response": json_like(team, unset=True) }

@router.put("", response_model=MessageResponse[List[TeamEditForm]])
async def team_edit_list(data: List[TeamEditForm], db: DBSession):
    updates_queries = [
        sqla.update(Team)
        .where(Team.id == ele.id)
        .values(json_like(ele, exclude=["id"]))
        .returning(Team)
        for ele in data
    ]
    teams = [o.one_or_none() for o in await asyncio.gather(*[db.scalars(ele) for ele in updates_queries])]
    teams = [team for team in teams if team is not None]
    await redis_conn.publish(redis_channels.submitter, "update")
    return { "message": "Teams updated successfully", "response": json_like(teams, unset=True) }

