from multiprocessing import Process, Manager
from models.all import *
import logging, uvloop, asyncio
from typing import List
from types import GeneratorType
from datetime import timedelta
from utils import datetime_now
import traceback, time
from db import Submitter, Flag, connect_db, close_db, sqla, AttackExecution, redis_conn, redis_channels
from utils import pubsub_flush
from utils.query import create_or_update_env

class StopLoop(Exception): pass

class g:
    config:Configuration = None
    submitters:List[Submitter] = None
    last_submission = 0
    submitter_exec_required = False
    has_submitter_failed = False
    
    error_was_generated = False
    last_time_error_was_generated = False
    
    first_time_config_triggered = False

async def update_config():
    g.config = await Configuration.get_from_db()
    async with dbtransaction() as db:
        g.submitters = list((await db.scalars(sqla.select(Submitter))).all())

async def update_config_task():
    async with redis_conn.pubsub() as pubsub:
        await pubsub.subscribe(redis_channels.submitter)
        await pubsub.subscribe(redis_channels.config)
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout= None)
            await pubsub_flush(pubsub)
            if message is not None:
                await update_config()

async def err_warn_event_update():
    if g.error_was_generated or g.first_time_config_triggered or (not g.error_was_generated and g.last_time_error_was_generated):
        g.error_was_generated = False
        g.first_time_config_triggered = True
        await redis_conn.publish(redis_channels.config, "update")
    g.last_time_error_was_generated = g.error_was_generated

def raw_submit_task_execution(submitter:Submitter, flags: List[str], return_dict: dict):
    from io import StringIO
    import sys
    
    return_dict["ok"] = False
    return_dict["error"] = "Submitter failed (probably kille due to SUBMITTER_TIMEOUT)"
    
    string_io_buffer = StringIO()
    
    sys.stdout = string_io_buffer
    sys.stderr = string_io_buffer
    
    try:
        set_warning = False
        glob = {}
        try:
            exec(submitter.code, glob) #Probably it's not me :(, See the errors below
        except Exception as e:
            logging.error(f"Submitter [{submitter.name}<id:{submitter.id}>] failed: {e}")
            print(f"Submitter [{submitter.name}<id:{submitter.id}>] failed: {e}\n-------------------------------")
            traceback.print_exc()
            return_dict["error"] = "Submitter setup error: " + str(e)
            return
        try:
            results = glob["submit"](flags, **{k:v["value"] for k, v in submitter.kargs.items()}) #Probably it's not me :(, See the errors below
            if isinstance(results, GeneratorType): #If it's a generator, we can skip checking if it is iterable
                results = list(results) #Probably it's not me :(, See the errors below
            else:
                try:
                    results = list(results)
                except Exception:
                    raise Exception("The sumbitter didn't return a list or iterable object!")            
            filtered_results = []
            for f in list(results):
                try:
                    if not isinstance(f[0], str) or not isinstance(f[1], str) or not isinstance(f[2], str):
                        set_warning = True
                        print(f"WARNING: found an invalid response from submitter: the elements of every tuple must contain 3 strings, found: {type(f[0])}, {type(f[1])}, {type(f[2])}")
                        continue
                    try:
                        FlagStatus(f[1])
                    except Exception:
                        set_warning = True
                        print("WARNING: found an invalid response from submitter: second element must be a valid FlagStatus")
                        continue
                    filtered_results.append(f[:3])
                except Exception:
                    set_warning = True
                    print("WARNING: found an invalid response from submitter: must be [(flag, status, msg), ...]")
            del return_dict["error"]
            if set_warning:
                return_dict["warning"] = True
            return_dict["ok"] = True
            return_dict["results"] = filtered_results
        except Exception as e:
            logging.error(f"Submitter [{submitter.name}<id:{submitter.id}>] failed: {e}")
            print(f"Submitter [{submitter.name}<id:{submitter.id}>] failed: {e}\n-------------------------------")
            traceback.print_exc()
            return_dict["error"] = str(e)
    except KeyboardInterrupt:
        logging.info("Submitter loop stopped by KeyboardInterrupt")
    finally:
        return_dict["output"] = string_io_buffer.getvalue()

