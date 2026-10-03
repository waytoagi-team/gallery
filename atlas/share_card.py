"""Render or reuse fingerprinted topic share cards for reproducible offline builds."""
import hashlib, html, json, re
from .config import TEMPLATES

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


def card_markup(topic, data):
    custom = topic.spec.get("ogTemplate")
    template = (topic.content_path(custom) if custom else TEMPLATES / "og_image.html").read_text()
    values = card_values(data)
    values.update(MODEL_NAME=html.escape(topic.spec["name"]),
                  CARD_STATUS="尚无已审核案例" if not data["cases"] else "每条案例附原始出处",
                  AS_OF=data["meta"].get("asOf") or "—")
    return fill(template, values)


def ensure_card(topic, data, render=False, check=False):
    markup = card_markup(topic, data)
    fingerprint = hashlib.sha256(markup.encode()).hexdigest()
    out = topic.content / "assets/og-image.png"
    stamp = topic.content / "assets/og-image.card.json"
    prior = json.loads(stamp.read_text()) if stamp.exists() else {}
    valid = (out.exists() and prior.get("markupSha256") == fingerprint and
             prior.get("imageSha256") == hashlib.sha256(out.read_bytes()).hexdigest())
    if valid and not render:
        return out
    if check:
        raise ValueError(f"{topic.id}: share card is missing or stale; run atlas build with the development dependencies")
    try:
        render_png(markup, out)
    except ImportError as exc:
        raise ValueError("Share card needs Playwright: install requirements-dev.txt and Chromium, then rebuild") from exc
    stamp.write_text(json.dumps({"markupSha256": fingerprint,
                                "imageSha256": hashlib.sha256(out.read_bytes()).hexdigest()}, indent=2) + "\n")
    return out


def render_png(markup, out):
    from playwright.sync_api import sync_playwright
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 630}, device_scale_factor=1)
        page.route("**/*", lambda route: route.abort())
        page.set_content(markup, wait_until="load")
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": 1200, "height": 630})
        browser.close()
