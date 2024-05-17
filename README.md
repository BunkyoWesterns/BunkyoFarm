# Exploit Farm

## Main Points:
- keep status of exploits running!!! (running time, output, number of flags obtained, code version (hash))
- easy web config with autoconfig script upload option
- pip library exploitfarm (that is both cli (xfarm -u url ./exploit) and python library)
- one-command deploy (donwload docker-compose, and start it using curl)

## TODO:
- Attack execution API (+ exploit APIS)
- Hard testing on submitter process (need a fake attack flag spammer first to be able to test this)
- Flag GetFlags API / STATS
- AuthKey Gen and Revoke

Notes:
- managment of output (sending, to server, compression, send only if no flag is submitted)
- client side: exclude some teams option
- warning if time is wrong on client

## Details:
- Client are authenticated if required with a token (web request using mini web-server as webhook)

