"""Merge all use-case sources into data/all_cases.json and render site/index.html."""
import csv, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
EXTRA_FILES = ["extra_x.json", "extra_github.json", "extra_hn.json", "extra_web.json"]
EVIDENCE = {"演示": "Demo", "评测": "Evaluation", "集成": "Integration", "教程": "Tutorial", "限制": "Limitation"}


def norm_url(u):
    u = re.sub(r"^https?://(www\.|mobile\.)?", "", u.strip().lower()).rstrip("/")
    u = u.replace("twitter.com/", "x.com/")
    # tweet URLs carry tracking params; elsewhere (e.g. HN ?id=) the query identifies the page
    return u.split("?")[0] if u.startswith("x.com/") else u.split("#")[0]


def main():
    base = json.loads((DATA / "base_cases.json").read_text())
    meta, cases = base["meta"], base["cases"]
    seen = {norm_url(c["sourceUrl"]) for c in cases}
    added = {}
    for fn in EXTRA_FILES:
        p = DATA / fn
        if not p.exists():
            continue
        for i, c in enumerate(json.loads(p.read_text())):
            u = norm_url(c.get("sourceUrl") or "")
            # one page (e.g. a launch post) can hold several distinct cases, so key extras on url + title
            key = (u, (c.get("title_en") or c.get("title") or "").strip().lower())
            if not u or u in seen or key in seen or c.get("category") not in meta["categories"]:
                continue
            seen.add(key)
            src = fn[len("extra_"):-len(".json")]
            cases.append({
                "id": f"{src}-{i + 1:03d}",
                # HN items found by the web search are grouped with the dedicated HN pass
                "source": "hn" if c.get("platform") == "Hacker News" else src,
                "platform": c.get("platform") or src,
                "category": c["category"],
                "evidenceType": c.get("evidenceType", "演示"),
                "evidenceType_en": EVIDENCE.get(c.get("evidenceType"), "Demo"),
                "title": c.get("title") or c.get("title_en"), "title_en": c.get("title_en") or c.get("title"),
                "summary": c.get("summary") or c.get("summary_en"), "summary_en": c.get("summary_en") or c.get("summary"),
                "author": c.get("author"), "sourceUrl": c["sourceUrl"], "date": c.get("date"),
                "likes": c.get("likes"), "bookmarks": c.get("bookmarks"), "stars": c.get("stars"),
                "mediaKind": "none",
            })
            added[cases[-1]["source"]] = added.get(cases[-1]["source"], 0) + 1
    meta = {**meta, "count": len(cases), "added": added}
    (DATA / "all_cases.json").write_text(json.dumps({"meta": meta, "cases": cases}, ensure_ascii=False, indent=1))
    fields = [k for k in cases[0] if k not in ("poster", "video")] + ["stars"]
    with open(DATA / "all_cases.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(cases)

    # compact payload for the page
    keep = ["id", "source", "platform", "category", "evidenceType", "evidenceType_en", "title", "title_en",
            "summary", "summary_en", "author", "sourceUrl", "date", "likes", "bookmarks", "stars", "mediaKind", "poster"]
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
