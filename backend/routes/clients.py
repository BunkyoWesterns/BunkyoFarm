from models.client import *
from models.response import *
from db import Client, client_id_hashing, MANUAL_CLIENT_ID
from typing import List
from fastapi import APIRouter, HTTPException
from utils import *

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("", response_model=List[ClientDTO])
async def client_get():
    return await Client.objects.all()

@router.post("", response_model=MessageResponse[ClientDTO])
async def client_new_or_edit(data: ClientAddForm):
    client = await Client.objects.get_or_none(id=data.id)
    if client:
        client = await client.update(**json_like(data))
        return { "message": "Client updated successfully", "response": client }
    client = await Client(**json_like(data)).save()
    return { "message": "Client created successfully", "response": client }

@router.delete("/{client_id}", response_model=MessageResponse)
async def client_delete_hashed_or_uuid(client_id: ClientID):
    if client_id == MANUAL_CLIENT_ID:
        raise HTTPException(400, "You cannot delete the manual client")
    client = await Client.objects.get_or_none(id=client_id)
    if client:
        await client.delete()
        return { "message": "Client deleted successfully" }
    try:
        client_id = UnHashedClientID(client_id)
        client_id = client_id_hashing(client_id)
    except Exception:
        raise HTTPException(400, "Invalid hash or UUID identifier (use sha256- before the hash hex-digest, otherwise use a valid UUID)")

    client = await Client.objects.get_or_none(id=client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    await client.delete()
    return { "message": "Client deleted successfully" }

@router.put("/{client_id}", response_model=MessageResponse[ClientDTO])
async def client_edit(client_id: UnHashedClientID, data: ClientEditForm):
    client = await Client.objects.get_or_none(id=client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    await client.update(**json_like(data))
    return { "message": "Client updated successfully", "response": json_like(client) }