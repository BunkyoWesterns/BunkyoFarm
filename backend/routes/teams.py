from models.teams import *
from models.response import *
from models.config import *
from db import Team
from typing import List
from fastapi import APIRouter
from utils import *
import asyncio
from fastapi import HTTPException

router = APIRouter(prefix="/teams", tags=["Teams"])

@router.get("", response_model=List[TeamDTO])
async def team_get():
    return await Team.objects.all()

@router.post("", response_model=MessageResponse)
async def team_new(data: List[TeamAddForm]):
    await Team.objects.bulk_create([Team(**json_like(ele)) for ele in data])
    return { "message": "Teams created successfully" }

@router.post("/delete", response_model=MessageResponse)
async def team_delete_list(data: List[TeamID]):
    await Team.objects.filter(Team.id << data).delete()
    return { "message": "Teams deleted successfully" }

@router.delete("/{team_id}", response_model=MessageResponse)
async def team_delete(team_id: TeamID):
    await Team.objects.filter(id=team_id).delete()
    return { "message": "Team deleted successfully" }

@router.put("", response_model=MessageResponse)
async def team_edit_list(data: List[TeamEditForm]):
    async def update_action(ele):
        return await Team.objects.filter(id=ele.id).update(**json_like(ele))
    await asyncio.gather(*[update_action(ele) for ele in data])
    return { "message": "Teams updated successfully" }

