#!/usr/bin/env python3

import requests
from exploitfarm.models.enums import AttackMode
from dateutil.parser import parse as date_parser
from rich import print
from os.path import join as pjoin
from os.path import dirname
from typer import confirm
from exploitfarm import get_config

CCIT_SERVER = "10.10.0.1"

with open(pjoin(dirname(__file__), "submitters", "ccit_submitter.py")) as f:
    SUBMITTER = f.read()

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

auth = confirm("Do you want to set authentication?", default=True)
password = None
if auth:
    while True:
        password = input("Enter the password: ").strip()
        if len(password) > 0:
            check_password = input("Re-enter the password: ").strip()
            if password == check_password:
                break
            print("Passwords do not match")
            continue
        print("Password cannot be empty")
    
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
        attack_mode=AttackMode.TICK_DELAY,
        submitter=submitter_id,
        attack_time_tick_delay=2,
        authentication_required=auth,
        password_hash=password,
        start_time=date_parser(general_info["start"]) if general_info["start"] else None,
        end_time=date_parser(general_info["end"]) if general_info["end"] else None,
        tick_duration=general_info["roundTime"],
        flag_regex="[A-Z0-9]{31}=",
        flag_submit_limit=2500,
        submit_delay=0.1,
        submitter_timeout=30,
        set_running=True
    )
)
