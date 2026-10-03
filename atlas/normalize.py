"""Normalize a configured bilingual base source into an editorial candidate."""
import json, pathlib

from .config import ROOT

CATEGORIES = {k: (v["zh"], v["en"]) for k, v in json.loads((ROOT / "atlas/categories.json").read_text()).items()}

EVIDENCE = {"演示": "Demo", "评测": "Evaluation", "集成": "Integration", "教程": "Tutorial", "限制": "Limitation"}


def clean(obj):
    # Next.js RSC payload encodes missing values as "$undefined"
    return {k: (None if v == "$undefined" else v) for k, v in obj.items()}


def normalize_base(topic, raw_path, output_path):
    """Create a review candidate; replacing accepted data is an editorial action."""
    raw = json.loads(pathlib.Path(raw_path).read_text())
    zh, en = raw["zh"], raw["en"]
    if not zh or set(zh) != set(en):
        raise ValueError("Expected a nonempty, matching zh/en snapshot")
    cases = []
    for cid, z in sorted(zh.items(), key=lambda kv: kv[1]["caseNumber"]):
        z, e = clean(z), clean(en.get(cid, {}))
        cases.append({
            "id": f"uc-{z['caseNumber']:04d}",
            "source": "hn" if "ycombinator.com" in z["sourceUrl"] else "x",
            "platform": "Hacker News" if "ycombinator.com" in z["sourceUrl"] else "X",
            "category": z["category"],
            "evidenceType": z["evidenceType"],
            "evidenceType_en": EVIDENCE.get(z["evidenceType"], z["evidenceType"]),
            "title": z["title"],
            "title_en": e.get("title"),
            "summary": z["takeaway"],
            "summary_en": e.get("takeaway"),
            "author": z["author"],
            "sourceUrl": z["sourceUrl"],
            "date": (z.get("sourcePublishedAt") or z["publishedAt"])[:10],
            "likes": z.get("likes"),
            "bookmarks": z.get("bookmarks"),
            "mediaKind": z.get("mediaKind"),
            "poster": z.get("poster"),
            "video": z.get("video"),
        })
    meta = {"categories": {k: {"zh": v[0], "en": v[1]} for k, v in CATEGORIES.items()}, "count": len(cases)}
    if raw.get("fetchedAt"):
        meta["baseFetchedAt"] = raw["fetchedAt"]
    pathlib.Path(output_path).write_text(json.dumps({"meta": meta, "cases": cases}, ensure_ascii=False, indent=1))
    return {"topic": topic.id, "cases": len(cases), "candidateFile": str(output_path)}
