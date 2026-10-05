"""Merge reviewed topic inputs and build a self-contained public directory."""
import csv, datetime, hashlib, html, ipaddress, json, pathlib, re, shutil, tempfile
from decimal import ROUND_HALF_UP, Decimal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from .github_metrics import sanitize_github_metrics
from .config import ROOT, TEMPLATES, load_topic

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


def apply_poster_enrichments(cases, enrichments):
    """Fill missing posters from reviewed context, guarding both ID and source identity.

    Editorial URLs can describe multiple experiments. Matching the editorial title
    as well as the ID prevents a shared article cover from silently patching them all.
    Upstream posters always win; a later import must not inherit evidence for a
    different image from this overlay.
    """
    by_id = {c["id"]: c for c in cases}
    if len(by_id) != len(cases):
        raise ValueError("Duplicate case IDs in poster enrichment targets")
    required = {"id", "sourceUrl", "title_en", "poster", "mediaKind", "posterEvidence"}
    seen = set()
    for patch in enrichments:
        if set(patch) != required:
            raise ValueError("Poster enrichment has missing or unsupported fields")
        target = by_id.get(patch["id"])
        if target is None or case_key(target) != case_key(patch) or patch["id"] in seen:
            raise ValueError(f"Poster enrichment target missing, changed or duplicated: {patch['id']}")
        seen.add(patch["id"])
        if not isinstance(patch["posterEvidence"], dict):
            raise ValueError(f"Poster evidence must be an object: {patch['id']}")
        for url in (patch["poster"], patch["posterEvidence"].get("sourcePage", "")):
            parsed = urlsplit(url)
            host = parsed.hostname or ""
            try:
                public = ipaddress.ip_address(host).is_global
            except ValueError:
                public = "." in host and not host.endswith((".localhost", ".local", ".internal"))
            if parsed.scheme != "https" or not public or parsed.username or parsed.password:
                raise ValueError(f"Poster evidence requires a public HTTPS URL: {patch['id']}")
        evidence = patch["posterEvidence"]
        if (patch["mediaKind"] not in ("image", "video") or
                evidence.get("reviewStatus") != "accepted" or
                not evidence.get("checkedAt") or not evidence.get("method") or
                not evidence.get("relation") or
                not isinstance(evidence.get("width"), int) or evidence["width"] < 180 or
                not isinstance(evidence.get("height"), int) or evidence["height"] < 100 or
                not re.fullmatch(r"[0-9a-f]{64}", evidence.get("imageSha256", ""))):
            raise ValueError(f"Poster enrichment lacks verified image evidence: {patch['id']}")
        if not target.get("poster"):
            target.update({k: patch[k] for k in ("poster", "mediaKind", "posterEvidence")})
    return cases


SUBMIT_URL = "https://github.com/waytoagi-team/gallery/issues/new?template=case-submission.yml"
PAGE_FIELDS = ["id", "source", "platform", "category", "evidenceType", "title", "title_en", "summary", "summary_en",
               "author", "sourceUrl", "date", "likes", "bookmarks", "stars", "views", "mediaKind", "poster", "resources",
               "githubKind", "reactions", "comments"]
TWIMG = re.compile(r"^(https://pbs\.twimg\.com/(?:media|amplify_video_thumb|ext_tw_video_thumb|tweet_video_thumb)/[^?]+?)"
                   r"(?:\.(?:jpe?g|png|webp))?(?:\?.*)?$")


def page_poster(url):
    """Ask the image CDN for a card-sized WebP instead of the original upload (page payload only)."""
    if not url:
        return url
    m = TWIMG.match(url)
    if m:
        return m.group(1) + "?format=webp&name=small"
    if re.match(r"^https://i\d\.hdslb\.com/bfs/[^@?]+\.(?:jpe?g|png|webp)$", url):
        return url + "@640w_360h_1c.webp"
    return url


