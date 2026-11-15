# -*- coding: utf-8 -*-
"""Gate for plan 3.7 step 4b: www must 301 to the apex on both 443 and 80.

Six cases (three paths x two ports) plus a loop check and an apex control.
Redirects are never followed, so the raw status and Location are asserted.
Writes www-gate.json next to the repo. Exits 1 on any failure.

    python scripts/check_www.py
"""

import http.client
import json
import socket
import ssl
import sys
import time
import urllib.request

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))
DOH = "https://dns.alidns.com/resolve?name={}&type={}"
_orig_gai = socket.getaddrinfo
_IPS = {}

# The resolver on this machine answers nothing for the zone (a proxy TAP eats
# :53), so fall through to DoH. The requests below are still ordinary TLS
# requests with the real SNI and Host.
def _ips(host):
    if host not in _IPS:
        try:
            with OPENER.open(
                urllib.request.Request(DOH.format(host, "A"), headers={"User-Agent": "apoca-gate/1.0"}),
                timeout=15,
            ) as r:
                _IPS[host] = [a["data"] for a in (json.load(r).get("Answer") or []) if a.get("type") == 1]
        except Exception:
            _IPS[host] = []
    return _IPS[host]


def _getaddrinfo(host, port, *args, **kwargs):
    try:
        return _orig_gai(host, port, *args, **kwargs)
    except socket.gaierror:
        pass
    name = host.decode() if isinstance(host, bytes) else str(host)
    found = _ips(name)
    if found:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port or 0)) for ip in found]
    return _orig_gai(host, port, *args, **kwargs)


socket.getaddrinfo = _getaddrinfo

APEX = "https://apocalab.com"
CASES = [
    ("https", "/", f"{APEX}/"),
    ("https", "/nuclear-bomb-map/", f"{APEX}/nuclear-bomb-map/"),
    ("https", "/nuclear-bomb-map/?city=denver&yield=100", f"{APEX}/nuclear-bomb-map/?city=denver&yield=100"),
    ("http", "/", f"{APEX}/"),
    ("http", "/nuclear-bomb-map/", f"{APEX}/nuclear-bomb-map/"),
    ("http", "/nuclear-bomb-map/?city=denver&yield=100", f"{APEX}/nuclear-bomb-map/?city=denver&yield=100"),
]


def hit(host, path, port):
    tls = port == 443
    conn = (
        http.client.HTTPSConnection(host, port, timeout=20, context=ssl.create_default_context())
        if tls
        else http.client.HTTPConnection(host, port, timeout=20)
    )
    try:
        conn.request("GET", path, headers={"User-Agent": "apoca-gate/1.0", "Accept": "*/*"})
        r = conn.getresponse()
        return {
            "code": r.status,
            "location": r.getheader("Location"),
            "ray": r.getheader("cf-ray"),
            "bytes": len(r.read()),
            "x-robots-tag": r.getheader("X-Robots-Tag"),
        }
    except Exception as exc:  # noqa: BLE001 - a dead port is a result, not a crash
        return {"code": None, "error": f"{type(exc).__name__}: {exc}"}
    finally:
        conn.close()


def main():
    rows, fails = [], []

    for scheme, path, expect in CASES:
        port = 443 if scheme == "https" else 80
        url = f"{scheme}://www.apocalab.com{path}"
        got = hit("www.apocalab.com", path, port)
        ok = got.get("code") == 301 and got.get("location") == expect
        if not ok:
            fails.append(f"{url} -> {got.get('code')} {got.get('location')}")
        rows.append({"url": url, "code": got.get("code"), "location": got.get("location"),
                     "expected": expect, "ok": ok, "ray": got.get("ray")})
        print(f"{url:58} {str(got.get('code')):4} {got.get('location')}  {'ok' if ok else 'FAIL'}")

    print("\nloop check: https://www.apocalab.com/")
    first = hit("www.apocalab.com", "/", 443)
    hop1, final, loop_ok = first.get("location"), None, False
    print(f"  hop 1: {first.get('code')} -> {hop1}")
    if hop1:
        try:
            r = OPENER.open(urllib.request.Request(hop1, headers={"User-Agent": "apoca-gate/1.0"}), timeout=25)
            body = r.read()
            final = r.geturl()
            loop_ok = r.status == 200 and final.startswith(f"{APEX}/") and "www." not in final
            print(f"  hop 2: {r.status} final={final} bytes={len(body)}  {'ok' if loop_ok else 'FAIL'}")
        except Exception as exc:  # noqa: BLE001
            print(f"  hop 2 failed: {type(exc).__name__}: {exc}")
    if not loop_ok:
        fails.append("loop check")

    print("\ncontrol: apex over http must still be 301 -> https")
    apex = hit("apocalab.com", "/", 80)
    apex_ok = apex.get("code") == 301 and (apex.get("location") or "").startswith(APEX)
    print(f"  http://apocalab.com/  {apex.get('code')} {apex.get('location')}  {'ok' if apex_ok else 'FAIL'}")
    if not apex_ok:
        fails.append("apex :80")

    out = {
        "when": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "cases": rows,
        "loop_check": {"hop1": hop1, "final": final, "ok": loop_ok},
        "apex_http": apex,
        "fails": fails,
    }
    with open("www-gate.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)

    print(f"\nresult: {'PASS' if not fails else 'FAIL ' + str(len(fails))}")
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
