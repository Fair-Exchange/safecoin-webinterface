import configparser
from pathlib import Path
import requests
import json
import os, sys

def get_config():
    config = configparser.ConfigParser()
    config.read('config.cfg')

    try:
        safecoinPath = config.get("safecoindaemon", "datadir", fallback=str(Path.home().joinpath(".safecoin")))
        with open(os.path.join(safecoinPath, ".cookie")) as cookieFile:
            username, password = cookieFile.readline().split(":")
    except:
        username = config.get("safecoindaemon", "RPC_USER", fallback="user")
        password = config.get("safecoindaemon", "RPC_PASS", fallback="pass")

    return [
        config.get("safecoindaemon", "RPC_HOST", fallback="127.0.0.1"),
        config.getint("safecoindaemon", "RPC_PORT", fallback=8771),
        username,
        password,
    ]


def request(command, args={}):
    args.update({"method": command})

    host, port, user, passwd = get_config()

    r =  requests.post(
        f'http://{host}:{port}/',
        auth=(user, passwd), data=json.dumps(args)
    )
    return r.json()