from models.client import *
from models.response import *
from db import Client, transactional, find_client_by_hash, _GenericClientID
from typing import List
from fastapi import APIRouter, HTTPException
from utils import *

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", response_model=List[ClientDTO])
async def service_get():
    return await Client.objects.all()

@router.post("/", response_model=MessageResponse[ClientDTO])
@transactional
async def service_new_or_edit(data: ClientAddForm):
    client = await Client.objects.get_or_none(id=data.id)
    if client:
        client = await client.update(**json_like(data))
        return { "message": "Client updated successfully", "response": client }
    client = await Client(**json_like(data)).save()
    return { "message": "Client created successfully", "response": client }

@router.delete("/{client_id}", response_model=MessageResponse)
@transactional
async def service_delete_hashed_or_uuid(client_id: _GenericClientID):
    client = await find_client_by_hash(client_id)
    if client:
        await client.delete()
        return { "message": "Client deleted successfully" }
    # If the client is not found by hash, try to find it by UUID
    if client_id.lower().startswith("sha256-"):
        raise HTTPException(404, "Client not found")
    try:
        client_id = ClientID(client_id)
    except Exception:
        raise HTTPException(400, "Invalid hash or UUID identifier (use sha256- before the hash hex-digest, otherwise use a valid UUID)")
    client = await Client.objects.get_or_none(id=client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    await client.delete()
    return { "message": "Client deleted successfully" }

@router.put("/{client_id}", response_model=MessageResponse[ClientDTO])
@transactional
async def service_edit(client_id: ClientID, data: ClientEditForm):
    client = await Client.objects.get_or_none(id=client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    await client.update(**json_like(data))
    return { "message": "Client updated successfully", "response": json_like(client) }