def boot_summary(meta, cases, topic=None):
    """Everything the first screen needs, so it renders before the large case payload is parsed."""
    topic = topic or load_topic()
    counts = {dim: {} for dim in ("src", "cat", "ev")}
    cube = {}  # src|cat|ev -> count, so facet combinations are exact before the case data is parsed
    for c in cases:
        for dim, key in (("src", "source"), ("cat", "category"), ("ev", "evidenceType")):
            counts[dim][c[key]] = counts[dim].get(c[key], 0) + 1
        cell = f"{c['source']}|{c['category']}|{c['evidenceType']}"
        cube[cell] = cube.get(cell, 0) + 1
    liked = sorted((c for c in cases if c.get("likes")), key=lambda c: -c["likes"])[:14]
    refreshed = {"zh": meta.get("asOf", ""), "en": meta.get("asOf", "")}
    if meta.get("refreshedAt"):
        t = datetime.datetime.fromisoformat(meta["refreshedAt"]).astimezone(datetime.timezone(datetime.timedelta(hours=8)))
        refreshed = {"zh": t.strftime("%Y-%m-%d %H:%M") + " 北京时间", "en": t.strftime("%Y-%m-%d %H:%M") + " UTC+8"}
    scope = meta.get("refreshScope")
    scope = scope if isinstance(scope, dict) else {"zh": "公开信源", "en": "Public sources"}
    return {
        "meta": {k: meta[k] for k in ("categories", "count", "asOf")},
        "info": {"released": topic.spec.get("releasedAt") or "—", "refreshed": refreshed, "scope": {"zh": scope["zh"], "en": scope["en"]}},
        "counts": counts,
        "cube": cube,
        "xLikes": sum(c.get("likes") or 0 for c in cases if c["source"] == "x"),
        "tops": [{k: c[k] for k in ("title", "title_en", "sourceUrl", "likes") if c.get(k) is not None} for c in liked],
    }


SOURCE_ORDER = ["x", "github", "hn", "reddit", "video", "web"]  # same order as SRC in template.html


def js_esc(text):
    """Mirror of the page's esc(): only & < > \" are escaped."""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def compact_zh(n):
    """Intl.NumberFormat('zh-CN', {notation: 'compact', maximumFractionDigits: 1}) for the hero stat.

    Rounds half up like Intl and picks the unit after rounding (99,999,999 -> 1亿).
    """
    if n < 10 ** 4:
        return str(n)
    for unit, size in (("万", 10 ** 4), ("亿", 10 ** 8)):
        value = (Decimal(n) / size).quantize(Decimal("0.1"), ROUND_HALF_UP)
        if unit == "亿" or value < 10 ** 4:
            return f"{value.normalize():f}{unit}"


def hero_blocks(zh, boot):
    """zh HTML of the hero blocks the app script renders, pre-filled so phones never paint them empty.

    Must stay identical to renderStatic() in template.html: after a template change, compare each block's raw
    HTML with its innerHTML after load (see README).
    """
    total = f"{boot['meta']['count']:,}"
    n_cat, n_src = len(boot["meta"]["categories"]), sum(1 for s in SOURCE_ORDER if boot["counts"]["src"].get(s))
    fields = " · ".join(f'<span class="nw">{js_esc(f)}</span>' for f in zh["fields"])
    rows = [js_esc(v) for v in (boot["info"]["released"], boot["meta"]["asOf"] or "—", boot["info"]["refreshed"]["zh"] or "—", boot["info"]["scope"]["zh"])]
    rows += [fields, f'<a href="data/all_cases.json" download>JSON</a> / <a href="data/all_cases.csv" download>CSV</a> · {js_esc(zh["offline"])}']
    vals = [total, n_cat, compact_zh(boot["xLikes"]), f"{boot['counts']['ev'].get('限制', 0):,}"]
    stats = "".join(
        f'<button class="stat" type="button" data-ev="限制" data-jump="1"><b>{v}</b><span>{zh["stats"][i]}</span></button>' if i == 3
        else f'<div class="stat{" hl" if i == 0 else ""}"><b>{v}</b><span>{zh["stats"][i]}</span></div>' for i, v in enumerate(vals))
    return {
        '<p class="tagline" id="tagline"></p>': f'<p class="tagline" id="tagline">{zh["taglineT"].format(n=total, c=n_cat, s=n_src)}</p>',
        '<a class="hero-cta" id="heroCta" href="#cases"></a>':
            f'<a class="hero-cta" id="heroCta" href="#cases">{js_esc(zh["heroCtaT"].format(n=total))} <span aria-hidden="true">↓</span></a>',
        '<dl id="infoCard"></dl>': '<dl id="infoCard">' + "".join(
            f"<div><dt>{js_esc(k)}</dt><dd>{rows[i]}</dd></div>" for i, k in enumerate(zh["info"])) + "</dl>",
        '<div class="stats" id="stats"></div>': f'<div class="stats" id="stats">{stats}</div>',
    }


