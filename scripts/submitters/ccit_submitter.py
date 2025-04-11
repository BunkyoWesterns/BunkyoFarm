#!/usr/bin/env python3

import requests
from exploitfarm.models.enums import FlagStatus

RESPONSES = {
    FlagStatus.timeout: ['timeout', 'too old', 'expired'],
    FlagStatus.ok: ['accepted', 'congrat', 'claimed'],
    FlagStatus.invalid: ['too old', 'unknown', 'your own', 'already claimed', 'invalid', 'nop team', 'game over', 'no such flag'],
    FlagStatus.wait: ['try again later', 'is not up', 'game not started', 'didn\'t terminate successfully', 'RESUBMIT', 'ERROR']
}

def submit(flags, token:str = None, http_timeout:int=30, url:str="http://10.10.0.1:8080/flags"):
    r = requests.put(url, headers={'X-Team-Token': token}, json=flags, timeout=http_timeout)
    if r.status_code == 429:
        for flag in flags:
            yield (flag, FlagStatus.wait, "Too many requests. Error 429")
    else:
        req_response = r.json()
        if not isinstance(req_response, list):
            raise ValueError(f"Unexpected response. {req_response}")
        for i, item in enumerate(req_response):
            
            if not isinstance(item, dict):       
                yield (flags[i], FlagStatus.wait, "Unexpected response. Error 429")
            
            response = item['msg']
            response = response.split("]")
            if len(response) > 1:
                response = response[1]
            else:
                response = response[0]
            
            response_lower = response.strip().lower()
            for status, substrings in RESPONSES.items():
                if any(s in response_lower for s in substrings):
                    found_status = status
                    break
            else:
                found_status = FlagStatus.wait

            yield (item['flag'], found_status, response)
