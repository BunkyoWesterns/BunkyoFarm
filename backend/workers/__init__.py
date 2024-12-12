from workers.stats import run_stats_daemon
from workers.submitter import run_submitter_daemon
from workers.skio import run_skio_daemon
from workers.group_manager import run_group_manager_daemon

global procs
procs = []

def run_workers():
    global procs
    procs = [
        run_submitter_daemon(),
        run_stats_daemon(),
        run_skio_daemon(),
        run_group_manager_daemon()
    ]
    
def terminate_workers():
    global procs
    for p in procs:
        p.terminate()
        p.join()