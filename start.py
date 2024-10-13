#!/usr/bin/env python3
from __future__ import annotations
import argparse, sys, os, multiprocessing, subprocess

pref = "\033["
reset = f"{pref}0m"

class g:
    keep_file = False
    composefile = "exploitfarm-compose-tmp-file.yml"
    container_name = "exploitfarm"
    compose_project_name = "exploitfarm"
    compose_volume_name = "exploitfarm_data"
    container_repo = "ghcr.io/pwnzer0tt1/exploitfarm"
    name = "ExploitFarm"
    build = False

os.chdir(os.path.dirname(os.path.realpath(__file__)))
volume_name = f"{g.container_name}_{g.compose_volume_name}"

if os.path.isfile("./Dockerfile"):
    with open("./Dockerfile", "rt") as dockerfile:
        if "c9ce2441-d842-44d7-9178-dd1617efb8f6" in dockerfile.read():
            g.build = True

#Terminal colors

class colors:
    black = "30m"
    red = "31m"
    green = "32m"
    yellow = "33m"
    blue = "34m"
    magenta = "35m"
    cyan = "36m"
    white = "37m"

def dict_to_yaml(data, indent_spaces:int=4, base_indent:int=0, additional_spaces:int=0, add_text_on_dict:str|None=None):
    yaml = ''
    spaces = ' '*((indent_spaces*base_indent)+additional_spaces)
    if isinstance(data, dict):
        for key, value in data.items():
            if not add_text_on_dict is None:
                spaces_len = len(spaces)-len(add_text_on_dict)
                spaces = (' '*max(spaces_len, 0))+add_text_on_dict
                add_text_on_dict = None
            if isinstance(value, dict) or isinstance(value, list):
                yaml += f"{spaces}{key}:\n"
                yaml += dict_to_yaml(value, indent_spaces=indent_spaces, base_indent=base_indent+1, additional_spaces=additional_spaces)
            else:
                yaml += f"{spaces}{key}: {value}\n"
            spaces = ' '*((indent_spaces*base_indent)+additional_spaces)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                yaml += dict_to_yaml(item, indent_spaces=indent_spaces, base_indent=base_indent, additional_spaces=additional_spaces+2, add_text_on_dict="- ")
            elif isinstance(item, list):
                yaml += dict_to_yaml(item, indent_spaces=indent_spaces, base_indent=base_indent+1, additional_spaces=additional_spaces)
            else:
                yaml += f"{spaces}- {item}\n"
    else:
        yaml += f"{data}\n"
    return yaml

def puts(text, *args, color=colors.white, is_bold=False, **kwargs):
    print(f'{pref}{1 if is_bold else 0};{color}' + text + reset, *args, **kwargs)

def sep(): puts("-----------------------------------", is_bold=True)

def cmd_check(program, get_output=False):
    if get_output:
        return subprocess.getoutput(program)
    return subprocess.call(program, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT, shell=True) == 0

def composecmd(cmd, composefile=None):
    if composefile:
        cmd = f"-f {composefile} {cmd}"
    if cmd_check("docker compose --version"):
        return os.system(f"docker compose -p {g.compose_project_name} {cmd}")
    elif cmd_check("docker-compose --version"):
        return os.system(f"docker-compose -p {g.compose_project_name} {cmd}")
    else:
        puts("Docker compose not found! please install docker compose!", color=colors.red)

def check_already_running():
    return g.container_name in cmd_check(f'docker ps --filter "name=^{g.container_name}$"', get_output=True)

def gen_args(args_to_parse: list[str]|None = None):                     
    
    #Main parser
    parser = argparse.ArgumentParser(description=f"{g.name} Manager")
    parser.add_argument('--clear', dest="bef_clear", required=False, action="store_true", help=f'Delete docker volume associated to {g.name} resetting all the settings', default=False)

    subcommands = parser.add_subparsers(dest="command", help="Command to execute [Default start if not running]")
    
    #Compose Command
    parser_compose = subcommands.add_parser('compose', help='Run docker compose command')
    parser_compose.add_argument('compose_args', nargs=argparse.REMAINDER, help='Arguments to pass to docker compose', default=[])
    
    #Start Command
    parser_start = subcommands.add_parser('start', help=f'Start {g.name}')
    parser_start.add_argument('--threads', "-t", type=int, required=False, help='Number of threads started for each service/utility', default=-1)
    parser_start.add_argument('--port', "-p", type=int, required=False, help='Port where open the web service', default=5050)
    parser_start.add_argument('--logs', required=False, action="store_true", help=f'Show {g.name} logs', default=False)

    #Stop Command
    parser_stop = subcommands.add_parser('stop', help=f'Stop {g.name}')
    parser_stop.add_argument('--clear', required=False, action="store_true", help=f'Delete docker volume associated to {g.name} resetting all the settings', default=False)
    
    parser_restart = subcommands.add_parser('restart', help=f'Restart {g.name}')
    parser_restart.add_argument('--logs', required=False, action="store_true", help=f'Show {g.name} logs', default=False)
    args = parser.parse_args(args=args_to_parse)
    
    if not "clear" in args:
        args.clear = False
    
    if not "threads" in args or args.threads < 1:
        args.threads = multiprocessing.cpu_count()
    
    if not "port" in args or args.port < 1:
        args.port = 5050
    
    if args.command is None:
        if not args.clear:
            return gen_args(["start", *sys.argv[1:]])
        
    args.clear = args.bef_clear or args.clear

    return args

