"""Merge all use-case sources into data/all_cases.json and render site/index.html."""
import csv, json, pathlib, re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EXTRA_FILES = ["extra_x.json", "extra_github.json", "extra_hn.json", "extra_web.json", "extra_lists.json",
               "extra_reddit.json", "extra_video.json", "extra_gosail.json"]
PLATFORM_SOURCE = {"X": "x", "GitHub": "github", "Hacker News": "hn", "Reddit": "reddit", "YouTube": "video", "Bilibili": "video"}
EVIDENCE = {"演示": "Demo", "评测": "Evaluation", "集成": "Integration", "教程": "Tutorial", "限制": "Limitation"}


def norm_url(u):
    parts = urlsplit(u.strip())
    host = re.sub(r"^(www\.|mobile\.|m\.)", "", parts.netloc.lower())
    path = parts.path.rstrip("/")
    query = dict(parse_qsl(parts.query))
    if host in ("x.com", "twitter.com"):
        m = re.search(r"/status/(\d+)", path)
        if m:
            return "x.com/i/status/" + m.group(1)
    if host in ("reddit.com", "old.reddit.com"):
        m = re.search(r"/comments/([a-z0-9]+)", path, re.I)
        if m:
            return "reddit.com/comments/" + m.group(1).lower()
    if host in ("youtube.com", "youtu.be"):
        vid = query.get("v") if host == "youtube.com" else path.lstrip("/")
        if not vid:
            m = re.match(r"/(?:shorts|embed)/([\w-]{11})", path)
            vid = m.group(1) if m else None
        if vid:
            return "youtube.com/watch?v=" + vid
    if host == "bilibili.com" and path.startswith("/video/"):
        return host + path
    if host == "github.com":
        path = re.sub(r"\.git$", "", path.lower())
    query = {k: v for k, v in query.items() if not k.startswith("utm_") and k not in ("fbclid", "gclid", "si", "feature")}
    return urlunsplit(("", host, path, urlencode(sorted(query.items())), "")).lstrip("/")


def case_key(c):
    u = norm_url(c.get("sourceUrl") or "")
    # Posts, videos and repositories identify one case even if the title changes.
    # Editorial pages can document multiple distinct experiments/customer results.
    if u.startswith(("x.com/", "reddit.com/", "youtube.com/", "bilibili.com/", "news.ycombinator.com/", "github.com/")):
        return (u,)
    return (u, (c.get("title_en") or c.get("title") or "").strip().lower())


def apply_enrichments(cases, enrichments):
    """Apply reviewed evidence after deduplication, without changing case identity.

    Only immutable X post identities are supported. This avoids applying one
    editorial-page patch to multiple independent experiments on the same URL.
    """
    by_url = {norm_url(c["sourceUrl"]): c for c in cases}
    scalars = ("likes", "bookmarks", "views", "metricsCheckedAt")
    lists = ("resources", "promptEvidence", "relatedSources", "sourceSnapshots")
    for patch in enrichments:
        key = norm_url(patch["sourceUrl"])
        if not key.startswith("x.com/i/status/") or key not in by_url:
            raise ValueError(f"Enrichment target missing or ambiguous: {key}")
        unknown = set(patch) - set(scalars) - set(lists) - {"sourceUrl"}
        if unknown:
            raise ValueError(f"Unsupported enrichment fields: {sorted(unknown)}")
        case = by_url[key]
        if patch.get("metricsCheckedAt", "") >= case.get("metricsCheckedAt", ""):
            for field in scalars:
                if field in patch:
                    case[field] = patch[field]
        for field in lists:
            if field not in patch:
                continue
            existing = list(case.get(field, []))
            for item in patch[field]:
                # Resource fragments can identify different sections of a guide.
                if field == "resources":
                    duplicate = any(x["url"] == item["url"] for x in existing)
                else:
                    duplicate = item in existing
                if not duplicate:
                    existing.append(item)
            case[field] = existing
    return cases


