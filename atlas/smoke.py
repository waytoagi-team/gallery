"""Browser regression checks at the same nested paths used in production."""
import argparse
import functools
import http.server
import json
from pathlib import Path
import shutil
import tempfile
import threading
from urllib.parse import urlsplit

from .config import topics, load_topic


def smoke(selected, report_path):
    from playwright.sync_api import sync_playwright
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    results = []
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    with tempfile.TemporaryDirectory(prefix="atlas-smoke-") as directory:
        for topic in selected:
            destination = Path(directory) / topic.spec["publicPath"].strip("/")
            shutil.copytree(topic.public, destination)
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=directory))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        origin = f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                for topic in selected:
                    count = json.loads((topic.public / "data/all_cases.json").read_text())["meta"]["count"]
                    for width, height in ((1440, 1000), (390, 844)):
                        page = browser.new_page(viewport={"width": width, "height": height}, locale="zh-CN")
                        errors = []
                        page.on("pageerror", lambda error: errors.append(str(error)))
                        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith(origin + "/") else route.abort())
                        for lang in ("zh", "en"):
                            url = origin + topic.spec["publicPath"] + f"?lang={lang}&sort=hot"
                            response = page.goto(url, wait_until="load")
                            assert response.status == 200, url
                            page.wait_for_selector("#grid article.card" if count else "#grid .empty")
                            assert topic.spec["name"] in page.title()
                            expected_lang = "zh-CN" if lang == "zh" else "en"
                            assert page.locator("html").get_attribute("lang") == expected_lang
                            assert page.locator("#sort").input_value() == "hot"
                            assert not page.evaluate("document.documentElement.scrollWidth > innerWidth + 1"), (topic.id, width, lang)
                            if count:
                                assert page.locator("#grid article.card").count() >= 24
                                page.locator("#q").fill("HAProxy")
                                page.wait_for_function("new URL(location.href).searchParams.get('q') === 'HAProxy'")
                                page.wait_for_selector("#grid article.card")
                            else:
                                expected = "尚无已审核案例" if lang == "zh" else "No reviewed cases yet"
                                assert expected in page.locator("#grid").inner_text()
                                assert page.locator("a[data-guide-en]").count() == 0
                                assert "2026-09-22" not in page.locator("#infoCard").inner_text()
                                assert "Opus" not in page.locator("body").inner_text()
                            button = page.locator("#langBtnM" if width == 390 else "#langBtn")
                            button.click()
                            other = "en" if lang == "zh" else "zh"
                            page.wait_for_function("lang => document.documentElement.lang === lang", arg="zh-CN" if other == "zh" else "en")
                            assert page.locator("#sort").input_value() == "hot"
                            if count:
                                assert page.locator("#q").input_value() == "HAProxy"
                                expected_guide = topic.spec["guide"][other]
                                assert page.locator("a[data-guide-en]").first.get_attribute("href") == expected_guide
                            assert not errors, errors
                            results.append({"topic": topic.id, "viewport": [width, height], "language": lang,
                                            "runtimeErrors": len(errors), "horizontalOverflow": False})
                        page.goto(origin + topic.spec["publicPath"] + "?lang=zh", wait_until="load")
                        page.wait_for_selector("#grid article.card" if count else "#grid .empty")
                        page.screenshot(path=str(report_path.parent / f"{topic.id}-{width}.png"), full_page=False)
                        page.close()
                    # Offline single-file behavior remains supported.
                    page = browser.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.route("https://**/*", lambda route: route.abort())
                    page.goto((topic.public / "index.html").as_uri())
                    page.wait_for_selector("#grid article.card" if count else "#grid .empty")
                    assert not errors, errors
                    page.close()
                    results.append({"topic": topic.id, "offlineFileMode": True, "runtimeErrors": 0})
                browser.close()
        finally:
            server.shutdown()
            server.server_close()
    report = {"status": "passed", "checks": results, "externalPosters": "Blocked for offline regression; original URLs unchanged"}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    return {"status": "passed", "views": len(results), "report": str(report_path)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    scope = parser.add_mutually_exclusive_group(required=True)
    scope.add_argument("--all", action="store_true")
    scope.add_argument("--topic")
    parser.add_argument("--report", type=Path, default=Path(".cache/validation/browser.json"))
    args = parser.parse_args()
    print(json.dumps(smoke(topics() if args.all else [load_topic(args.topic)], args.report)))