args = gen_args()

def write_compose():
    with open(g.composefile,"wt") as compose:
        compose.write(dict_to_yaml({
            "services": {
                "exploitfarm": {
                    "restart": "unless-stopped",
                    "container_name": g.container_name,
                    "build" if g.build else "image": "." if g.build else g.container_repo,
                    "environment": [
                        f"NTHREADS={args.threads}",
                        f"POSTGRES_USER={g.container_name}",
                        f"POSTGRES_PASSWORD={g.container_name}",
                        f"POSTGRES_DB={g.container_name}"
                    ],
                    "extra_hosts": ["host.docker.internal:host-gateway"],
                    "ports": [f"{args.port}:5050"],
                    "volumes": [f"{g.compose_volume_name}:/execute/db-data/"],
                    "depends_on": ["database"]
                },
                "database": {
                    "image": "postgres:17",
                    "restart": "unless-stopped",
                    "container_name": f"{g.container_name}-database",
                    "command": '["postgres", "-c", "max_connections=1000"]',
                    "environment": [
                        f"POSTGRES_USER={g.container_name}",
                        f"POSTGRES_PASSWORD={g.container_name}",
                        f"POSTGRES_DB={g.container_name}"
                    ],
                    "volumes": [f"{g.compose_volume_name}:/var/lib/postgresql/data"]
                }
            },
            "volumes": {g.compose_volume_name:""}
        }))

def volume_exists():
    return volume_name in cmd_check(f'docker volume ls --filter "name=^{volume_name}$"', get_output=True)

def delete_volume():
    return cmd_check(f"docker volume rm {volume_name}")

def main():    
    if not cmd_check("docker --version"):
        puts("Docker not found! please install docker and docker compose!", color=colors.red)
        exit()
    elif not cmd_check("docker-compose --version") and not cmd_check("docker compose --version"):
        puts("Docker compose not found! please install docker compose!", color=colors.red)
        exit()
    if not cmd_check("docker ps"):
        puts("Cannot use docker, the user hasn't the permission or docker isn't running", color=colors.red)
        exit()    
    
    if args.command:
        match args.command:
            case "start":
                if check_already_running():
                    puts(f"{g.name} is already running! use --help to see options useful to manage {g.name} execution", color=colors.yellow)
                else:
                    puts(f"{g.name}", color=colors.yellow, end="")
                    puts(" will start on port ", end="")
                    puts(f"{args.port}", color=colors.cyan)
                    write_compose()
                    if not g.build:
                        puts(f"Downloading docker image from github packages 'docker pull {g.container_repo}'", color=colors.green)
                        cmd_check(f"docker pull {g.container_repo}")
                    puts("Running 'docker compose up -d --build'\n", color=colors.green)
                    composecmd("up -d --build", g.composefile)
            case "compose":
                write_compose()
                compose_cmd = " ".join(args.compose_args)
                puts(f"Running 'docker compose {compose_cmd}'\n", color=colors.green)
                composecmd(compose_cmd, g.composefile)
            case "restart":
                if check_already_running():
                    write_compose()
                    puts("Running 'docker compose restart'\n", color=colors.green)
                    composecmd("restart", g.composefile)
                else:
                    puts(f"{g.name} is not running!" , color=colors.red, is_bold=True, flush=True)
            case "stop":
                if check_already_running():
                    write_compose()
                    puts("Running 'docker compose down'\n", color=colors.green)
                    composecmd("down", g.composefile)
                else:
                    puts(f"{g.name} is not running!" , color=colors.red, is_bold=True, flush=True)
    
    write_compose()
    
    if args.clear:
        if volume_exists():
            delete_volume()
        else:
            puts(f"{g.name} volume not found!", color=colors.red)

    if "logs" in args and args.logs:
        composecmd("logs -f")


if __name__ == "__main__":
    try:
        try:
            main()
        finally:
            if os.path.isfile(g.composefile) and not g.keep_file:
                os.remove(g.composefile)
    except KeyboardInterrupt:
        print()
