import requests

def submit(flags, url:str = "http://127.0.0.1:5050/"):
    return requests.post(url, json=flags).json()
