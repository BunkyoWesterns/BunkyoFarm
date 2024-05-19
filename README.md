# Exploit Farm

## Main Points:
- keep status of exploits running!!! (running time, output, number of flags obtained, code version (hash))
- easy web config with autoconfig script upload option
- pip library exploitfarm (that is both cli (xfarm -u url ./exploit) and python library)
- one-command deploy (donwload docker-compose, and start it using curl)

## TODO:
- Develop the client side
- Develop the front-end side

Notes:
- Clients schedule their own jobs, status api gives all the information needed to update exploit status on clients
- managment of output (sending, to server, compression, send only if no flag is submitted)
- client side: exclude some teams option
- warning if time is wrong on client

## Details:
- Client are authenticated if required with a token (web request using mini web-server as webhook)

## Future works
- Upload tar of exploit to share it with other players or run it remotely
- exploit versioning

