"""Render the 1200x630 share card (assets/og-image.png) from scripts/og_image.html with current numbers.

Run after build_html.py whenever the case data changes. Needs Playwright with Chromium
(pip install playwright && python -m playwright install chromium); the page build itself stays stdlib-only.
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_ORDER = ["x", "github", "hn", "reddit", "video", "web"]


def card_values(data):
    """Every {{NAME}} the card template may use, computed from data/all_cases.json."""
    meta, cases = data["meta"], data["cases"]
    count = lambda key, value: sum(1 for c in cases if c.get(key) == value)
    values = {
        "COUNT": f"{len(cases):,}",
        "CATEGORIES": str(len(meta["categories"])),
        "SOURCES": str(sum(1 for s in SOURCE_ORDER if count("source", s))),
        "LIMITS": f"{count('evidenceType', '限制'):,}",
        "AS_OF": meta.get("asOf", ""),
    }
    for key, tag in (("DEMOS", "演示"), ("EVALS", "评测"), ("INTEGRATIONS", "集成"), ("TUTORIALS", "教程")):
        values[key] = f"{count('evidenceType', tag):,}"
    ranked = sorted(meta["categories"], key=lambda k: -count("category", k))
    for i, k in enumerate(ranked, 1):
        values[f"CAT{i}_ZH"], values[f"CAT{i}_EN"], values[f"CAT{i}_N"] = (
            meta["categories"][k]["zh"], meta["categories"][k]["en"], f"{count('category', k):,}")
    return values


def fill(template, values):
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", template)) - set(values))
    if missing:
        raise SystemExit(f"og_image.html uses unknown placeholders: {missing}")
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], template)


def main():
    from playwright.sync_api import sync_playwright
    data = json.loads((ROOT / "data" / "all_cases.json").read_text())
    html = fill((ROOT / "scripts" / "og_image.html").read_text(), card_values(data))
    out = ROOT / "assets" / "og-image.png"
    with sync_playwright() as p:
        browser = p.chromium.launch(args=sys.argv[1:] or None)
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(300)  # let local fonts settle
        page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
        browser.close()
    print(f"{out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
