# Exploit Farm

## Main Points:
- keep status of exploits running!!! (running time, output, number of flags obtained, code version (hash))
- easy web config with autoconfig script upload option
- pip library exploitfarm (that is both cli (xfarm -u url ./exploit) and python library)
- one-command deploy (donwload docker-compose, and start it using curl)

## Configs:
- FLAG_REGEX [required]

Tick config:
- START_TIME / END_TIME 
- TICK_DURATION 

- Exploit submitter upload (test with cli)

Exploit timing run:
- RUN_UNIL_NEW_TICK [bool, requires tick config]
- RUN_LOOP (could spam and be dangerous)
- RUN_WITH_TICK_TIMEOUT [requires TICK_DURATION]

- FLAG_SUBMIT_LIMIT [int, default None]
- FLAG_MAX_TIMEOUT [int, default None] //Never expire default

Submitter Timing:
- SUBMIT_TIMEOUT [int, default None] (flag ageing from recievend-at and not from clinet-generated end-time)

- AUTHENTICATION_REQUIRED [bool, default False]

## Details:
- Client are authenticated if required with a token (web request using mini web-server as webhook)
