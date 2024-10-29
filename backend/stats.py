from multiprocessing import Process
from models.all import *
import logging, uvloop, sys
from utils import Scheduler, get_stats
from datetime import timedelta
import env, traceback
import math, time
from dateutil.parser import parse as dateparse
from datetime import datetime
from db import set_stats, AttackExecution, Flag, dbtransaction, connect_db, close_db, Exploit, Team, Client
from sqlalchemy.orm import defer, selectinload

class StopLoop(Exception): pass

LIMIT_QUERY_SIZE = 3000


def flags_stats() -> dict:
    return {
        "timeout": 0,
        "wait": 0,
        "invalid": 0,
        "ok": 0,
        "tot": 0
    }

def complete_stats() -> dict:
    return {
        "flags": flags_stats(),
        "attacks": {
            "done": 0,
            "noflags": 0,
            "crashed": 0,
            "tot": 0,
        }
    }

def create_tick(tick:int, start_time:datetime, end_time:datetime) -> dict:
    return {
        "tick": tick,
        "start_time": start_time,
        "end_time": end_time,
        "globals": complete_stats(),
        "exploits": {},
        "teams": {},
        "clients": {}
    }

def reset_stats():
    print("Stats Proc: ----- RESETTING STATS -----")
    g.stats = {
        "last_flag_id": 0,
        "last_attack_id": 0,
        "start_time": g.config.start_time,
        "tick_duration": g.config.TICK_DURATION,
        "wait_flag_ids": [],
        "globals": complete_stats(),
        "ticks": []
    }
    return g.stats

def recover_stats():
    if g.stats is None:
        g.stats = get_stats()
        if not g.stats:
            return reset_stats()
        return g.stats
    return g.stats

async def update_db_structures():
    g.config = await Configuration.get_from_db()
    recover_stats()
    if g.stats["start_time"] is None:
        g.stats["start_time"] = g.config.start_time
    if g.stats["start_time"] != g.config.start_time or g.stats["tick_duration"] != g.config.TICK_DURATION:
        reset_stats()
    g.stats["start_time"] = dateparse(g.stats["start_time"]) if isinstance(g.stats["start_time"], str) else g.stats["start_time"]

def calc_tick(time:datetime):
    return math.ceil((time - g.stats["start_time"]).total_seconds() / g.stats["tick_duration"]) + 1

def calc_tick_range(tick:int):
    return (g.stats["start_time"] + timedelta(seconds=((tick-1)*g.stats["tick_duration"])), g.stats["start_time"] + timedelta(seconds=tick*g.stats["tick_duration"]))

def add_stats(attack: AttackExecution, action: callable):
    # Add stats in globals
    action(g.stats["globals"])
    
    #Adding missing ticks
    tick = calc_tick(attack.received_at)
    if tick <= 0: return #skip data before start time
    
    if tick-len(g.stats["ticks"]) > 0:
        old_tick = len(g.stats["ticks"])
        for i in range(tick-len(g.stats["ticks"])):
            new_tick = old_tick+i+1
            g.stats["ticks"].append(create_tick(new_tick,*calc_tick_range(new_tick)))
    
    # Add stats in tick
    tick_block = g.stats["ticks"][tick-1]
    action(tick_block["globals"])
    
    # Add stats in exploit
    exploit_id = str(attack.exploit_id) if attack.exploit_id else "null"
    if tick_block["exploits"].get(exploit_id) is None:
        tick_block["exploits"][exploit_id] = complete_stats()
    action(tick_block["exploits"][exploit_id])
    
    # Add stats in team
    team_id = str(attack.target_id) if attack.target_id else "null"
    if tick_block["teams"].get(team_id) is None:
        tick_block["teams"][team_id] = complete_stats()
    action(tick_block["teams"][team_id])
    
    # Add stats in client
    client_id = str(attack.executed_by_id) if attack.executed_by_id else "null"
    if tick_block["clients"].get(client_id) is None:
        tick_block["clients"][client_id] = complete_stats()
    action(tick_block["clients"][client_id])

def add_attack_stats(att: AttackExecution, value:int = 1):
    def add_single_stat(stat: dict):
        stat["attacks"]["tot"] += value
        stat["attacks"][att.status.value] += value
    return add_stats(att, add_single_stat)
    
def add_flag_stats(flg: Flag, value:int = 1):
    def add_single_stat(stat: dict):
        stat["flags"]["tot"] += value
        stat["flags"][flg.status.value] += value
    return add_stats(flg.attack, add_single_stat)

