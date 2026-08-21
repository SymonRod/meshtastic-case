"""Minimal MCP stdio client: initialize, then run the requests given on argv."""
import json
import subprocess
import sys

CMD = ["uv", "--directory", "/home/rod/blender_mcp/mcp", "run", "blender-mcp"]

p = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)


def send(obj):
    p.stdin.write(json.dumps(obj) + "\n")
    p.stdin.flush()


def read():
    while True:
        line = p.stdout.readline()
        if not line:
            return None
        line = line.strip()
        if line.startswith("{"):
            return json.loads(line)


send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "diag", "version": "0"}}})
init = read()
print("SERVER:", init["result"]["serverInfo"])
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

for n, raw in enumerate(sys.argv[1:], start=2):
    req = json.loads(raw)
    req.update({"jsonrpc": "2.0", "id": n})
    send(req)
    print(json.dumps(read(), indent=2))

p.stdin.close()
p.terminate()
