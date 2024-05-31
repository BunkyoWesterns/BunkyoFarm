#!/usr/bin/env python3

import requests
from exploitfarm import *
from exploitfarm.model import AttackMode
from dateutil.parser import parse as date_parser
from rich import print

CCIT_SERVER = "10.10.0.1"

try:
    general_info = requests.get(f"http://{CCIT_SERVER}/api/status", timeout=5).json()
except Exception as e:
    print(f"Could not fetch general info from {CCIT_SERVER} {e}")
    exit(1)
if len(general_info["teams"]) == 0:
    print("No teams found")
    exit(1)
config = get_config()

if config.status["status"] != "setup":
    print("Server is not in setup mode")
    exit(1)

token = input("Enter your token: ").strip()

while True:
    try:
        my_team_id = int(input("Enter your team id: ").strip())
        if my_team_id in [ele["id"] for ele in general_info["teams"]]:
            break
    except Exception:
        pass
    print("Invalid team id")

SUBMITTER = """
import requests

class FlagStatus:
    ok = 'ok'
    wait = 'wait'
    timeout = 'timeout'
    invalid = 'invalid'

RESPONSES = {
    FlagStatus.wait: ['game not started', 'try again later', 'game over', 'is not up', 'no such flag'],
    FlagStatus.timeout: ['timeout'],
    FlagStatus.ok: ['accepted', 'congrat'],
    FlagStatus.invalid: ['bad', 'wrong', 'expired', 'unknown', 'your own',
                          'too old', 'not in database', 'already', 'invalid', 'nop team'],
}


def submit(flags, token:str = None, http_timeout:int=30, url:str="http://10.10.0.1:8080/flags"):
    r = requests.put(url, headers={'X-Team-Token': token}, json=flags, timeout=http_timeout)
    if r.status_code == 429:
        for flag in flags:
            yield (flag, FlagStatus.wait, "Too many requests. Error 429")
    else:
        for i, item in enumerate(r.json()):
            if not isinstance(item, dict):       
                yield (flags[i], FlagStatus.wait, "Unexpected response. Error 429")

            response = item['msg'].strip()
            response = response.replace('[{}] '.format(item['flag']), '')

            response_lower = response.lower()
            for status, substrings in RESPONSES.items():
                if any(s in response_lower for s in substrings):
                    found_status = status
                    break
            else:
                found_status = FlagStatus.wait

            yield (item['flag'], found_status, response)
"""

submitter_id = config.reqs.new_submitter({
    "name": "CCIT submitter",
    "code": SUBMITTER,
    "kargs": { "token": token }
})["id"]

config.reqs.new_teams([
    {"name": ele["name"], "short_name": ele["shortname"], "host": f"10.60.{ele['id']}.1" }
    for ele in general_info["teams"]
    if not ele["nop"] and ele['id'] != my_team_id
])

for ele in general_info["services"]:
    config.reqs.new_service({ "name": ele["name"] })

print(
    config.reqs.configure_server(
        attack_mode=AttackMode.WAIT_FOR_TIME_TICK,
        submitter=submitter_id,
        attack_time_tick_delay=2,
        authentication_required=False,
        start_time=date_parser(general_info["start"]),
        end_time=date_parser(general_info["end"]),
        tick_duration=general_info["roundTime"],
        flag_timeout=general_info["roundTime"]*5,
        flag_regex="[A-Z0-9]{31}=",
        flag_submit_limit=500,
        submit_delay=1,
        submitter_timeout=30,
        set_running=True
    )
)
