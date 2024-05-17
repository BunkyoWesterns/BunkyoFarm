from db import *
from models import *
from utils import *
from typing import List
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/services", tags=["Services"])

@router.get("/", response_model=List[ServiceDTO])
async def service_get():
    return await Service.objects.all()

@router.post("/", response_model=MessageResponse[ServiceDTO])
@transactional
async def service_new(data: AddService):
    service = await Service.model_validate(json_like(data)).save()
    return { "status": "ok", "message": "Service created successfully", "response": service}

@router.delete("/{service_id}", response_model=MessageResponse[ServiceDTO])
@transactional
async def service_delete(service_id: int):
    service = await Service.objects.get_or_none(id=service_id)
    if not service:
        raise HTTPException(404, "Service not found")
    await service.delete()
    return { "status": "ok", "message": "Service deleted successfully", "response": service}

@router.put("/{service_id}", response_model=MessageResponse[ServiceDTO])
@transactional
async def service_edit(service_id: int, data: EditService):
    service = await Service.objects.get_or_none(id=service_id)
    if not service:
        raise HTTPException(404, "Service not found")
    await service.update(json_like(data))
    return { "status": "ok", "message": "Service updated successfully", "response": service }