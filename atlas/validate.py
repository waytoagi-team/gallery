"""Offline checks of reviewed records and the exact files deployed under a topic."""
import csv
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


def validate_cases(topic, payload):
    from .build import case_key
    cases, meta = payload["cases"], payload["meta"]
    ids, sources = set(), set()
    for case in cases:
        cid = case.get("id")
        if not cid or cid in ids:
            raise ValueError(f"{topic.id}: missing or duplicate case ID {cid}")
        key = case_key(case)
        if key in sources:
            raise ValueError(f"{topic.id}: duplicate source identity {key}")
        if case.get("category") not in meta["categories"]:
            raise ValueError(f"{topic.id}: unknown category for {cid}")
        if not case.get("title") or not case.get("sourceUrl"):
            raise ValueError(f"{topic.id}: missing title or source for {cid}")
        if topic.spec.get("attribution", {}).get("requireReviewMetadata"):
            required = ("checkedAt", "evidenceUrl", "evidenceBasis", "modelAttribution")
            if any(not case.get(field) for field in required):
                raise ValueError(f"{topic.id}: case {cid} lacks editorial evidence metadata")
            attribution = case["modelAttribution"]
            if (not isinstance(attribution, dict) or attribution.get("topicId") != topic.id
                    or attribution.get("basis") != "explicit-source" or not attribution.get("role")):
                raise ValueError(f"{topic.id}: case {cid} lacks explicit version attribution and role")
        if case.get("source") == "github" and case.get("githubKind") != "repository" and "stars" in case:
            raise ValueError(f"{topic.id}: inherited repository stars for {cid}")
        ids.add(cid)
        sources.add(key)
    if meta["count"] != len(cases):
        raise ValueError(f"{topic.id}: incorrect case count")


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if value and key in ("src", "href", "poster"):
                self.urls.append(value)
            elif value and key == "srcset" and not value.startswith("data:"):
                self.urls.extend(part.strip().split()[0] for part in value.split(",") if part.strip())


def validate_public(topic, directory):
    directory = Path(directory)
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        if path.is_symlink() or any(part.startswith(".") for part in relative.parts):
            raise ValueError(f"Unexpected hidden file or symlink in public: {relative}")
        if path.is_file() and path.suffix not in {".html", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".json", ".csv", ".css", ".js", ".ico"}:
            raise ValueError(f"Unexpected public file: {relative}")
    payload = json.loads((directory / "data/all_cases.json").read_text())
    validate_cases(topic, payload)
    with (directory / "data/all_cases.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != len(payload["cases"]):
        raise ValueError("CSV and JSON counts differ")
    if [r["id"] for r in rows] != [r["id"] for r in payload["cases"]]:
        raise ValueError("CSV and JSON identities differ")
    for row, case in zip(rows, payload["cases"]):
        for field, value in row.items():
            original = case.get(field)
            expected = (json.dumps(original, ensure_ascii=False) if isinstance(original, (dict, list))
                        else "" if original is None else str(original))
            if value != expected:
                raise ValueError(f"CSV and JSON differ at {case['id']}.{field}")
    for path in directory.rglob("*.html"):
        markup = path.read_text()
        refs = References()
        refs.feed(markup)
        refs.urls.extend(re.findall(r"url\(['\"]?([^)'\"]+)", markup))
        for url in refs.urls:
            parts = urlsplit(url)
            if parts.scheme or parts.netloc or not parts.path or "${" in url:
                continue
            if parts.path.startswith("/"):
                raise ValueError(f"Root-relative URL in {path.name}: {url}")
            target = (path.parent / unquote(parts.path)).resolve()
            if not target.is_relative_to(directory.resolve()):
                raise ValueError(f"URL escapes public directory: {url}")
            if target.is_dir():
                target /= "index.html"
            if not target.is_file():
                raise ValueError(f"Missing local asset in {path.relative_to(directory)}: {url}")
    index = (directory / "index.html").read_text()
    if re.search(r"\{\{[A-Z_]+\}\}|/\*__[A-Z_]+__\*/", index):
        raise ValueError("Unresolved page template placeholder")
    if topic.page_url not in index:
        raise ValueError("Incorrect canonical topic URL")
    if (directory / "build.json").exists():
        manifest = json.loads((directory / "build.json").read_text())
        if manifest.get("topicId") != topic.id or manifest.get("caseCount") != len(rows):
            raise ValueError("Build manifest refers to another topic or snapshot")
        actual = {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in directory.rglob("*") if p.is_file() and p != directory / "build.json"}
        if actual != manifest["files"]:
            raise ValueError("Public file manifest mismatch")
    return {"topic": topic.id, "cases": len(rows), "status": "passed"}