async def clear_deleted_object_stats():
    async with dbtransaction() as db:
        stmt = sqla.select(Exploit.id)
        exploits = list(map(str, (await db.scalars(stmt)).all()))
        stmt = sqla.select(Team.id)
        teams = list((await db.scalars(stmt)).all())
        stmt = sqla.select(Client.id)
        clients = list((await db.scalars(stmt)).all())
    
    for tick in g.stats["ticks"]:
        for exploit_id in list(tick["exploits"].keys()):
            if exploit_id != "null" and exploit_id not in exploits:
                del tick["exploits"][exploit_id]
        for team_id in list(tick["teams"].keys()):
            if team_id != "null" and int(team_id) not in teams:
                del tick["teams"][team_id]
        for client_id in list(tick["clients"].keys()):
            if client_id != "null" and client_id not in clients:
                del tick["clients"][client_id]

async def stats_updater_task():
    await clear_deleted_object_stats()
    if g.stats["start_time"] is None:
        return
    
    flags_query = (
        sqla.select(Flag)
            .options(
                selectinload(Flag.attack)
                .defer(AttackExecution.output)
                .selectinload(AttackExecution.exploit))
            .order_by(Flag.id.asc()).limit(LIMIT_QUERY_SIZE)
    )
    
    attacks_query = sqla.select(AttackExecution).options(defer(AttackExecution.output)).order_by(AttackExecution.id.asc()).limit(LIMIT_QUERY_SIZE)

    try:
        async with dbtransaction() as db:
            flags_before_waited = (await db.scalars(
                flags_query.where(Flag.id.in_(g.stats["wait_flag_ids"]))
            )).all()
            
            new_wait_list = []
            
            for flg in flags_before_waited:
                if flg.status == FlagStatus.wait:
                    new_wait_list.append(flg.id)
                else:
                    new_status = flg.status
                    flg.status = FlagStatus.wait
                    add_flag_stats(flg, -1)
                    flg.status = new_status
                    add_flag_stats(flg)
            
            g.stats["wait_flag_ids"] = new_wait_list
            
            flags_to_analyse = (await db.scalars(flags_query.where(Flag.id > (g.stats["last_flag_id"])))).all()
            attacks_to_analyse = (await db.scalars(attacks_query.where(AttackExecution.id > (g.stats["last_attack_id"])))).all()
            
            # Probably need to fasten the loop
            if len(flags_to_analyse) == LIMIT_QUERY_SIZE or len(attacks_to_analyse) == LIMIT_QUERY_SIZE:
                g.loop_sleep = 0.1
            
            max_id = None
            
            for flg in flags_to_analyse:
                if max_id is None or flg.id > max_id:
                    max_id = flg.id
                if flg.status == FlagStatus.wait:
                    g.stats["wait_flag_ids"].append(flg.id)
                add_flag_stats(flg)
            
            if not max_id is None:
                g.stats["last_flag_id"] = max_id
            
            max_id = None
            
            for att in attacks_to_analyse:
                if max_id is None or att.id > max_id:
                    max_id = att.id
                add_attack_stats(att)
            
            if not max_id is None:
                g.stats["last_attack_id"] = max_id
    finally:
        set_stats(g.stats)

DEFAULT_LOOP_SLEEP = 3

class g:
    stats_updater = Scheduler(stats_updater_task)
    structure_update = Scheduler(update_db_structures, env.FLAG_UPDATE_POLLING)
    config:Configuration = None
    stats: dict = None
    loop_sleep = DEFAULT_LOOP_SLEEP

async def loop():
    await g.structure_update.commit()
    if g.config.SETUP_STATUS == SetupStatus.SETUP:
        return
    await g.stats_updater.commit()

#Loop based process with a half of a second of delay
async def loop_init():
    try:
        await connect_db()
        await update_db_structures()
        logging.info("Stats loop started")
        while True:
            await loop()
            await asyncio.sleep(g.loop_sleep)
            g.loop_sleep = DEFAULT_LOOP_SLEEP #Reset sleep time (if changed)
    except KeyboardInterrupt:
        pass
    finally:
        await close_db()

def inital_setup():
    try:
        while True:
            try:
                with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
                    runner.run(loop_init())
            except Exception as e:
                traceback.print_exc()
                time.sleep(5)
                logging.exception(f"Stats loop failed: {e}, restarting loop")
    except (KeyboardInterrupt, StopLoop):
        logging.info("Stats stopped by KeyboardInterrupt")

def run_stats_daemon() -> Process:
    p = Process(target=inital_setup)
    p.start()
    return p