import uvicorn, random
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Tuple

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
        "flag_spammer:app",
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

import requests, secrets, uuid, time, traceback
from datetime import datetime, UTC

def main():
    status = requests.get("http://127.0.0.1:5050/api/status").json()
    if status["status"] != "setup":
        run_webserver()
        return
    submitter = requests.post("http://127.0.0.1:5050/api/submitters", json={
        "code": SUBMITTER_CODE,
        "name": "flag_spammer"
    }).json()
    if submitter["status"] != "ok":
        print("failed to create submitter")
        return
    submitter_id = submitter["response"]["id"]
    requests.post("http://127.0.0.1:5050/api/setup", json={
        "FLAG_REGEX": "[a-zA-Z0-9]{32}=",
        "TICK_DURATION": 120,
        "ATTACK_MODE": "tick-delay",
        "FLAG_TIMEOUT": 120*5,
        "SUBMITTER": submitter_id,
        "SETUP_STATUS": "running"
    }).json()
    
    client_id = str(uuid.uuid4())
    print(requests.post("http://127.0.0.1:5050/api/clients", json={
        "id": client_id,
        "name": "Spammer client"
    }).json())
    requests.post("http://127.0.0.1:5050/api/teams", json=[{"host":f"127.0.0.{ele}", "name":f"Fake team {ele}"} for ele in range(1, 101)]).json()
    requests.post("http://127.0.0.1:5050/api/services/", json={"name":"Fake service"}).json()["response"]["id"]
    run_webserver()
    
    

def setup():
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()

if __name__ == '__main__':
    setup()
