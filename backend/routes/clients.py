from db import *
from models import *
from utils import *
from typing import List
from fastapi import APIRouter, HTTPException
from hashlib import sha256

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/", response_model=List[ClientDTO])
async def service_get():
    clients = [json_like(ele) for ele in (await Client.objects.all())]
    for client in clients:
        client["id"] = "SHA256-"+sha256(str(client["id"]).lower().encode()).hexdigest().lower()
    return clients

@router.post("/", response_model=MessageResponse[ClientDTO])
@transactional
async def service_new(data: ClientAddForm):
    client = await Client.objects.get_or_none(id=data.id)
    if client:
        raise HTTPException(400, "Client already exists")
    client = await Client(**json_like(data)).save()
    return { "message": "Client created successfully", "response": json_like(client) }

@router.delete("/{client_id}", response_model=MessageResponse[ClientDTO])
@transactional
async def service_delete(client_id: UUID):
    client = await Client.objects.get_or_none(id=client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    await client.delete()
    return { "message": "Client deleted successfully", "response": json_like(client) }

@router.delete("/hash/{client_id_hashed}", response_model=MessageResponse)
@transactional
async def service_delete_hashed(client_id_hashed: str):
    try:
        client_id = client_id_hashed.split("SHA256-")[1]
    except Exception:
        raise HTTPException(400, "Invalid hash, insert 'SHA256-' before the hash hex-digest")
    try:
        client = list(filter(
            lambda x: sha256(str(x.id).lower().encode()).hexdigest().lower() == client_id.lower(),
            await Client.objects.all()
        ))[0]
    except IndexError:
        raise HTTPException(400, "Client not found")
    if not client:
        raise HTTPException(400, "Client not found")
    await client.delete()
    return { "message": "Client deleted successfully" }

@router.put("/{client_id}", response_model=MessageResponse[ClientDTO])
@transactional
async def service_edit(client_id: UUID, data: ClientEditForm):
    client = await Client.objects.get_or_none(id=client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    await client.update(**json_like(data))
    return { "message": "Client updated successfully", "response": json_like(client) }