def main():
    base = json.loads((DATA / "base_cases.json").read_text())
    meta, cases = base["meta"], []
    seen, duplicates = set(), 0
    for c in base["cases"]:
        key = case_key(c)
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        cases.append(c)
    added = {}
    for fn in EXTRA_FILES:
        p = DATA / fn
        if not p.exists():
            continue
        for i, c in enumerate(json.loads(p.read_text())):
            u = norm_url(c.get("sourceUrl") or "")
            key = case_key(c)
            if key in seen:
                duplicates += 1
                continue
            if not u or c.get("category") not in meta["categories"]:
                continue
            seen.add(key)
            src = fn[len("extra_"):-len(".json")]
            cases.append({
                "id": f"{src}-{i + 1:03d}",
                # group by where the case lives, not by which search pass found it
                "source": PLATFORM_SOURCE.get(c.get("platform"), "web" if src in ("lists", "reddit", "video") else src),
                "platform": c.get("platform") or src,
                "category": c["category"],
                "evidenceType": c.get("evidenceType", "演示"),
                "evidenceType_en": EVIDENCE.get(c.get("evidenceType"), "Demo"),
                "title": c.get("title") or c.get("title_en"), "title_en": c.get("title_en") or c.get("title"),
                "summary": c.get("summary") or c.get("summary_en"), "summary_en": c.get("summary_en") or c.get("summary"),
                "author": c.get("author"), "sourceUrl": c["sourceUrl"], "date": c.get("date"),
                "likes": c.get("likes"), "bookmarks": c.get("bookmarks"), "stars": c.get("stars"), "views": c.get("views"),
                "mediaKind": c.get("mediaKind") or "none", "poster": c.get("poster"),
                **{k: c[k] for k in ("discoveredVia", "checkedAt", "evidenceUrl", "evidenceBasis", "metricsCheckedAt", "resources") if c.get(k)},
            })
            added[cases[-1]["source"]] = added.get(cases[-1]["source"], 0) + 1
    # metric_refreshes.json holds metrics-only patches from full refreshes, kept apart from
    # case_enrichments.json so re-importing GoSail cannot drop them; newer metricsCheckedAt wins.
    for name in ("case_enrichments.json", "metric_refreshes.json"):
        enrichment_path = DATA / name
        if enrichment_path.exists():
            apply_enrichments(cases, json.loads(enrichment_path.read_text())["cases"])
    # snapshot date = newest dated case (sources lag a day or two behind the fetch)
    for c in cases:
        # video thumbnails: derive YouTube posters from the id, force https for Bilibili's CDN
        m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})", c["sourceUrl"])
        if m and not c.get("poster"):
            c["poster"], c["mediaKind"] = f"https://i.ytimg.com/vi/{m.group(1)}/hqdefault.jpg", "video"
        if (c.get("poster") or "").startswith(("http://", "//")) and "hdslb.com" in c["poster"]:
            c["poster"] = "https://" + c["poster"].split("//", 1)[1]
    meta = {**meta, "count": len(cases), "added": added, "asOf": max(c["date"] for c in cases if c.get("date")), "duplicatesSkipped": duplicates}
    report_path = DATA / "refresh_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text())
        meta["refreshedAt"] = report["refreshedAt"]
        meta["refreshScope"] = report.get("scope", "public-source refresh")
        meta["lastFullRefreshAt"] = report.get("lastFullRefreshAt", report["refreshedAt"])
    (DATA / "all_cases.json").write_text(json.dumps({"meta": meta, "cases": cases}, ensure_ascii=False, indent=1))
    fields = list(dict.fromkeys(k for c in cases for k in c if k not in ("poster", "video")))
    with open(DATA / "all_cases.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                     for k, v in c.items()} for c in cases)

    # compact payload for the page
    keep = ["id", "source", "platform", "category", "evidenceType", "evidenceType_en", "title", "title_en",
            "summary", "summary_en", "author", "sourceUrl", "date", "likes", "bookmarks", "stars", "views", "mediaKind", "poster", "resources"]
    payload = {"meta": meta, "cases": [{k: c[k] for k in keep if c.get(k) not in (None, "")} for c in cases]}
    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    tpl = (ROOT / "scripts" / "template.html").read_text()
    # inline the brand logos so index.html stays a single self-contained file
    for key, name in (("LOGO_LIGHT", "waytoagi-logo-light.svg"), ("LOGO_DARK", "waytoagi-logo-dark.svg")):
        svg = (ROOT / "assets" / name).read_text().strip()
        tpl = tpl.replace(f"/*__{key}__*/", svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1))
    out = ROOT / "index.html"
    out.write_text(tpl.replace("/*__DATA__*/null", blob))
    print(f"{len(cases)} cases (added {added}) -> {out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
