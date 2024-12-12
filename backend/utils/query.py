from db import Exploit, AttackExecution, redis_conn, redis_keys
from db import AttackGroup
from sqlalchemy.ext.asyncio import AsyncSession
from models.config import Configuration, SetupStatus
from sqlalchemy.orm import aliased
from utils import datetime_now
import pickle
import traceback
from exploitfarm.models.response import MessageInfo
from typing import List, Type, Tuple, Literal
from fastapi import HTTPException
from pydantic import BaseModel
from db import SUBMITTER_ERROR_OUTPUT, SUBMITTER_WARNING_OUTPUT
from db import Env, dbtransaction, sqla
from exploitfarm.models.enums import ExploitStatus, AttackMode
from exploitfarm.models.response import MessageStatusLevel

MAX_EXPLOIT_TIMEOUT_TOLLERANCE = 5

def calc_max_timeout_exploit(config: Configuration) -> int:
    max_timeout = MAX_EXPLOIT_TIMEOUT_TOLLERANCE #Base timeout
    match config.ATTACK_MODE:
        case AttackMode.WAIT_FOR_TIME_TICK:
            max_timeout += config.ATTACK_TIME_TICK_DELAY + config.TICK_DURATION
        case AttackMode.TICK_DELAY:
            max_timeout += config.TICK_DURATION
        case AttackMode.LOOP_DELAY:
            max_timeout += max(config.LOOP_ATTACK_DELAY, config.TICK_DURATION)
    return max_timeout

async def get_exploits_with_latest_attack(db: AsyncSession) -> List[sqla.Row[Tuple[Exploit, AttackExecution|None]]]:
    attack_exec, attack_exec_2 = aliased(AttackExecution), aliased(AttackExecution)
    
    stmt = (
        sqla.select(Exploit, attack_exec)
        .outerjoin(
            attack_exec,
            attack_exec.id == (
                sqla.select(attack_exec_2.id)
                    .where(attack_exec_2.exploit_id == Exploit.id)
                    .order_by(attack_exec_2.received_at.desc())
                    .limit(1)
            ).correlate(Exploit).scalar_subquery()
        )
    )
    return (await db.execute(stmt)).all()

async def get_exploit_status(config: Configuration, latest_attack: AttackExecution|None) -> bool:
    result, _ = await detailed_exploit_status(config, latest_attack)
    return result

async def detailed_exploit_status(config: Configuration, latest_attack: AttackExecution|None) -> Tuple[bool, Literal["setup", "timeout", "stopped"]|None]:
    reason = None
    
    if config.SETUP_STATUS == SetupStatus.SETUP or latest_attack is None:
        return ExploitStatus.disabled, "setup"
    
    timeouted = (datetime_now() - latest_attack.received_at).total_seconds() > calc_max_timeout_exploit(config)
    
    if timeouted:
        reason = "timeout"
        exploit_status = ExploitStatus.disabled
    else:
        exploit_status = ExploitStatus.active
    
    last_exploit_stop = await redis_conn.get(f"exploit:{latest_attack.exploit_id}:stopped")
    if last_exploit_stop:
        last_exploit_stop = pickle.loads(last_exploit_stop)
        if last_exploit_stop > latest_attack.received_at:
            reason = "stopped"
            exploit_status = ExploitStatus.disabled
    
    return exploit_status, reason

async def get_groups_with_latest_attack(db: AsyncSession) -> List[sqla.Row[Tuple[AttackGroup, AttackExecution|None]]]:
    attack_exec, attack_exec_2 = aliased(AttackExecution), aliased(AttackExecution)
    
    stmt = (
        sqla.select(AttackGroup, attack_exec)
        .outerjoin(
            attack_exec,
            attack_exec.id == (
                sqla.select(attack_exec_2.id)
                    .where(attack_exec_2.executed_by_group_id == AttackGroup.id)
                    .order_by(attack_exec_2.received_at.desc())
                    .limit(1)
            ).correlate(AttackGroup).scalar_subquery()
        )
    )
    return (await db.execute(stmt)).all()

async def _get_messages_array():
    """ This function will recognize problems, dangerous situations and errors detected by the system, and collect them in a list """
    # Submitter exceptions
    error = await SUBMITTER_ERROR_OUTPUT()
    warning = await SUBMITTER_WARNING_OUTPUT()
    if error:
        yield MessageInfo(
            level=MessageStatusLevel.error,
            title="The submitter gave an unexpected exception! That's a problem in your submitter",
            message=error
        )
    if warning:
        yield MessageInfo(
            level=MessageStatusLevel.warning,
            title="The submitter gave a warning! Check the output",
            message=warning
        )
    #yield other messages here!
    
async def get_messages_array() -> List[MessageInfo]:
    """ This function will recognize problems, dangerous situations and errors detected by the system, and collect them in a list """
    return [ele async for ele in _get_messages_array()]

async def check_only_setup():
    config = await Configuration.get_from_db()
    if config.SETUP_STATUS != SetupStatus.SETUP:
        raise HTTPException(400, "You can delete all teams only in SETUP status")
    
async def set_stats(stats:dict):
    await redis_conn.set(redis_keys.stats, pickle.dumps(stats))

async def create_or_update_env(key:str, value:str):
    async with dbtransaction() as db:
        return (await db.scalars(
            sqla.insert(Env)
            .values(key=key, value=value)
            .on_conflict_do_update(
                index_elements=[Env.key], set_=dict(value=value)
            ).returning(Env)
            
        )).one()

async def get_stats():
    try:
        data = await redis_conn.get(redis_keys.stats)
        if not data:
            return None
        return pickle.loads(data)
    except Exception:
        traceback.print_exc()
        return None

def sqlparam_from_model(Model:Type[BaseModel], exclude:list[str]|None=None, include:list[str]|None=None) -> dict:
    def filter_check(x:str):
        if exclude and x in exclude:
            return False
        if include and x not in include:
            return False
        return True
    return {k: sqla.bindparam(k) for k in list(filter(filter_check, Model.model_fields.keys()))}