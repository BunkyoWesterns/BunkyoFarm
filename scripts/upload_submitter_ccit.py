from exploitfarm import *
from os.path import join as pjoin
from os.path import dirname
from rich import print

config = get_config()

token = input("Enter your token: ").strip()

with open(pjoin(dirname(__file__), "submitters", "ccit_submitter.py")) as f:
    SUBMITTER = f.read()

submitter_id = config.reqs.new_submitter({
    "name": "CCIT submitter",
    "code": SUBMITTER,
    "kargs": { "token": token }
})["id"]

print(
    config.reqs.configure_server(submitter=submitter_id)
)