def fill_i18n(markup, strings):
    """Pre-fill empty data-i18n elements with the default (zh) text so the page never paints empty chips."""
    def fill(m):
        text = strings.get(m.group(2))
        return m.group(1) + html.escape(text, quote=False) if isinstance(text, str) else m.group(0)
    return re.sub(r'(<[a-z0-9]+\b[^>]*\bdata-i18n="(\w+)"[^>]*>)(?=</)', fill, markup)


def to_script(obj):
    """JSON for an inline <script>: "\\u003c" keeps "</script" and "<!--" out; JSON.parse reads it back as "<"."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")


def render_page(meta, cases, topic=None, og_path=None):
    topic = topic or load_topic()
    cases = [sanitize_github_metrics(dict(c)) for c in cases]
    payload = {"cases": [{k: (page_poster(c[k]) if k == "poster" else c[k]) for k in PAGE_FIELDS if c.get(k) not in (None, "")}
                         for c in cases]}
    tpl = (TEMPLATES / "page.html").read_text()
    tpl = tpl.replace("/*__RANKING__*/", (TEMPLATES / "ranking.js").read_text())
    # inline the brand logos so index.html stays a single self-contained file
    for key, name in (("LOGO_LIGHT", "waytoagi-logo-light.svg"), ("LOGO_DARK", "waytoagi-logo-dark.svg")):
        svg = (TEMPLATES / "assets" / name).read_text().strip()
        tpl = tpl.replace(f"/*__{key}__*/", svg.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1))
    head, sep, rest = tpl.partition('<script id="i18n" type="application/json">')
    # HTML and script string contents need distinct escaping.
    for marker, value in (("{{MODEL_NAME}}", topic.spec["name"]), ("{{MODEL_SHORT}}", topic.spec["shortName"])):
        head = head.replace(marker, html.escape(value))
        rest = rest.replace(marker, json.dumps(value, ensure_ascii=False)[1:-1].replace("'", "\\u0027").replace("<", "\\u003c"))
    if not topic.spec.get("guide"):
        head = re.sub(r'<a\b(?=[^>]*\{\{GUIDE_URL\}\})[^>]*>.*?</a>', '', head, flags=re.S)
    strings = json.loads(rest[:rest.index("</script>")])
    if not cases:
        strings["zh"].update(taglineT=f"正在整理 {html.escape(topic.spec['name'])} 的公开项目与使用记录。候选须核对原始出处和模型版本后收录，目前尚无已审核案例。", heroCtaT="查看收录进度")
        strings["en"].update(taglineT=f"Collecting public {html.escape(topic.spec['name'])} projects and usage reports. Candidates need source and model-version review before inclusion. No reviewed cases yet.", heroCtaT="View collection status")
        strings["zh"]["stats"][1] = "预设分类"
        strings["en"]["stats"][1] = "Available categories"
        rest = to_script(strings) + rest[rest.index("</script>"):]
    boot = boot_summary(meta, cases, topic)
    head = fill_i18n(head, strings["zh"])
    for empty, filled in hero_blocks(strings["zh"], boot).items():
        assert head.count(empty) == 1, empty
        head = head.replace(empty, filled)
    tpl = head + sep + rest
    n = f"{len(cases):,}"
    from .share_card import card_values, fill  # stdlib-only; Playwright is imported only when rendering the card
    card = card_values({"meta": meta, "cases": cases})
    png = og_path or topic.content / "assets" / "og-image.png"
    version = hashlib.sha256(png.read_bytes()).hexdigest()[:10] if png.exists() else "0"
    desc = {
        "{{DESC_ZH}}": f"{topic.spec['name']} 的 {n} 个公开使用案例，来自 X、Reddit、GitHub、Hacker News、YouTube / B 站与网页，"
                       "含任务类别、证据类型、中英文摘要与原帖链接。",
        "{{DESC_EN}}": f"{n} public {topic.spec['name']} use cases from X, Reddit, GitHub, Hacker News, YouTube / Bilibili and the web, "
                       "with task categories, evidence types, zh/en summaries and source links.",
        "{{PAGE_URL}}": topic.page_url, "{{SUBMIT_URL}}": SUBMIT_URL, "{{REPO_URL}}": topic.repo_url,
        # versioned so X/WeChat/Slack caches pick up a re-rendered card
        "{{OG_IMAGE}}": f"{topic.page_url}assets/og-image.png?v={version}",
        "{{OG_ALT_ZH}}": fill(topic.spec.get("ogAlt", {}).get("zh", topic.spec["name"] + " 案例图谱，收录 {{COUNT}} 条公开案例，含 {{LIMITS}} 条失败与限制。"), card), "{{OG_ALT_EN}}": fill(topic.spec.get("ogAlt", {}).get("en", topic.spec["name"] + " use-case atlas: {{COUNT}} public cases, including {{LIMITS}} limitations."), card),
        # relative to index.html; placeholders keep the template's own relative-link check clean
        "{{CSV_URL}}": "data/all_cases.csv", "{{JSON_URL}}": "data/all_cases.json",
        "{{GUIDE_URL}}": (topic.spec.get("guide") or {}).get("zh", ""), "{{GUIDE_URL_EN}}": (topic.spec.get("guide") or {}).get("en", ""),
    }
    for key, value in desc.items():
        tpl = tpl.replace(key, html.escape(value))
    return (tpl.replace("/*__BOOT__*/null", to_script(boot))
               .replace("/*__DATA__*/null", to_script(payload)))


def merge_cases(topic):
    DATA = topic.data
    base = json.loads((DATA / "base_cases.json").read_text()) if (DATA / "base_cases.json").exists() else {"meta": {"categories": json.loads((ROOT / "atlas/categories.json").read_text())}, "cases": []}
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
            # A withdrawn record keeps its slot so later positional IDs never shift or get reused.
            if c.get("withdrawn"):
                continue
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
                "id": c.get("id") or f"{src}-{i + 1:03d}",
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
                **{k: c[k] for k in ("githubKind", "reactions", "comments", "metricsSourceUrl") if c.get(k) is not None},
                **{k: c[k] for k in ("modelAttribution",) if c.get(k) is not None},
            })
            added[cases[-1]["source"]] = added.get(cases[-1]["source"], 0) + 1
    # metric_refreshes.json holds metrics-only patches from full refreshes, kept apart from
    # case_enrichments.json so re-importing GoSail cannot drop them; newer metricsCheckedAt wins.
    for name in ("case_enrichments.json", "reply_enrichments.json", "metric_refreshes.json"):
        enrichment_path = DATA / name
        if enrichment_path.exists():
            apply_enrichments(cases, json.loads(enrichment_path.read_text())["cases"])
    poster_path = DATA / "poster_enrichments.json"
    if poster_path.exists():
        apply_poster_enrichments(cases, json.loads(poster_path.read_text())["cases"])
    # snapshot date = newest dated case (sources lag a day or two behind the fetch)
    for c in cases:
        sanitize_github_metrics(c)
        # video thumbnails: derive YouTube posters from the id, force https for Bilibili's CDN
        m = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([\w-]{11})", c["sourceUrl"])
        if m and not c.get("poster"):
            c["poster"], c["mediaKind"] = f"https://i.ytimg.com/vi/{m.group(1)}/hqdefault.jpg", "video"
        if (c.get("poster") or "").startswith(("http://", "//")) and "hdslb.com" in c["poster"]:
            c["poster"] = "https://" + c["poster"].split("//", 1)[1]
    meta = {**meta, "count": len(cases), "added": added, "asOf": max((c["date"] for c in cases if c.get("date")), default=""), "duplicatesSkipped": duplicates}
    report_path = DATA / "refresh_report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text())
        meta["refreshedAt"] = report.get("refreshedAt")
        meta["refreshScope"] = report.get("scope", "public-source refresh")
        meta["lastFullRefreshAt"] = report.get("lastFullRefreshAt", report["refreshedAt"])
    return {"meta": meta, "cases": cases}


def write_exports(payload, data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    cases = payload["cases"]
    (data_dir / "all_cases.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    fields = list(dict.fromkeys(k for c in cases for k in c if k != "video")) or [
        "id", "source", "platform", "category", "evidenceType", "title", "title_en",
        "summary", "summary_en", "author", "sourceUrl", "date"]
    with open(data_dir / "all_cases.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                     for k, v in c.items()} for c in cases)


def file_hashes(directory):
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(directory.rglob("*")) if p.is_file()}


def build_topic(topic, check=False, render_card=False):
    from .share_card import ensure_card
    from .validate import validate_cases, validate_public
    payload = merge_cases(topic)
    validate_cases(topic, payload)
    # An unchanged, fingerprinted card is reused so offline verification does not
    # require a browser or depend on different platform font rasterizers.
    card = ensure_card(topic, payload, render=render_card, check=check)
    with tempfile.TemporaryDirectory(prefix="atlas-build-") as directory:
        out = pathlib.Path(directory)
        for folder in ("assets", "blog"):
            source = topic.content / folder
            if source.exists():
                shutil.copytree(source, out / folder, ignore=shutil.ignore_patterns(".*", "*.card.json"))
        # Preserve original article inputs; normalize insignificant trailing space
        # only in generated copies, which are newly added files in this migration.
        for article in out.rglob("*.html"):
            article.write_text(re.sub(r"[ \t]+$", "", article.read_text(), flags=re.M))
        (out / "assets").mkdir(exist_ok=True)
        shutil.copy2(card, out / "assets/og-image.png")
        write_exports(payload, out / "data")
        page = render_page(payload["meta"], payload["cases"], topic, card)
        (out / "index.html").write_text(re.sub(r"[ \t]+$", "", page, flags=re.M))
        hashes = file_hashes(out)
        (out / "build.json").write_text(json.dumps({"schemaVersion": 1, "topicId": topic.id,
            "publicPath": topic.spec["publicPath"], "caseCount": len(payload["cases"]),
            "files": hashes}, ensure_ascii=False, indent=2) + "\n")
        validate_public(topic, out)
        if check:
            expected, actual = file_hashes(out), file_hashes(topic.public)
            changed = sorted(k for k in set(expected) | set(actual) if expected.get(k) != actual.get(k))
            if changed:
                raise ValueError(f"{topic.id}: stale public files: {', '.join(changed[:20])}; run atlas build")
        else:
            # Build and validate in isolation before replacing the tracked output.
            topic.public.mkdir(parents=True, exist_ok=True)
            for p in topic.public.iterdir():
                if p.is_dir(): shutil.rmtree(p)
                else: p.unlink()
            shutil.copytree(out, topic.public, dirs_exist_ok=True)
    return {"topic": topic.id, "cases": len(payload["cases"]), "checked": check,
            "public": str(topic.public.relative_to(ROOT))}
