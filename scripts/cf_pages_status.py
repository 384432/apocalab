"""Poll the Pages project: latest deployments and their stages.

Usage: CF_ACCOUNT_ID=... python scripts/cf_pages_status.py [rounds]
"""
import json
import os
import pathlib
import sys
import time
import tomllib
import urllib.error
import urllib.request

ACCOUNT = os.environ.get("CF_ACCOUNT_ID", "")  # from `wrangler whoami`; not committed
PROJECT = "apocalab"


def token():
    p = pathlib.Path(os.path.expanduser("~/.wrangler/config/default.toml"))
    return tomllib.loads(p.read_text(encoding="utf-8"))["oauth_token"]


def get(path):
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4{path}",
        headers={"Authorization": f"Bearer {token()}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


if not ACCOUNT:
    sys.exit("set CF_ACCOUNT_ID (see `npx wrangler whoami`)")

rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 1
for i in range(rounds):
    d = get(f"/accounts/{ACCOUNT}/pages/projects/{PROJECT}/deployments?per_page=5")
    res = d.get("result") or []
    if not res:
        print("no deployments yet")
    for dep in res[:3]:
        st = dep.get("latest_stage") or {}
        print(
            dep.get("short_id"),
            dep.get("environment"),
            dep.get("deployment_trigger", {}).get("type"),
            "|", st.get("name"), st.get("status"),
            "|", (dep.get("url") or "")[:70],
        )
        for s in dep.get("stages", []):
            if s.get("status") not in ("success", "idle"):
                print("    stage", s.get("name"), s.get("status"))
    if i + 1 < rounds:
        time.sleep(20)
