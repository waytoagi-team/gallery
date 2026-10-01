"""Refresh existing X metrics and GitHub stars, retaining old values on failure.

HTTP receipts are saved in the ignored refresh cache. This does not add cases.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import re
import urllib.error
import urllib.request

from github_api import read_github, response_metadata

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def fetch(job):
    key, url = job
    receipt = {"key": key, "url": url,
               "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    try:
        if key.startswith("github:"):
            body, metadata = read_github(url)
            receipt.update(metadata)
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "Opus55-public-source-review"})
            with urllib.request.urlopen(request, timeout=25) as response:
                body = response.read()
                receipt.update(status=response.status)
        receipt["sha256"] = hashlib.sha256(body).hexdigest()
        value = json.loads(body)
        if key.startswith("x:"):
            tweet = value.get("tweet") or {}
            if str(tweet.get("id")) != key[2:]:
                raise ValueError("Missing or mismatched tweet identity")
            metrics = {field: tweet[field] for field in ("likes", "bookmarks", "views")
                       if isinstance(tweet.get(field), int) and not isinstance(tweet[field], bool) and tweet[field] >= 0}
        else:
            stars = value["stargazers_count"]
            if not isinstance(stars, int) or isinstance(stars, bool) or stars < 0:
                raise ValueError("Invalid repository star count")
            metrics = {"stars": stars}
        if not metrics:
            raise ValueError("Response contained no metrics")
        receipt.update(ok=True, metrics=metrics)
    except (OSError, ValueError, KeyError) as error:
        receipt.update(ok=False, error=str(error))
        if isinstance(error, urllib.error.HTTPError):
            receipt["status"] = error.code
            if key.startswith("github:"):
                receipt.update(response_metadata(error.code, error.headers))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DATA / "_refresh" / "latest")
    parser.add_argument("--only", choices=("github", "x"), help="Refresh only this platform")
    parser.add_argument("--workers", type=int, default=2, help="Concurrent requests (default: 2)")
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases = json.loads((DATA / "all_cases.json").read_text())["cases"]
    posts, repos = {}, set()
    for case in cases:
        url = case["sourceUrl"]
        match = re.match(r"https?://(?:www\.)?(?:x|twitter)\.com/[^/]+/status/(\d+)", url)
        if match:
            posts[match[1]] = url
        match = re.match(r"https?://github\.com/([^/]+/[^/?#]+)", url)
        if match:
            repos.add(match[1].lower().removesuffix(".git"))
    if args.only == "github":
        posts = {}
    elif args.only == "x":
        repos = set()
    jobs = [("x:" + tid, "https://api.fxtwitter.com/" +
             re.search(r"(?:x|twitter)\.com/([^/]+)/status/", url)[1] + "/status/" + tid)
            for tid, url in posts.items()]
    jobs += [("github:" + repo, "https://api.github.com/repos/" + repo) for repo in sorted(repos)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        receipts = list(pool.map(fetch, jobs))
    (args.output_dir / "metric-receipts.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=1) + "\n")
    patch_path = DATA / "metric_refreshes.json"
    prior = json.loads(patch_path.read_text()) if patch_path.exists() else {"cases": []}
    patches = {re.search(r"/status/(\d+)", row["sourceUrl"])[1]: row for row in prior["cases"]}
    stars = {}
    for receipt in receipts:
        if not receipt["ok"]:
            continue
        key = receipt["key"]
        if key.startswith("x:"):
            tid = key[2:]
            patches[tid] = {**patches.get(tid, {}), "sourceUrl": posts[tid],
                            **receipt["metrics"], "metricsCheckedAt": receipt["checkedAt"]}
        else:
            stars[key[7:]] = receipt
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    if posts:
        patch_path.write_text(json.dumps({"meta": {"source": "https://api.fxtwitter.com/", "refreshedAt": now,
            "note": "Primary X metrics only. Failed posts retain their previous values and timestamps."},
            "cases": list(patches.values())}, ensure_ascii=False, indent=1) + "\n")
    changed_repos = set()
    for path in sorted(DATA.glob("extra_*.json")):
        rows = json.loads(path.read_text())
        touched = False
        for row in rows:
            match = re.match(r"https?://github\.com/([^/]+/[^/?#]+)", row.get("sourceUrl", ""))
            repo = match[1].lower().removesuffix(".git") if match else None
            if repo not in stars:
                continue
            receipt = stars[repo]
            if row.get("stars") != receipt["metrics"]["stars"]:
                changed_repos.add(repo)
            row.update(receipt["metrics"], metricsCheckedAt=receipt["checkedAt"])
            touched = True
        if touched:
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n")
    summary = {"refreshedAt": now, "x": {"attempted": len(posts),
        "succeeded": sum(r["ok"] for r in receipts if r["key"].startswith("x:"))},
        "github": {"attempted": len(repos), "succeeded": len(stars), "changed": len(changed_repos)},
        "failed": [r for r in receipts if not r["ok"]]}
    (args.output_dir / "metric-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "failed"}))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