def submit_task_fork(submitter:Submitter, flags: List[str], submitter_timeout:int):
    return_dict = Manager().dict()
    process = Process(target=raw_submit_task_execution, args=(submitter, flags, return_dict), )
    process.start()
    process.join(submitter_timeout)
    return return_dict.copy()

async def run_submit_routine(flags: List[Flag]):   
    submitter = list(filter(lambda x: x.id == g.config.SUBMITTER, g.submitters))
    if len(submitter) == 0:
        logging.error(f"Submitter <{g.config.SUBMITTER}> not found, unexpected behavior!")
        return False
    submitter = submitter[0]
    try:
        return_dict = submit_task_fork(submitter, [flag.flag for flag in flags], g.config.SUBMITTER_TIMEOUT)
    except Exception as e:
        logging.error(f"Submitter [{submitter.name}<id:{submitter.id}>] failed: {e}")
        for f in flags:
            f.status_text = str(e)
            f.last_submission_at = datetime_now()
            f.submit_attempts += 1
        return False
    
    if not "ok" in return_dict or not return_dict["ok"]:
        g.error_was_generated = True
        if not "error" in return_dict or not "output" in return_dict:
            logging.error(f"Submitter [{submitter.name}<id:{submitter.id}>] failed: killed by SUBMITTER_TIMEOUT")
            await create_or_update_env("SUBMITTER_ERROR_OUTPUT", "killed by SUBMITTER_TIMEOUT (no data received from submit)")
            return False
        logging.error(f"Submitter [{submitter.name}<id:{submitter.id}>] failed: {return_dict['error']}")
        await create_or_update_env("SUBMITTER_ERROR_OUTPUT", return_dict["output"] if return_dict["output"] else "An error without output was generated") #Put the error in the db
        print("\n\n-------------- SUBMITTER OUTPUT --------------\n\n", return_dict["output"], "\n\n------------ SUBMITTER OUTPUT END ------------\n\n", sep="")
        for f in flags:
            f.status_text = return_dict["error"]
            f.last_submission_at = datetime_now()
            f.submit_attempts += 1
        return False
    else:
        await create_or_update_env("SUBMITTER_ERROR_OUTPUT", "") #Clear the error output
    
    if "warning" in return_dict and return_dict["warning"]:
        g.error_was_generated = True
        await create_or_update_env("SUBMITTER_WARNING_OUTPUT", return_dict["output"] if return_dict["output"] else "A warning without output was generated") #Put the output in the db
    else:
        await create_or_update_env("SUBMITTER_WARNING_OUTPUT", "")
    
    results_dict = {ele[0]:ele[1:] for ele in return_dict["results"]}
    
    if len(results_dict.keys()) != len(flags):
        g.error_was_generated = True
        await create_or_update_env("SUBMITTER_ERROR_OUTPUT", f"The submitter returned a different amount of flag status than the flags put in the submitter (given flags: {len(flags)}, returned flags: {len(results_dict.keys())}). Please check the submitter code.")
    
    for flag in flags:
        status, status_text = results_dict.get(flag.flag, (None, None))
        if status is None or status_text is None:       
            continue
        flag.submit_attempts += 1
        flag.last_submission_at = datetime_now()
        if status in [ele.value for ele in list(FlagStatus)]:
            flag.status = status
            flag.status_text = status_text
        else:
            flag.status_text = "The submitter return an invalid status! must be [(flag, status, msg), ...]"
    return True

