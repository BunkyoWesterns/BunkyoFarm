from models.teams import *
from models.response import *
from models.config import *
from typing import List
from fastapi import APIRouter
from utils import *
from db import Team, DBSession, sqla, TeamID

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("", response_model=List[TeamDTO])
async def team_get(db: DBSession):
    return db.scalars(sqla.select(Team)).all()

@router.post("", response_model=MessageResponse)
async def team_new(data: List[TeamAddForm], db: DBSession):
    db.add_all([Team(**json_like(ele)) for ele in data])
    return { "message": "Teams created successfully" }

@router.post("/delete", response_model=MessageResponse)
async def team_delete_list(data: List[TeamID], db: DBSession):
    await db.execute(sqla.delete(Team).where(Team.id.in_(data)))
    return { "message": "Teams deleted successfully" }

@router.delete("/{team_id}", response_model=MessageResponse)
async def team_delete(team_id: TeamID, db: DBSession):
    await db.execute(sqla.delete(Team).where(Team.id == team_id))
    return { "message": "Team deleted successfully" }

@router.put("", response_model=MessageResponse)
async def team_edit_list(data: List[TeamEditForm], db: DBSession):
    
    updates_queries = (
        sqla.update(Team) 
            .where(Team.id == sqla.bindparam("id"))
            .values(sqlparam_from_model(TeamEditForm, exclude=["id"]))
    )
    
    await db.execute(updates_queries, json_like(data))
    return { "message": "Teams updated successfully" }

