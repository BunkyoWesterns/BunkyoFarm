#!/usr/bin/env python3

import uvicorn, random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Tuple
from exploitfarm import get_config

app = FastAPI()

def get_random_status(flag):
    choice = random.randrange(1,50)
    if choice == 45:
        return (flag, 'invalid', "The flag is not valid")
    elif choice == 46:
        return (flag, 'timeout', "Too old")
    elif choice == 47:
        return (flag, 'invalid', "NOP flag")
    return (flag, 'ok', f'points: {random.randrange(1,10)}')

@app.post("/", response_model=List[Tuple[str, str, str]])
async def fake_submit(data: List[str]):
    return [get_random_status(ele) for ele in data]
    

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run_webserver():
    uvicorn.run(
        "test_setup:app",
        host="0.0.0.0",
        port=4455,
        reload=False,
        access_log=True,
        workers=1
    )

SUBMITTER_CODE = """
import requests

def submit(flags, url:str = "http://127.0.0.1:4455/"):
    return requests.post(url, json=flags).json()

"""

def main():
    config = get_config()
    if config.status["status"] != "setup":
        run_webserver()
        return
    submitter_id = config.reqs.new_submitter({
        "code": SUBMITTER_CODE,
        "name": "test_setup"
    })["id"]
    config.reqs.setup({
        "FLAG_REGEX": "[a-zA-Z0-9]{32}=",
        "TICK_DURATION": 120,
        "ATTACK_MODE": "tick-delay",
        "FLAG_TIMEOUT": 120*5,
        "SUBMITTER": submitter_id,
        "SETUP_STATUS": "running"
    })
    config.reqs.new_teams([{"host":f"127.0.0.{ele}", "name":f"Fake team {ele}"} for ele in range(1, 101)])
    run_webserver()

def setup():
    try:
        main()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    setup()
