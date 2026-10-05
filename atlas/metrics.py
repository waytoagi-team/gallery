"""Refresh X metrics and object-specific GitHub metrics, retaining valid old values on failure.

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

from .github_api import read_github, response_metadata
from .github_metrics import github_target, github_response_metrics, sanitize_github_metrics

from .config import ROOT, load_topic

# Compatibility hook for existing transport unit tests; normal calls pass a Topic.
DATA = None


def fetch(job):
    key, url = job
    receipt = {"key": key, "url": url,
               "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    try:
        if key.startswith("github:"):
            body, metadata = read_github(url)
            receipt.update(metadata)
        else:
            request = urllib.request.Request(url, headers={"User-Agent": "UseCaseAtlas-public-source-review"})
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
            metrics = github_response_metrics(value, key)
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


def main(argv=None, topic=None):
    data_dir = topic.data if topic else (DATA or load_topic().data)
    snapshot = topic.public / "data/all_cases.json" if topic else data_dir / "all_cases.json"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=pathlib.Path, required=True)
    parser.add_argument("--only", choices=("github", "x"), help="Refresh only this platform")
    parser.add_argument("--github-kind", choices=("repository", "thread"),
                        help="With --only github, restrict API requests to repositories or PRs/issues")
    parser.add_argument("--workers", type=int, default=2, help="Concurrent requests (default: 2)")
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be positive")
    if args.github_kind and args.only != "github":
        parser.error("--github-kind requires --only github")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cases = json.loads((snapshot).read_text())["cases"]
    posts, targets = {}, {}
    for case in cases:
        url = case["sourceUrl"]
        match = re.match(r"https?://(?:www\.)?(?:x|twitter)\.com/[^/]+/status/(\d+)", url)
        if match:
            posts[match[1]] = url
        target = github_target(url)
        if target and target.get("api"):
            group = "repository" if target["kind"] == "repository" else "thread"
            if not args.github_kind or group == args.github_kind:
                targets[target["key"]] = target
    if args.only == "github":
        posts = {}
    elif args.only == "x":
        targets = {}
    jobs = [("x:" + tid, "https://api.fxtwitter.com/" +
             re.search(r"(?:x|twitter)\.com/([^/]+)/status/", url)[1] + "/status/" + tid)
            for tid, url in posts.items()]
    jobs += [(key, target["api"]) for key, target in sorted(targets.items())]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        receipts = list(pool.map(fetch, jobs))
    (args.output_dir / "metric-receipts.json").write_text(json.dumps(receipts, ensure_ascii=False, indent=1) + "\n")
    patch_path = data_dir / "metric_refreshes.json"
    prior = json.loads(patch_path.read_text()) if patch_path.exists() else {"cases": []}
    patches = {re.search(r"/status/(\d+)", row["sourceUrl"])[1]: row for row in prior["cases"]}
    github = {}
    for receipt in receipts:
        if not receipt["ok"]:
            continue
        key = receipt["key"]
        if key.startswith("x:"):
            tid = key[2:]
            patches[tid] = {**patches.get(tid, {}), "sourceUrl": posts[tid],
                            **receipt["metrics"], "metricsCheckedAt": receipt["checkedAt"]}
        else:
            github[key] = receipt
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    if posts:
        patch_path.write_text(json.dumps({"meta": {"source": "https://api.fxtwitter.com/", "refreshedAt": now,
            "note": "Primary X metrics only. Failed posts retain their previous values and timestamps."},
            "cases": list(patches.values())}, ensure_ascii=False, indent=1) + "\n")
    changed_targets = set()
    paths = sorted(data_dir.glob("extra_*.json"))
    if (data_dir / "base_cases.json").exists():
        paths.append(data_dir / "base_cases.json")
    for path in paths if args.only != "x" else []:
        document = json.loads(path.read_text())
        rows = document["cases"] if isinstance(document, dict) else document
        touched = False
        for row in rows:
            before = dict(row)
            sanitize_github_metrics(row)
            target = github_target(row.get("sourceUrl", "")) or {}
            receipt = github.get(target.get("key"))
            if receipt:
                if any(row.get(k) != v for k, v in receipt["metrics"].items()):
                    changed_targets.add(receipt["key"])
                row.update(receipt["metrics"], metricsCheckedAt=receipt["checkedAt"],
                           metricsSourceUrl=receipt["url"])
            touched |= row != before
        if touched:
            path.write_text(json.dumps(document, ensure_ascii=False, indent=1) + "\n")
    summary = {"refreshedAt": now, "x": {"attempted": len(posts),
        "succeeded": sum(r["ok"] for r in receipts if r["key"].startswith("x:"))},
        "github": {"attempted": len(targets), "succeeded": len(github), "changed": len(changed_targets),
                   "byKind": {kind: {"attempted": sum(t["kind"] == kind for t in targets.values()),
                       "succeeded": sum(targets[k]["kind"] == kind for k in github)}
                       for kind in ("repository", "pull_request", "issue")}},
        "failed": [r for r in receipts if not r["ok"]]}
    (args.output_dir / "metric-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "failed"}))
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
