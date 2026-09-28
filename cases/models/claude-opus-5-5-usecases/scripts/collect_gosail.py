"""Collect the complete GoSail video source and original-post evidence for review.

Read-only: this never imports candidates. Bodies are stored in the ignored cache.
Pass a Git commit to --ref to reproduce a reviewed source snapshot.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (public-source review)"})
    with urllib.request.urlopen(request, timeout=25) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="main")
    parser.add_argument("--output-dir", type=pathlib.Path, default=ROOT / "data/_refresh/gosail")
    parser.add_argument("--use-cache", action="store_true")
    args = parser.parse_args()
    url = f"https://raw.githubusercontent.com/zhuyansen/awesome-opus-5.5-video/{args.ref}/cases.json"
    source = get_json(url)
    cases = source["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Expected nonempty source with unique original-post IDs")
    directory = args.output_dir
    posts_dir = directory / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(source, ensure_ascii=False, indent=2) + "\n"
    (directory / "upstream-cases.json").write_text(serialized)
    urls = {c["original_post_url"] for c in cases}
    urls.update(c["prompt"]["source_url"] for c in cases if c.get("prompt"))
    post_urls = {}
    for link in urls:
        match = re.search(r"(?:x\.com|twitter\.com)/[^/]+/status/(\d+)", link)
        if match:
            post_urls[match[1]] = link

    def collect(item):
        post_id, link = item
        path = posts_dir / (post_id + ".json")
        record = {"id": post_id, "url": link, "checkedAt": now()}
        try:
            cached = args.use_cache and path.exists()
            data = json.loads(path.read_text()) if cached else get_json("https://api.fxtwitter.com/status/" + post_id)
            if data.get("code") != 200 or not data.get("tweet"):
                raise ValueError(f"Unreadable post: {data.get('code')}")
            if str(data["tweet"].get("id")) != post_id:
                raise ValueError("Returned post identity differs from request")
            if not cached:
                tmp = path.with_suffix(".tmp")
                tmp.write_text(json.dumps(data, ensure_ascii=False))
                tmp.replace(path)
            else:
                record["checkedAt"] = datetime.datetime.fromtimestamp(path.stat().st_mtime, datetime.timezone.utc).isoformat(timespec="seconds")
            record.update(ok=True, cached=cached, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        except (OSError, ValueError, KeyError) as error:
            record.update(ok=False, error=str(error))
        return record

    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for record in pool.map(collect, sorted(post_urls.items())):
            records.append(record)
            if len(records) % 100 == 0:
                print(f"Reviewed retrieval: {len(records)}/{len(post_urls)}", flush=True)
    manifest = {"fetchedAt": now(), "sourceUrl": url, "ref": args.ref,
                "sourceSha256": hashlib.sha256(serialized.encode()).hexdigest(),
                "sourceCount": len(cases), "promptCount": sum(bool(c.get("prompt")) for c in cases),
                "nonPostEvidenceUrls": sorted(urls - set(post_urls.values())), "posts": records}
    (directory / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"sourceCases": len(cases), "postRequests": len(records),
                      "readable": sum(r["ok"] for r in records), "failed": [r["id"] for r in records if not r["ok"]]}))
    return int(any(not r["ok"] for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
