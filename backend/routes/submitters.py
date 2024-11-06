from typing import List
from fastapi import APIRouter, HTTPException
import re
from db import Submitter, DBSession, redis_conn, redis_channels
from models.submitter import SubmitterDTO, SubmitterAddForm, SubmitterEditForm, SubmitterInfoForm, SubmitterKargs
from models.response import MessageResponse, MessageResponseInvalidError
from models.config import Configuration
from typing import Dict, Any
from utils import json_like, extract_submit, has_submit_signature, get_additional_args, type_check_annotation
from db import SubmitterID, sqla

router = APIRouter(prefix="/submitters", tags=["Submitters"])

@router.post("", response_model=MessageResponse[SubmitterDTO])
async def new_submitter(data: SubmitterAddForm, db: DBSession):
    """ Set the submitter code """
    submit_function, error = extract_submit(data.code)
    
    if not submit_function:
        raise HTTPException(400, error)
    
    valid_sig, msg = has_submit_signature(submit_function)
    if not valid_sig:
        raise HTTPException(400, msg)
    
    kargs = get_additional_args(submit_function)
    
    #Set custom kargs
    if data.kargs:
        for k,v in data.kargs.items():
            if k not in kargs.keys():
                raise HTTPException(400, f"Invalid key {k}")
            kargs[k]["value"] = v
            
    #Check enforced type for kwargs
    for k,v in kargs.items():
        if not type_check_annotation(v["value"], v["type"]):
            raise HTTPException(400, f"Invalid type for {k} ({v['value']} is not of type {v['type']})")
    
    submitter = (await db.scalars(
        sqla.insert(Submitter)
        .values(name=data.name, code=data.code, kargs=kargs)
        .returning(Submitter)
    )).one()
    submitter.model_validate(submitter)
    await db.commit()
    await redis_conn.publish(redis_channels.submitter, "update")
    return { "message": "The submitter has been created", "response": json_like(submitter, unset=True)}

@router.post("/check", response_model=MessageResponse[SubmitterKargs])
async def info_submitter(data: SubmitterInfoForm):
    """ Get information about the submitter code """
    submit_function, error = extract_submit(data.code)
    
    if not submit_function:
        raise MessageResponseInvalidError(error)
    
    valid_sig, msg = has_submit_signature(submit_function)
    if not valid_sig:
        raise MessageResponseInvalidError(msg)
    
    kargs = get_additional_args(submit_function)
    
    return { "message": "The submitter is valid", "response": kargs}

@router.get("", response_model=List[SubmitterDTO])
async def get_submitters(db: DBSession):
    """ Get all the submitters """
    return (await db.scalars(sqla.select(Submitter))).all()

@router.put("/{submitter_id}", response_model=MessageResponse[SubmitterDTO])
async def update_submitter(submitter_id: SubmitterID, data: SubmitterEditForm, db: DBSession):
    """ Edit a submitter """
    
    submitter = (await db.scalars(
        sqla.select(Submitter).where(Submitter.id == submitter_id)
    )).one_or_none()
    
    if not submitter:
        raise HTTPException(404, "Submitter not found")
    
    data.code = data.code if data.code else submitter.code
    submit_function, error = extract_submit(data.code)
    
    if not submit_function:
        raise HTTPException(400, error)
    
    valid_sig, msg = has_submit_signature(submit_function)
    if not valid_sig:
        raise HTTPException(400, msg)
    kargs = get_additional_args(submit_function)
    
    #Setting old values
    for k,v in kargs.items():
        if k in submitter.kargs.keys():
            kargs[k]["value"] = submitter.kargs[k]["value"]
    #Old values filtered and saved in submitter
    submitter.kargs = kargs
    
    #Apply edit on data.kargs
    if data.kargs:
        for k,v in data.kargs.items():
            if k not in submitter.kargs.keys():
                raise HTTPException(400, f"Invalid key {k}")
            data.kargs[k] = { "value":v, "type": submitter.kargs[k]["type"] }
    else:
        data.kargs = submitter.kargs

    #Check enforced type for kwargs
    for k,v in data.kargs.items():
        if not type_check_annotation(v["value"], v["type"]):
            raise HTTPException(400, f"Invalid type for {k} ({v['value']} is not of type {v['type']})")

    submitter = (await db.scalars(
        sqla.update(Submitter)
        .where(Submitter.id == submitter_id)
        .values(json_like(data))
        .returning(Submitter)
    )).one()
    await db.commit()
    await redis_conn.publish(redis_channels.submitter, "update")
    return { "message": "The submitter has been updated", "response": json_like(submitter, unset=True)}

@router.delete("/{submitter_id}", response_model=MessageResponse[SubmitterDTO])
async def delete_submitter(submitter_id: SubmitterID, db: DBSession):
    """ Delete a submitter """
    config = await Configuration.get_from_db()
    
    if config.SUBMITTER == submitter_id:
        raise HTTPException(400, "Cannot delete the currently selected submitter (change it in configuration first)")
    
    submitter = (await db.scalars(
        sqla.select(Submitter).where(Submitter.id == submitter_id)
    )).one_or_none()
    
    if not submitter:
        raise HTTPException(404, "Submitter not found")
    
    await db.delete(submitter)
    await db.commit()
    await redis_conn.publish(redis_channels.submitter, "update")
    return { "message": "The submitter has been deleted", "response": json_like(submitter, unset=True)}

@router.post("/{submitter_id}/test", response_model=MessageResponse[Dict[str, Any]])
async def test_submitter(submitter_id: SubmitterID, data: List[str], db: DBSession):
    """ Test the submitter (Flags will not be stored in the database)"""
    config = await Configuration.get_from_db()
    submitter = (await db.scalars(sqla.select(Submitter).where(Submitter.id == submitter_id))).one_or_none()
    if not submitter:
        raise HTTPException(404, "Submitter not found")
    if config.FLAG_REGEX:
        data = [re.findall(config.FLAG_REGEX, ele) for ele in data]
        #Flatten the list
        data = [item for sublist in data for item in sublist]
    from submitter import submit_task_fork
    return { "message": "submitter task executed", "response": submit_task_fork(submitter, data, config.SUBMITTER_TIMEOUT) }