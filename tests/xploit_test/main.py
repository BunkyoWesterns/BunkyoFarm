#!/usr/bin/env python3

import time, random
from exploitfarm import get_host, random_str

host = get_host()

print(f"Hello {host}! This text should contain a lot of flags!")

flags =[random_str(32)+"=" for _ in range(10)]

print(f"Submitted {len(flags)} flags")

fail = random.randint(1, 10) == 3
fail_time = random.randint(1, 2) == 1

if fail:
    if fail_time:
        print("Failed to submit flags, timeout")
        time.sleep(99999)
    else:
        if random.randint(1, 2) == 1:
            print("Failed to submit flags, invalid")
            exit(1)
        print("Failed to submit flags, invalid")
else:
    print(", ".join(flags))
