"""Normalize the base Opus 5.5 use cases (zh + en) into data/base_cases.json."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

CATEGORIES = {
    "games": ("游戏开发", "Game Development"),
    "education": ("交互教育与可视化", "Interactive Learning & Visualization"),
    "3d": ("3D 建模与场景", "3D Modeling & Scenes"),
    "audio": ("音乐与声音", "Music & Sound"),
    "graphics": ("创意图形与动画", "Creative Graphics & Animation"),
    "web": ("网站与界面", "Websites & Interfaces"),
    "business": ("业务分析与文档", "Business Analysis & Documents"),
    "agents": ("Agent 与开发工作流", "Agents & Developer Workflows"),
    "vision": ("视觉理解与数据标注", "Visual Understanding & Annotation"),
    "video": ("视频编辑与制作", "Video Editing & Production"),
    "coding": ("代码维护与测试", "Code Maintenance & Testing"),
    "writing": ("写作与知识解释", "Writing & Explanations"),
    "science": ("科学研究与电路", "Scientific Research & Circuits"),
    "computer-use": ("电脑操作", "Computer Use"),
}
EVIDENCE = {"演示": "Demo", "评测": "Evaluation", "集成": "Integration", "教程": "Tutorial", "限制": "Limitation"}


def clean(obj):
    # Next.js RSC payload encodes missing values as "$undefined"
    return {k: (None if v == "$undefined" else v) for k, v in obj.items()}


def main():
    raw = json.loads((DATA / "_raw_base.json").read_text())
    zh, en = raw["zh"], raw["en"]
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
    (DATA / "base_cases.json").write_text(json.dumps({"meta": meta, "cases": cases}, ensure_ascii=False, indent=1))
    print(len(cases), "cases")


if __name__ == "__main__":
    main()
