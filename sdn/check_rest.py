#!/usr/bin/env python3
"""PASS/FAIL check of the SDN side. Run in a 2nd terminal while run_all.sh is up."""
import json
import sys
import urllib.request

BASE = 'http://127.0.0.1:8080/v1.0/'


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=3) as r:
        return json.loads(r.read().decode())


try:
    switches = get('topology/switches')
    links = get('topology/links')
    hosts = get('topology/hosts')
    paths = get('diag/paths')
except Exception as exc:
    print('FAIL cannot reach Ryu REST:', exc)
    sys.exit(1)

checks = [
    ('4 switches discovered', len(switches) == 4),
    ('8 directed links (= 4 physical links)', len(links) == 8),
    ('2 hosts discovered', len(hosts) >= 2),
    ('h1 <-> h2 path installed', len(paths) >= 2),
]
for name, ok in checks:
    print('PASS' if ok else 'FAIL', '-', name)
for p in paths:
    print('   %s -> %s via %s' % (p['src_ip'], p['dst_ip'], p['path']))
sys.exit(0 if all(ok for _, ok in checks) else 1)
