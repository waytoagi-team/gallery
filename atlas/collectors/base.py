"""Fetch a configured bilingual base source into the topic cache.

The page is a Next.js app; every case object is embedded in the RSC flight payload
(self.__next_f.push chunks), even though only the first ~20 are rendered server-side.
"""
import datetime, json, pathlib, re, urllib.request

from ..config import ROOT


def fetch_cases(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    page = urllib.request.urlopen(req, timeout=60).read().decode("utf-8")
    flight = ""
    for chunk in re.findall(r"self\.__next_f\.push\((\[.*?\])\)</script>", page, flags=re.S):
        arr = json.loads(chunk)
        if len(arr) > 1 and isinstance(arr[1], str):
            flight += arr[1]
    dec, cases = json.JSONDecoder(), {}
    for m in re.finditer(r'\{"id":"case-\d+"', flight):
        obj, _ = dec.raw_decode(flight, m.start())
        cases[obj["id"]] = obj
    return cases


def fetch_base(topic):
    urls = topic.spec.get("baseSource")
    if not urls:
        raise ValueError(f"{topic.id} has no optional base source configured")
    raw = {lang: fetch_cases(url) for lang, url in urls.items()}
    if not raw["zh"] or set(raw["zh"]) != set(raw["en"]):
        raise ValueError("Empty or mismatched bilingual snapshot; keeping the previous file")
    print({k: len(v) for k, v in raw.items()})
    raw["fetchedAt"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    target = ROOT / ".cache" / "atlas" / topic.id / "base" / "raw.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = target.with_suffix(".tmp")
    staging.write_text(json.dumps(raw, ensure_ascii=False))
    staging.replace(target)
    return {"topic": topic.id, "raw": str(target)}
