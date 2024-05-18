from multiprocessing import Process, Manager
from db import *
from models.all import *
import logging, uvloop, sys
from typing import List
from utils import Scheduler
from datetime import timedelta
from utils import datetime_now
import env, traceback

class StopLoop(Exception): pass

async def update_db_structures():
    g.config = await Configuration.get_from_db()
    g.submitters = await Submitter.objects.all()

def submit_flag(submitter:Submitter, flags: List[Flag], return_dict: dict):
    try:
        return_dict["ok"] = False
        return_dict["error"] = "Unknown error"
        glob = {}
        try:
            exec(submitter.code, glob)
        except Exception as e:
            logging.error(f"Submitter init {submitter.id} failed: {e}")
            return_dict["error"] = "Submitter setup error: " + str(e)
            return
        try:
            results = glob["submit"](flags, **{k:v["value"] for k, v in submitter.kargs.items()})
            return_dict["ok"] = True
            return_dict["results"] = results
        except Exception as e:
            traceback.print_exc()
            logging.error(f"Submitter {submitter.id} failed: {e}")
            return_dict["error"] = str(e)
    except KeyboardInterrupt:
        pass
async def execute_submitter(flags: List[Flag]):
    manager = Manager()
    
    submitter = list(filter(lambda x: x.id == g.config.SUBMITTER, g.submitters))
    if len(submitter) == 0:
        logging.error(f"Submitter {g.config.SUBMITTER} not found, unexpected behavior!")
        return
    submitter = submitter[0]
    try:
        return_dict = manager.dict()
        process = Process(target=submit_flag, args=(submitter, [flg.flag for flg in flags], return_dict))
        process.start()
        process.join(g.config.SUBMITTER_TIMEOUT)
    except Exception as e:
        logging.error(f"Submitter {submitter.id} failed: {e}")
        for f in flags:
            f.status_text = str(e)
            f.last_submission_at = datetime_now()
            f.submit_attempts += 1
        await Flag.objects.bulk_update(flags)
        return
    
    if not return_dict["ok"]:
        logging.error(f"Submitter {submitter.id} failed: {return_dict['error']}")
        for f in flags:
            f.status_text = return_dict["error"]
            f.last_submission_at = datetime_now()
            f.submit_attempts += 1
        await Flag.objects.bulk_update(flags)
        return
    
    results_dict = {ele[0]:ele[1:] for ele in return_dict["results"]}
    
    for flag in flags:
        status, status_text = results_dict.get(flag.flag, (None, None))
        if status is None or status_text is None:
            continue
        flag.submit_attempts += 1
        flag.last_submission_at = datetime_now()
        if status in [FlagStatus.ok.value, FlagStatus.invalid.value, FlagStatus.timeout.value, FlagStatus.wait.value]:
            flag.status = status
            flag.status_text = status_text
        else:
            flag.status_text = "The submitter return an invalid status! must be [(flag, status, msg), ...]"
    await Flag.objects.bulk_update(flags)


async def submit_flags():
    if g.config.FLAG_TIMEOUT:
        await Flag.objects.filter(Flag.attack.recieved_at < (datetime_now() - timedelta(seconds=g.config.FLAG_TIMEOUT))).update(status=FlagStatus.timeout.value)
    flags_to_submit = Flag.objects.filter(status=FlagStatus.wait.value).order_by(Flag.attack.recieved_at.asc())
    if g.config.FLAG_SUBMIT_LIMIT is None:
        flags_to_submit = await flags_to_submit.all()
    else:
        flags_to_submit = await flags_to_submit.limit(g.config.FLAG_SUBMIT_LIMIT).all()
    if len(flags_to_submit) == 0:
        return
    await execute_submitter(flags_to_submit)

class g:
    flag_submit = Scheduler(submit_flags)
    structure_update = Scheduler(update_db_structures, env.SUBMITTER_POLLING)
    config:Configuration = None
    submitters:List[Submitter] = None

async def loop():
    await g.structure_update.commit()
    if g.config.SETUP_STATUS == SetupStatus.SETUP:
        return
    if g.config.SUBMITTER is None:
        if len(g.submitters) == 0:
            return
        else:
            g.config.SUBMITTER = g.submitters[0].id
            await g.config.write_on_db()
            logging.warn(f"Submitter not set, using {g.config.SUBMITTER} as fallback submitter")
    g.flag_submit.interval = g.config.SUBMIT_DELAY
    await g.flag_submit.commit()

#Loop based process with a half of a second of delay
async def setup():
    try:
        await connect_db()
        await update_db_structures()
        logging.info("Submitter loop started")
        try:
            while True:
                await loop()
                await asyncio.sleep(0.5)
        except StopLoop:
            logging.info("Submitter loop stopped")
            pass
    finally:
        await close_db()

def run_submitter_proc():
    try:
        if sys.version_info >= (3, 11):
            with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
                runner.run(setup())
        else:
            uvloop.install()
            asyncio.run(setup())
    except KeyboardInterrupt:
        logging.info("Submitter loop stopped")
    except Exception as e:
        logging.exception(f"Submitter loop failed: {e}")

def run_submitter() -> Process:
    p = Process(target=run_submitter_proc)
    p.start()
    return p