#!/usr/bin/env python3

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