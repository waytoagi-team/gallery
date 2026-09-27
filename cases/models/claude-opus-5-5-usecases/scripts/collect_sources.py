"""Fetch discovery snapshots for review; never auto-add search hits to the gallery.

Standard library only. Successful bodies and an HTTP/error manifest go into the
ignored cache. Google discovery is a separate browser step (see the update log).
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import http.cookiejar
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent


def collect(source, directory, since):
    url = source["url"]
    if "arctic-shift.photon-reddit.com/api/posts/search" in url:
        parts = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(parts.query), after=since)
        url = urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))
    entry = {"key": source["key"], "url": url,
             "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    headers = {"User-Agent": "Mozilla/5.0 (Opus55 public-source review)"}
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    try:
        if source["key"] == "bilibili":
            headers["Referer"] = "https://www.bilibili.com/"
            with opener.open(urllib.request.Request(headers["Referer"], headers=headers), timeout=25) as response:
                response.read()
        with opener.open(urllib.request.Request(url, headers=headers), timeout=30) as response:
            body = response.read()
            entry.update(status=response.status, finalUrl=response.url, bytes=len(body))
        if source["format"] == "json":
            parsed = json.loads(body)
            if source["key"] == "bilibili" and parsed.get("code") != 0:
                raise ValueError("Bilibili API returned an application error")
        elif source["format"] == "xml":
            ET.fromstring(body)
        if not body:
            raise ValueError("Empty response")
        filename = source["key"] + ".txt"
        target = directory / filename
        target.with_suffix(".tmp").write_bytes(body)
        target.with_suffix(".tmp").replace(target)
        entry.update(file=filename, sha256=hashlib.sha256(body).hexdigest(), ok=True)
    except (OSError, ValueError, ET.ParseError) as error:
        entry.update(ok=False, error=str(error))
        if isinstance(error, urllib.error.HTTPError):
            entry["status"] = error.code
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", default=(datetime.date.today() - datetime.timedelta(days=2)).isoformat())
    parser.add_argument("--only", help="Comma-separated source keys")
    parser.add_argument("--output-dir", type=pathlib.Path, default=ROOT / "data" / "_refresh" / "latest")
    args = parser.parse_args()
    datetime.date.fromisoformat(args.since)
    sources = json.loads((ROOT / "data" / "source_endpoints.json").read_text())
    if args.only:
        wanted = set(args.only.split(","))
        unknown = wanted - {s["key"] for s in sources}
        if unknown:
            parser.error("Unknown sources: " + ", ".join(sorted(unknown)))
        sources = [s for s in sources if s["key"] in wanted]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(lambda s: collect(s, args.output_dir, args.since), sources))
    (args.output_dir / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"sources": len(records), "fetched": sum(r["ok"] for r in records),
                      "failed": [r["key"] for r in records if not r["ok"]],
                      "manifest": str(args.output_dir / "manifest.json")}, ensure_ascii=False))
    # An HTTP 200 proves retrieval, not model attribution or a successful demo.
    return 1 if any(not r["ok"] for r in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