async def submit_flags():
    g.submitter_exec_required = False
    async with dbtransaction() as db:
        if g.config.FLAG_TIMEOUT:

            stmt = sqla.update(Flag).where(
                Flag.id.in_(
                    sqla.select(Flag.id).outerjoin(AttackExecution, AttackExecution.id == Flag.attack_id).where(
                        (datetime_now() - timedelta(seconds=g.config.FLAG_TIMEOUT)) > AttackExecution.received_at, # Is expired
                        Flag.status == FlagStatus.wait, # Has not been submitted
                        Flag.submit_attempts > 0 # Has at least 1 submission attempt
                    ).subquery().select()
                )
            ).values(
                status=FlagStatus.timeout,
                status_text="⚠️ Timeouted by Exploitfarm due to FLAG_TIMEOUT"
            ).returning(Flag.id)
            
            updated = (await db.scalars(stmt)).all()
            if len(updated) > 0:
                logging.warning(f"{len(updated)} flags have been timeouted by FLAG_TIMEOUT")
                await redis_conn.publish(redis_channels.attack_execution, "update")
            
        flags_to_submit = (
            sqla.select(Flag).outerjoin(AttackExecution, AttackExecution.id == Flag.attack_id)
                .where(Flag.status == FlagStatus.wait).order_by(AttackExecution.received_at.asc())
        )
        if g.config.FLAG_SUBMIT_LIMIT is not None:
            flags_to_submit = flags_to_submit.limit(g.config.FLAG_SUBMIT_LIMIT)
        
        flags_to_submit = (await db.scalars(flags_to_submit)).all()

        if len(flags_to_submit) == 0:  
            g.submitter_exec_required = False
            return
        
        logging.info(f"Submitting {len(flags_to_submit)} flags")
        print(datetime_now(), f"Submitting {len(flags_to_submit)} flags")
        status = await run_submit_routine(flags_to_submit)
        await err_warn_event_update()
        
        g.last_submission = time.time()
        await redis_conn.publish(redis_channels.attack_execution, "update")
        
        if not status:
            g.has_submitter_failed = True
            g.submitter_exec_required = True
        elif g.config.FLAG_SUBMIT_LIMIT and len(flags_to_submit) >= g.config.FLAG_SUBMIT_LIMIT:
            g.submitter_exec_required = True

async def submit_flags_task():
    await submit_flags()
    async with redis_conn.pubsub() as pubsub:
        await pubsub.subscribe(redis_channels.attack_execution)
        while True:
            #Check if the submitter can be executed if some attacks has been submitted
            timeout_message = None
            if g.submitter_exec_required:
                timeout_message = 0.1
            if g.has_submitter_failed:
                g.has_submitter_failed = False
                await asyncio.sleep(10)
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=timeout_message)
            await pubsub_flush(pubsub)
            #If the submitter is not required, we can skip the submission
            if g.config.SETUP_STATUS == SetupStatus.SETUP:
                continue
            if g.config.SUBMITTER is None: # Strange behavior: the submitter is not set
                if len(g.submitters) == 0:
                    #If the submitter is not set and there are no submitters, we can skip the submission
                    continue
                else:
                    #If the submitter is not set, we can use the first submitter as fallback
                    g.config.SUBMITTER = g.submitters[0].id
                    await g.config.write_on_db()
                    await redis_conn.publish(redis_channels.config, "update")
                    logging.warning(f"Submitter not set, using id:{g.config.SUBMITTER} as fallback submitter")
            
            delta_from_last_submission = time.time() - g.last_submission
            #If a message is received, we can require the submitter execution
            if message is not None:
                g.submitter_exec_required = True
            #If the submitter is required and the delay has passed, we can submit the flags
            if delta_from_last_submission > g.config.SUBMIT_DELAY and g.submitter_exec_required:
                await submit_flags()

#Loop based process with a half of a second of delay
async def tasks_init():
    try:
        await connect_db()
        await update_config()
        logging.info("Submitter started")
        update_task = asyncio.create_task(update_config_task())
        flag_task = asyncio.create_task(submit_flags_task())
        await asyncio.gather(update_task, flag_task)
    except KeyboardInterrupt:
        pass
    finally:
        await close_db()

def inital_setup():
    try:
        while True:
            try:
                with asyncio.Runner(loop_factory=uvloop.new_event_loop) as runner:
                    runner.run(tasks_init())
            except Exception as e:
                traceback.print_exc()
                logging.exception(f"Submitter loop failed: {e}, restarting loop")
    except (KeyboardInterrupt, StopLoop):
        logging.info("Submitter stopped by KeyboardInterrupt")

def run_submitter_daemon() -> Process:
    p = Process(target=inital_setup)
    p.start()
    return p