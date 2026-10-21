#!/usr/bin/env python3
"""Check exact local deployment secrets without printing their values.

Run after staging intended new files. --images also scans exported image contents
and image configuration, not running containers (which must receive env secrets).
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apitest'))
from common import environment

parser = argparse.ArgumentParser()
parser.add_argument('--images', action='store_true')
args = parser.parse_args()
env = environment()
names = ['SESSION_SECRET', 'MYSQL_PASSWORD', 'MCP_AUTH_TOKEN',
         'MCP_ENCRYPTION_KEY', 'CHAT_API_KEY', 'EMBEDDING_API_KEY']
secrets = {name: env[name].encode() for name in names if env.get(name)}
failures = []


def check(data, label):
    for name, secret in secrets.items():
        if secret in data:
            failures.append((label, name))


files = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).split(b'\0')
for raw in files:
    if not raw:
        continue
    path = ROOT / raw.decode()
    if path.is_file():
        check(path.read_bytes(), str(path.relative_to(ROOT)))
for path in (ROOT / 'frontend/dist').rglob('*'):
    if path.is_file():
        check(path.read_bytes(), str(path.relative_to(ROOT)))
check(subprocess.check_output(['git', 'log', '-p', '-5'], cwd=ROOT), 'recent commit patches')
print('Checked tracked/staged sources, frontend dist and recent commit patches')

if args.images:
    for name in ['internetdemo-api', 'internetdemo-web', 'internetdemo-mcp-demo']:
        check(subprocess.check_output(['docker', 'image', 'inspect', name]), name + ' config')
        cid = subprocess.check_output(['docker', 'create', name]).decode().strip()
        try:
            process = subprocess.Popen(['docker', 'export', cid], stdout=subprocess.PIPE)
            tail = b''
            overlap = max(map(len, secrets.values()), default=1) - 1
            while True:
                chunk = process.stdout.read(1 << 20)
                if not chunk:
                    break
                data = tail + chunk
                check(data, name + ' contents')
                tail = data[-overlap:] if overlap else b''
            if process.wait() != 0:
                raise SystemExit('Image export failed: ' + name)
        finally:
            subprocess.run(['docker', 'rm', cid], check=True, stdout=subprocess.DEVNULL)
        print('Checked image:', name)
check(subprocess.check_output(['docker', 'compose', 'logs', '--no-color', '--since', '24h', 'api', 'mcp-demo'], cwd=ROOT), 'service logs')
if failures:
    for label, name in sorted(set(failures)):
        print('FAIL:', label, 'contains deployment value for', name)
    raise SystemExit(1)
print('PASS: no exact deployment secret found in checked artifacts/logs')
