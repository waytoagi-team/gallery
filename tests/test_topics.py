import contextlib
import copy
import csv
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from atlas.build import merge_cases, render_page, build_topic
from atlas.collectors.discovery import discovery_url, run_discovery
from atlas.config import Topic, load_topic, read_topic
from atlas.share_card import ensure_card
from atlas.validate import validate_cases, validate_public


class TopicTests(unittest.TestCase):
    def test_rendering_topics_has_no_shared_mutable_context(self):
        opus, fable = load_topic("opus-5-5"), load_topic("fable-5-5")
        payload = merge_cases(fable)
        before = render_page(payload["meta"], [], opus)
        page = render_page(payload["meta"], [], fable)
        after = render_page(payload["meta"], [], opus)
        self.assertEqual(before, after)
        self.assertIn("Fable 5.5", page)
        self.assertIn(fable.page_url, page)
        self.assertNotIn("Opus", page)
        self.assertNotIn('data-guide-en=', page)
        self.assertNotIn("2026-09-22", page)
        self.assertNotIn("{{", page)

    def test_missing_base_source_can_build_an_empty_collection(self):
        with tempfile.TemporaryDirectory() as directory:
            original = load_topic("fable-5-5")
            topic = Topic(Path(directory), original.spec)
            topic.data.mkdir()
            payload = merge_cases(topic)
            self.assertEqual(payload["cases"], [])
            self.assertEqual(payload["meta"]["asOf"], "")
            self.assertEqual(payload["meta"]["count"], 0)
            self.assertNotIn("refreshedAt", payload["meta"])

    def test_explicit_ids_survive_reordering_extras(self):
        with tempfile.TemporaryDirectory() as directory:
            original = load_topic("fable-5-5")
            topic = Topic(Path(directory), original.spec)
            topic.data.mkdir()
            records = [{"id": "fable-project-b", "title": "B", "category": "coding", "platform": "GitHub", "sourceUrl": "https://github.com/a/b"},
                       {"id": "fable-project-a", "title": "A", "category": "coding", "platform": "GitHub", "sourceUrl": "https://github.com/a/a"}]
            path = topic.data / "extra_github.json"
            path.write_text(json.dumps(records))
            first = {c["sourceUrl"]: c["id"] for c in merge_cases(topic)["cases"]}
            path.write_text(json.dumps(list(reversed(records))))
            second = {c["sourceUrl"]: c["id"] for c in merge_cases(topic)["cases"]}
            self.assertEqual(first, second)

    def test_keyword_only_records_cannot_be_published_as_fable_cases(self):
        topic = load_topic("fable-5-5")
        payload = merge_cases(topic)
        case = {"id": "example", "category": "coding", "title": "Keyword hit", "sourceUrl": "https://example.com/project"}
        payload["cases"] = [case]
        payload["meta"]["count"] = 1
        with self.assertRaisesRegex(ValueError, "editorial evidence"):
            validate_cases(topic, payload)
        case.update(checkedAt="2026-10-03", evidenceUrl=case["sourceUrl"], evidenceBasis="The author states the exact model and task.",
                    modelAttribution={"topicId": topic.id, "basis": "explicit-source", "role": "implementation"})
        validate_cases(topic, payload)

    def test_topic_config_rejects_path_escape_and_duplicate_source_keys(self):
        original = load_topic("fable-5-5")
        with self.assertRaisesRegex(ValueError, "escapes"):
            original.content_path("../../.env")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "topic.json").write_text(json.dumps(original.spec))
            (path / "sources.json").write_text(json.dumps([original.sources[0], original.sources[0]]))
            with self.assertRaisesRegex(ValueError, "Duplicate source"):
                read_topic(path / "topic.json")

    def test_changed_title_invalidates_share_card_without_network(self):
        topic = load_topic("fable-5-5")
        spec = copy.deepcopy(topic.spec)
        spec["name"] = "Different Model"
        altered = Topic(topic.directory, spec)
        with self.assertRaisesRegex(ValueError, "stale"):
            ensure_card(altered, merge_cases(topic), check=True)


class DiscoveryTests(unittest.TestCase):
    def test_date_filters_are_platform_specific(self):
        from urllib.parse import parse_qs, urlsplit
        github = discovery_url({"url": 'https://api.github.com/search/repositories?q=%22fable5.5%22'}, "2026-10-01")
        self.assertIn("pushed:>=2026-10-01", parse_qs(urlsplit(github).query)["q"][0])
        hn = discovery_url({"url": 'https://hn.algolia.com/api/v1/search_by_date?query=fable'}, "2026-10-01")
        self.assertIn("numericFilters=created_at_i", hn)

    def test_dry_run_never_fetches_or_writes(self):
        with patch("atlas.collectors.discovery.collect") as fetch:
            summary, status = run_discovery(load_topic("fable-5-5"), dry_run=True)
        fetch.assert_not_called()
        self.assertEqual(status, 0)
        self.assertEqual(len(summary["sources"]), 6)

    def test_partial_failure_and_alias_duplicates_do_not_change_accepted_data(self):
        topic = load_topic("fable-5-5")
        baseline = (topic.data / "base_cases.json").read_bytes()
        freshness = (topic.data / "refresh_report.json").read_bytes()
        def fake_collect(source, directory, since):
            if source["key"].startswith("hn"):
                return {"key": source["key"], "url": source["url"], "ok": False, "status": 429}
            filename = source["key"] + ".txt"
            (directory / filename).write_text(json.dumps({"items": [{"html_url": "https://github.com/example/project", "full_name": "example/project"}]}))
            return {"key": source["key"], "url": source["url"], "ok": True, "file": filename}
        with tempfile.TemporaryDirectory() as directory, patch("atlas.collectors.discovery.collect", side_effect=fake_collect):
            summary, status = run_discovery(topic, output_dir=directory)
            report = json.loads((Path(directory) / "report.json").read_text())
            self.assertEqual(status, 1)
            self.assertEqual(summary["candidateCount"], 1)
            self.assertEqual(report["sourcesSucceeded"], 3)
            self.assertEqual(report["reviewedNewCases"], 0)
            self.assertEqual(report["coverage"], "partial")
            self.assertEqual(report["candidates"][0]["status"], "unreviewed")
            self.assertEqual(len(report["candidates"][0]["discoveredVia"]), 3)
            with self.assertRaisesRegex(ValueError, "not empty"):
                run_discovery(topic, output_dir=directory)
        self.assertEqual((topic.data / "base_cases.json").read_bytes(), baseline)
        self.assertEqual((topic.data / "refresh_report.json").read_bytes(), freshness)


if __name__ == "__main__":
    unittest.main()
