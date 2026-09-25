"""Fetch cheerselfai.com Opus 5.5 use cases (zh + en) into data/_raw_cheerselfai.json.

The page is a Next.js app; every case object is embedded in the RSC flight payload
(self.__next_f.push chunks), even though only the first ~20 are rendered server-side.
"""
import json, pathlib, re, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
URLS = {"zh": "https://cheerselfai.com/usecase/claude-opus-5-5",
        "en": "https://cheerselfai.com/en/usecase/claude-opus-5-5"}


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


def main():
    raw = {lang: fetch_cases(url) for lang, url in URLS.items()}
    (ROOT / "data" / "_raw_cheerselfai.json").write_text(json.dumps(raw, ensure_ascii=False))
    print({k: len(v) for k, v in raw.items()})


if __name__ == "__main__":
    main()
