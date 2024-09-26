from multiprocessing import Process
from db import *
from models.all import *
import logging, uvloop, sys
from utils import Scheduler
from datetime import timedelta
import env, traceback
import math
from dateutil.parser import parse as dateparse

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

async def recover_stats():
    if g.stats is None:
        g.stats = await get_db_stats()
        if not g.stats:
            return reset_stats()
        return g.stats
    return g.stats

async def update_db_structures():
    g.config = await Configuration.get_from_db()
    await recover_stats()
    if g.stats["start_time"] is None:
        g.stats["start_time"] = g.config.start_time
    if g.stats["start_time"] != g.config.start_time or g.stats["tick_duration"] != g.config.TICK_DURATION:
        reset_stats()
    g.stats["start_time"] = dateparse(g.stats["start_time"]) if isinstance(g.stats["start_time"], str) else g.stats["start_time"]

async def write_on_db():
    await set_db_stats(g.stats)

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
    exploit_id = str(attack.exploit.id) if attack.exploit else "null"
    if tick_block["exploits"].get(exploit_id) is None:
        tick_block["exploits"][exploit_id] = complete_stats()
    action(tick_block["exploits"][exploit_id])
    
    # Add stats in team
    team_id = str(attack.target.id) if attack.target else "null"
    if tick_block["teams"].get(team_id) is None:
        tick_block["teams"][team_id] = complete_stats()
    action(tick_block["teams"][team_id])
    
    # Add stats in client
    client_id = str(attack.executed_by.id) if attack.executed_by else "null"
    if tick_block["clients"].get(client_id) is None:
        tick_block["clients"][client_id] = complete_stats()
    action(tick_block["clients"][client_id])

def add_attack_stats(att: AttackExecution, value:int = 1):
    def add_single_stat(stat: dict):
        stat["attacks"]["tot"] += value
        stat["attacks"][att.status] += value
    return add_stats(att, add_single_stat)
    
def add_flag_stats(flg: Flag, value:int = 1):
    def add_single_stat(stat: dict):
        stat["flags"]["tot"] += value
        stat["flags"][flg.status] += value
    return add_stats(flg.attack, add_single_stat)

async def stats_updater_task():
    if g.stats["start_time"] is None:
        return
    
    flags_query = Flag.objects.select_related(["attack", "attack__exploit"]).exclude_fields("attack__error").order_by(Flag.id.asc()).limit(LIMIT_QUERY_SIZE)
    attacks_query = AttackExecution.objects.select_related(["target", "exploit", "executed_by"]).exclude_fields("error").order_by(AttackExecution.id.asc()).limit(LIMIT_QUERY_SIZE)

    try:
        flags_before_waited = await flags_query.filter(Flag.id << g.stats["wait_flag_ids"]).all()
        
        new_wait_list = []
        
        for flg in flags_before_waited:
            if flg.status == FlagStatus.wait.value:
                new_wait_list.append(flg.id)
            else:
                new_status = flg.status
                flg.status = FlagStatus.wait.value
                add_flag_stats(flg, -1)
                flg.status = new_status
                add_flag_stats(flg)
        
        g.stats["wait_flag_ids"] = new_wait_list
        
        flags_to_analyse = await flags_query.filter(Flag.id > g.stats["last_flag_id"]).all()
        attacks_to_analyse = await attacks_query.filter(AttackExecution.id > g.stats["last_attack_id"]).all()
        
        max_id = None
        
        for flg in flags_to_analyse:
            if max_id is None or flg.id > max_id:
                max_id = flg.id
            if flg.status == FlagStatus.wait.value:
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
        await write_on_db()

class g:
    stats_updater = Scheduler(stats_updater_task)
    structure_update = Scheduler(update_db_structures, env.FLAG_UPDATE_POLLING)
    config:Configuration = None
    stats: dict = None

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
            await asyncio.sleep(0.3)
    except KeyboardInterrupt:
        pass
    finally:
        await close_db()

def inital_setup():
    try:
        while True:
            try:
                if sys.version_info >= (3, 11):
                    with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
                        runner.run(loop_init())
                else:
                    uvloop.install()
                    asyncio.run(loop_init())
            except Exception as e:
                traceback.print_exc()
                logging.exception(f"Stats loop failed: {e}, restarting loop")
    except (KeyboardInterrupt, StopLoop):
        logging.info("Stats stopped by KeyboardInterrupt")

def run_stats_daemon() -> Process:
    p = Process(target=inital_setup)
    p.start()
    return p