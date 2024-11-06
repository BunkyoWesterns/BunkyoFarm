from models.client import ClientDTO, ClientAddForm, ClientEditForm
from models.response import MessageResponse
from typing import List
from fastapi import APIRouter, HTTPException
from utils import json_like
from db import Client, DBSession, sqla, MANUAL_CLIENT_ID
from db import client_id_hashing, check_client_id_hashing
from db import redis_channels, redis_conn
from db import ClientID, UnHashedClientID

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("", response_model=List[ClientDTO])
async def client_get(db: DBSession):
    return (await db.scalars(sqla.select(Client))).all()

@router.post("", response_model=MessageResponse[ClientDTO])
async def client_new_or_edit(data: ClientAddForm, db: DBSession):
    client = (await db.scalars(
        sqla.insert(Client)
            .values(json_like(data))
            .on_conflict_do_update(
                index_elements=[Client.id],
                set_=json_like(data)
            ).returning(Client)
    )).one()
    await redis_conn.publish(redis_channels.client, "update")
    return { "message": "Client created/updated successfully", "response": client }

@router.delete("/{client_id}", response_model=MessageResponse[ClientDTO])
async def client_delete_hashed_or_uuid(client_id: ClientID, db: DBSession):
    if client_id == MANUAL_CLIENT_ID:
        raise HTTPException(400, "You cannot delete the manual client")
    try:
        if not check_client_id_hashing(client_id):
            client_id = UnHashedClientID(client_id)
            client_id = client_id_hashing(client_id)
    except Exception:
        raise HTTPException(400, "Invalid hash or UUID identifier (use sha256- before the hash hex-digest, otherwise use a valid UUID)")
    
    result = (await db.scalars(
        sqla.delete(Client)
            .where(Client.id == client_id)
            .returning(Client)
    )).one_or_none()
    
    if not result:
        raise HTTPException(404, "Client not found")
    
    await redis_conn.publish(redis_channels.client, "update")
    return { "message": "Client deleted successfully", "response": json_like(result, unset=True) }

@router.put("/{client_id}", response_model=MessageResponse[ClientDTO])
async def client_edit(client_id: UnHashedClientID, data: ClientEditForm, db: DBSession):
    client = (await db.scalars(sqla.update(Client).values(json_like(data)).where(Client.id == client_id).returning(Client))).one_or_none()
    if not client:
        raise HTTPException(404, "Client not found")
    await redis_conn.publish(redis_channels.client, "update")
    return { "message": "Client updated successfully", "response": json_like(client, unset=True) }