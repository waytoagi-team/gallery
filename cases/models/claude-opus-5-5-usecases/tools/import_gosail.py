"""Materialize a reviewed GoSail snapshot; never infer acceptance from a feed.

Run collect_gosail.py at the review's pinned revision, then pass its cache path.
The offline build uses the resulting committed extras and enrichment overlay.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def post_id(url):
    match = re.search(r"(?:x\.com|twitter\.com)/[^/]+/status/(\d+)", url)
    return match[1] if match else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=pathlib.Path, required=True)
    args = parser.parse_args()
    review = json.loads((DATA / "gosail_review.json").read_text())
    manifest = json.loads((args.cache / "manifest.json").read_text())
    source_bytes = (args.cache / "upstream-cases.json").read_bytes()
    if (manifest["ref"] != review["meta"]["ref"] or
            hashlib.sha256(source_bytes).hexdigest() != review["meta"]["sourceJsonSha256"]):
        raise ValueError("Cache does not match the pinned review; review new source versions first")
    source = {c["id"]: c for c in json.loads(source_bytes)["cases"]}
    decisions = review["cases"]
    if len(decisions) != len(source) or {d["sourceId"] for d in decisions} != set(source):
        raise ValueError("Every source item must have exactly one reviewed decision")
    receipts = {r["id"]: r for r in manifest["posts"]}
    external = {r["url"]: r for r in json.loads((DATA / "gosail_fetch_manifest.json").read_text())["externalEvidence"]}
    included = {post_id(d["targetUrl"]) for d in decisions if d["action"] in ("add", "existing")}
    extras, patches = [], {}

    def read_post(pid):
        receipt = receipts[pid]
        raw = (args.cache / "posts" / (pid + ".json")).read_bytes()
        if not receipt["ok"] or hashlib.sha256(raw).hexdigest() != receipt["sha256"]:
            raise ValueError(f"Post receipt mismatch: {pid}")
        return json.loads(raw)["tweet"], receipt

    def resource(patch, url, label, label_en):
        if not url.startswith(("https://", "http://")):
            raise ValueError(f"Unexpected resource scheme: {url}")
        if url not in {r["url"] for r in patch["resources"]}:
            patch["resources"].append({"label": label, "label_en": label_en, "url": url})

    for decision in decisions:
        action = decision["action"]
        if action not in ("add", "existing", "related", "exclude"):
            raise ValueError(f"Unknown action: {action}")
        if action == "exclude":
            continue
        upstream = source[decision["sourceId"]]
        tweet, receipt = read_post(upstream["id"])
        target = decision["targetUrl"]
        tid = post_id(target)
        if action == "related" and tid not in included:
            # Related targets may be gallery cases outside this source snapshot.
            baseline = json.loads((ROOT / "public/data/all_cases.json").read_text())["cases"]
            if tid not in {post_id(c["sourceUrl"]) for c in baseline}:
                raise ValueError(f"Unresolved related case: {target}")
        patch = patches.setdefault(tid, {"sourceUrl": target, "resources": [], "sourceSnapshots": []})
        patch["sourceSnapshots"].append({"source": review["meta"]["sourceRepo"], "ref": manifest["ref"],
                                         "sourceId": upstream["id"], "relation": action,
                                         "checkedAt": receipt["checkedAt"], "evidenceSha256": receipt["sha256"]})
        if action in ("add", "existing"):
            patch.update({k: tweet[k] for k in ("likes", "bookmarks", "views") if tweet.get(k) is not None})
            patch["metricsCheckedAt"] = receipt["checkedAt"]
        if action == "add":
            media = (tweet.get("media") or {}).get("all", [])
            poster = next((x.get("thumbnail_url") for x in media if x.get("type") == "video"), None)
            extras.append({**decision["case"], "platform": "X", "author": "@" + tweet["author"]["screen_name"],
                           "sourceUrl": target, "date": datetime.datetime.fromtimestamp(tweet["created_timestamp"], datetime.timezone.utc).date().isoformat(),
                           "mediaKind": "video" if poster else "none", "poster": poster,
                           "discoveredVia": review["meta"]["sourceRepo"], "checkedAt": receipt["checkedAt"],
                           "evidenceUrl": upstream["original_post_url"],
                           "evidenceBasis": "Original post text and attached-media metadata read through FxTwitter. Author-reported workflow; video not independently watched or reproduced."})
        elif action == "related":
            patch.setdefault("relatedSources", []).append({"url": upstream["original_post_url"], "reason": decision["reason"],
                                                           "checkedAt": receipt["checkedAt"]})
            resource(patch, upstream["original_post_url"], "相关作品与后续记录", "Related work / follow-up")
        prompt = upstream.get("prompt")
        if prompt:
            evidence = {"sourcePostUrl": upstream["original_post_url"], "url": prompt["source_url"],
                        "kindReported": prompt["kind"], "sourceTypeReported": prompt["source"],
                        "curatorPage": prompt["page_url"], "completenessVerified": False,
                        "relationToCase": "related-post" if action == "related" else "primary-post"}
            pid = post_id(prompt["source_url"])
            if pid:
                prompt_tweet, prompt_receipt = read_post(pid)
                handle = prompt_tweet["author"]["screen_name"]
                evidence.update(checkedAt=prompt_receipt["checkedAt"], author=handle,
                                authorMatchesSourcePost=handle.lower() == tweet["author"]["screen_name"].lower(),
                                evidenceSha256=prompt_receipt["sha256"],
                                evidenceBasis="Public post text retrieved; upstream prompt classification retained, not a full-session verification.")
                if prompt["source"] == "image":
                    evidence["imageAttachmentPresent"] = any(x["type"] == "photo" for x in (prompt_tweet.get("media") or {}).get("all", []))
                    evidence["evidenceBasis"] = "Author reply and image attachment metadata checked; screenshot text not transcribed or independently verified."
            else:
                ext = external[prompt["source_url"]]
                if ext.get("status") != 200:
                    raise ValueError(f"External prompt evidence unavailable: {prompt['source_url']}")
                evidence.update(checkedAt=ext["checkedAt"], evidenceSha256=ext["sha256"],
                                evidenceBasis="Linked prompt / production page read; full run not reproduced.")
            patch.setdefault("promptEvidence", []).append(evidence)
            label = ("提示词截图（未转录）", "Prompt image (not transcribed)") if prompt["source"] == "image" else (
                ("关联帖提示词来源", "Related-post prompt source") if action == "related" else ("提示词来源", "Prompt source"))
            resource(patch, prompt["source_url"], *label)
        for url in upstream.get("resources", []):
            resource(patch, url, "来源附链", "Source resource")
    metadata = {"source": review["meta"]["sourceRepo"], "ref": manifest["ref"],
                "note": "Applied after deduplication; primary metrics only. Prompt completeness and project outcomes are not independently verified."}
    (DATA / "extra_gosail.json").write_text(json.dumps(extras, ensure_ascii=False, indent=2) + "\n")
    (DATA / "case_enrichments.json").write_text(json.dumps({"meta": metadata, "cases": list(patches.values())}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"added": len(extras), "enrichedTargets": len(patches),
                      "promptLinks": sum(len(p.get("promptEvidence", [])) for p in patches.values())}))


if __name__ == "__main__":
    main()
