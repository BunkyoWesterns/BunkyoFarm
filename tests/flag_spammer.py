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

import multiprocessing

def run_webserver_raw():
    uvicorn.run(
        "flag_spammer:app",
        host="0.0.0.0",
        port=4455,
        reload=False,
        access_log=True,
        workers=1
    )

def run_webserver():
    proc = multiprocessing.Process(target=run_webserver_raw)
    proc.start()
    return proc

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
        print("exploit has to be in setup status")
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
        "AUTHENTICATION_REQUIRED": True,
        "PASSWORD_HASH": "cattest",
        "SETUP_STATUS": "running"
    }).json()

    auth = requests.post("http://127.0.0.1:5050/api/login", data={"grant_type":"password", "username": "user", "password": "cattest"}).json()["access_token"]
    reqs = requests.Session()
    reqs.headers.update({"Authorization": "Bearer "+auth})
    auth_key = requests.get("http://127.0.0.1:5050/api/status").json()["auth_key"]
    print("Auth key:", auth_key)
    reqs.headers.update({"Authorization": "Bearer "+auth_key})
    
    
    client_id = str(uuid.uuid4())
    print(reqs.post("http://127.0.0.1:5050/api/clients", json={
        "id": client_id,
        "name": "Spammer client"
    }).json())
    team_id = 1
    reqs.post("http://127.0.0.1:5050/api/teams", json=[{"host":"127.0.0.1", "name":"fake team"}]).json()
    exploit_id = str(uuid.uuid4())
    service_id = reqs.post("http://127.0.0.1:5050/api/services/", json={"name":"Fake service"}).json()["response"]["id"]
    reqs.post("http://127.0.0.1:5050/api/exploits/", json={ "id": exploit_id, "name":"Spammer Exploit", "language": "python", "status":"active", "service": service_id, "created_by": client_id })
    start_time = datetime.now(UTC)
    last_flags = [secrets.token_hex(16)+"=" for _ in range(100)]
    while True:
        flags = [secrets.token_hex(16)+"=" for _ in range(100)]+last_flags[5:10]
        print(reqs.post(f"http://127.0.0.1:5050/api/exploits/{exploit_id}/submit", json={
            "start_time": start_time.isoformat(),
            "end_time": datetime.now(UTC).isoformat(),
            "status": "done",
            "error": None,
            "executed_by": client_id,
            "target": team_id,
            "flags":flags
        }).json())
        print(f"Submitted {len(flags)} flags")
        start_time = datetime.now(UTC)
        time.sleep(5)
        last_flags = flags


def setup():
    proc = run_webserver()
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        proc.terminate()



if __name__ == '__main__':
    setup()
