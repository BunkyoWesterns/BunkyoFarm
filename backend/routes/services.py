from typing import List
from fastapi import APIRouter, HTTPException
from db import Service, DBSession, sqla, redis_conn, redis_channels, ServiceID
from models.service import ServiceDTO, ServiceAddForm, ServiceEditForm
from models.response import MessageResponse
from utils import json_like

router = APIRouter(prefix="/services", tags=["Services"])

@router.get("", response_model=List[ServiceDTO])
async def service_get(db: DBSession):
    return (await db.scalars(sqla.select(Service))).all()

@router.post("", response_model=MessageResponse[ServiceDTO])
async def service_new(data: ServiceAddForm, db: DBSession):
    service = (await db.scalars(
        sqla.insert(Service)
            .values(json_like(data))
            .returning(Service)
    )).one()
    await redis_conn.publish(redis_channels.service, "update")
    return { "message": "Service created successfully", "response": service }

@router.delete("/{service_id}", response_model=MessageResponse[ServiceDTO])
async def service_delete(service_id: ServiceID, db: DBSession):
    
    service = (await db.scalars(
        sqla.delete(Service)
            .where(Service.id == service_id)
            .returning(Service)
    )).one_or_none()
    if not service:
        raise HTTPException(404, "Service not found")
    await redis_conn.publish(redis_channels.service, "update")
    return { "message": "Service deleted successfully", "response": service }

@router.put("/{service_id}", response_model=MessageResponse[ServiceDTO])
async def service_edit(service_id: ServiceID, data: ServiceEditForm, db: DBSession):
    service = (await db.scalars(
        sqla.update(Service)
            .where(Service.id == service_id)
            .values(json_like(data))
            .returning(Service)
    )).one_or_none()
    if not service:
        raise HTTPException(404, "Service not found")
    await redis_conn.publish(redis_channels.service, "update")
    return { "message": "Service updated successfully", "response": service }