"""Poll pages.dev until the search block is live (or give up). No proxy. """
import time
import urllib.request

OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "apocalab-deploy-watch"})
    with OPENER.open(req, timeout=20) as r:
        return r.status, r.read()


for i in range(24):
    try:
        st, body = get("https://apocalab.pages.dev/")
        has = b'id="city-search"' in body
        print(f"{i:02d} {time.strftime('%H:%M:%S')} HTTP {st} bytes {len(body)} search={has}", flush=True)
        if has:
            st2, shard = get("https://apocalab.pages.dev/data/cities/l.json")
            print("shard l.json", st2, len(shard), "bytes", flush=True)
            break
    except Exception as exc:  # noqa: BLE001
        print(f"{i:02d} {time.strftime('%H:%M:%S')} {type(exc).__name__}: {exc}", flush=True)
    time.sleep(15)
