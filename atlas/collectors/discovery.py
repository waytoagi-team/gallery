"""Fetch discovery snapshots for review; never auto-add search hits to the gallery.

Python standard library plus authenticated gh for GitHub API requests. Successful
bodies and an HTTP/error manifest go into the ignored cache. Google discovery is
a separate browser step (see the update log).
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

from ..github_api import read_github, response_metadata

from ..config import ROOT
from ..build import norm_url
import uuid


def discovery_url(source, since):
    parts = urllib.parse.urlsplit(source["url"])
    query = dict(urllib.parse.parse_qsl(parts.query))
    if "arctic-shift.photon-reddit.com/api/posts/search" in source["url"]:
        query["after"] = since
    elif parts.hostname == "api.github.com" and parts.path.startswith("/search/"):
        field = "pushed" if parts.path.endswith("repositories") else "updated"
        query["q"] = query.get("q", "") + f" {field}:>={since}"
    elif parts.hostname == "hn.algolia.com":
        epoch = int(datetime.datetime.fromisoformat(since).replace(tzinfo=datetime.timezone.utc).timestamp())
        query["numericFilters"] = f"created_at_i>={epoch}"
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query)))


def search_metadata(parsed):
    if isinstance(parsed, dict) and "items" in parsed:
        return {"returned": len(parsed["items"]), "totalReported": parsed.get("total_count"),
                "searchIncomplete": parsed.get("incomplete_results"), "pagination": "first-page-only"}
    if isinstance(parsed, dict) and "hits" in parsed:
        return {"returned": len(parsed["hits"]), "totalReported": parsed.get("nbHits"),
                "pagesReported": parsed.get("nbPages"), "pagination": "first-page-only"}
    return {"pagination": "not-verified"}


def collect(source, directory, since):
    url = discovery_url(source, since)
    entry = {"key": source["key"], "url": url,
             "checkedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    headers = {"User-Agent": "Mozilla/5.0 (UseCaseAtlas public-source review)"}
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    try:
        if urllib.parse.urlsplit(url).hostname == "api.bilibili.com":
            headers["Referer"] = "https://www.bilibili.com/"
            with opener.open(urllib.request.Request(headers["Referer"], headers=headers), timeout=25) as response:
                response.read()
        if urllib.parse.urlsplit(url).netloc == "api.github.com":
            body, metadata = read_github(url)
            entry.update(metadata, finalUrl=url, bytes=len(body))
        else:
            with opener.open(urllib.request.Request(url, headers=headers), timeout=30) as response:
                body = response.read()
                entry.update(status=response.status, finalUrl=response.url, bytes=len(body))
        if source["format"] == "json":
            parsed = json.loads(body)
            if urllib.parse.urlsplit(url).hostname == "api.bilibili.com" and parsed.get("code") != 0:
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
        if source["format"] == "json":
            entry.update(search_metadata(parsed))
    except (OSError, ValueError, ET.ParseError) as error:
        entry.update(ok=False, error=str(error))
        if isinstance(error, urllib.error.HTTPError):
            entry["status"] = error.code
            if urllib.parse.urlsplit(url).netloc == "api.github.com":
                entry.update(response_metadata(error.code, error.headers))
    return entry


def candidates_from_snapshot(source, parsed):
    """Minimal discovery metadata; no copied bodies or automatic acceptance."""
    if not isinstance(parsed, dict):
        return []
    rows = []
    if "items" in parsed and urllib.parse.urlsplit(source["url"]).hostname == "api.github.com":
        for item in parsed["items"]:
            url = item.get("html_url")
            if url:
                rows.append({"sourceUrl": url, "title": item.get("full_name") or item.get("title") or url,
                             "platform": "GitHub", "date": (item.get("created_at") or "")[:10] or None})
    elif "hits" in parsed and urllib.parse.urlsplit(source["url"]).hostname == "hn.algolia.com":
        for item in parsed["hits"]:
            if item.get("objectID"):
                rows.append({"sourceUrl": "https://news.ycombinator.com/item?id=" + str(item["objectID"]),
                             "title": item.get("title") or item.get("story_title") or "HN comment " + str(item["objectID"]),
                             "platform": "Hacker News", "date": (item.get("created_at") or "")[:10] or None})
    return rows


def run_discovery(topic, since=None, only=None, output_dir=None, report_path=None, dry_run=False, workers=2):
    since = since or (datetime.date.today() - datetime.timedelta(days=topic.spec["monitor"].get("lookbackDays", 2))).isoformat()
    datetime.date.fromisoformat(since)
    if workers < 1 or workers > 8:
        raise ValueError("workers must be between 1 and 8")
    sources = topic.sources
    if only:
        wanted = set(only.split(","))
        unknown = wanted - {s["key"] for s in sources}
        if unknown:
            raise ValueError("Unknown sources: " + ", ".join(sorted(unknown)))
        sources = [s for s in sources if s["key"] in wanted]
    if dry_run:
        return {"topic": topic.id, "since": since, "dryRun": True,
                "sources": [{"key": s["key"], "url": discovery_url(s, since)} for s in sources]}, 0
    if not topic.spec["monitor"]["enabled"]:
        raise ValueError(f"Monitoring is disabled for {topic.id}")
    started = datetime.datetime.now(datetime.timezone.utc)
    run_id = started.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    directory = pathlib.Path(output_dir) if output_dir else ROOT / ".cache/atlas" / topic.id / run_id
    directory.mkdir(parents=True, exist_ok=True)
    # Refuse reused run directories: old snapshots must not look like new successes.
    if any(directory.iterdir()):
        raise ValueError(f"Discovery output directory is not empty: {directory}")
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(pool.map(lambda s: collect(s, directory, since), sources))
    (directory / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    candidates = {}
    for source, receipt in zip(sources, records):
        if not receipt["ok"] or source["format"] != "json":
            continue
        parsed = json.loads((directory / receipt["file"]).read_bytes())
        for candidate in candidates_from_snapshot(source, parsed):
            identity = norm_url(candidate["sourceUrl"])
            item = candidates.setdefault(identity, {**candidate, "sourceIdentity": identity,
                "topicId": topic.id, "status": "unreviewed", "discoveredVia": []})
            item["discoveredVia"].append(source["key"])
    report = {"schemaVersion": 1, "topicId": topic.id, "runId": run_id,
              "startedAt": started.isoformat(timespec="seconds"),
              "finishedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
              "since": since, "status": "partial-failure" if any(not r["ok"] for r in records) else "retrieved",
              "sourcesAttempted": len(records), "sourcesSucceeded": sum(r["ok"] for r in records),
              "coverage": "partial", "candidateCount": len(candidates), "reviewedNewCases": 0,
              "limitations": ["Successful retrieval does not prove exhaustive coverage or model attribution.",
                              "Search adapters inspect one bounded page per configured query; no complete-pagination claim.",
                              "Only GitHub and HN JSON searches currently emit candidate metadata; other snapshots require manual review.",
                              "Discovery does not change accepted data, metric freshness or the published refresh report."],
              "sources": records, "candidates": list(candidates.values())}
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    (directory / "report.json").write_text(serialized)
    if report_path:
        destination = pathlib.Path(report_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(serialized)
    summary = {k: report[k] for k in ("topicId", "runId", "status", "sourcesAttempted", "sourcesSucceeded", "candidateCount", "reviewedNewCases", "coverage")}
    summary["report"] = str(directory / "report.json")
    return summary, int(report["status"] == "partial-failure")
