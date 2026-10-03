import contextlib
import io
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

import github_api
import refresh_metrics


class GitHubTransportTests(unittest.TestCase):
    def test_delegates_credentials_and_get_to_gh(self):
        response = subprocess.CompletedProcess([], 0, stdout=(
            b'HTTP/2.0 200 OK\r\nX-Ratelimit-Remaining: 4999\r\n\r\n{"stargazers_count": 7}'), stderr=b'')
        with patch.dict(os.environ, {"GH_DEBUG": "api"}), \
                patch("github_api.subprocess.run", return_value=response) as run:
            body, metadata = github_api.read_github("https://api.github.com/repos/a/b")
        self.assertEqual(json.loads(body), {"stargazers_count": 7})
        self.assertEqual(metadata["rateLimit"]["x-ratelimit-remaining"], "4999")
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--method") + 1], "GET")
        self.assertNotIn("GH_DEBUG", run.call_args.kwargs["env"])
        self.assertNotIn("Authorization", " ".join(command))

    def test_rejects_other_hosts_before_invoking_gh(self):
        with patch("github_api.subprocess.run") as run:
            for url in ("http://api.github.com/repos/a/b", "https://api.github.com.evil.test/",
                        "https://api.github.com@evil.test/", "https://x.com/"):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    github_api.read_github(url)
            run.assert_not_called()

    def test_error_retains_status_and_rate_limit_without_cli_diagnostics(self):
        response = subprocess.CompletedProcess([], 1, stdout=(
            b'HTTP/2.0 403 Forbidden\nX-Ratelimit-Remaining: 0\nRetry-After: 60\n\n{}'),
            stderr=b'private diagnostic must not enter receipts')
        with patch("github_api.subprocess.run", return_value=response):
            receipt = refresh_metrics.fetch(("github:a/b", "https://api.github.com/repos/a/b"))
        self.assertFalse(receipt["ok"])
        self.assertEqual(receipt["status"], 403)
        self.assertEqual(receipt["rateLimit"]["retry-after"], "60")
        self.assertNotIn("private diagnostic", json.dumps(receipt))

    def test_missing_login_does_not_fall_back_to_anonymous_requests(self):
        response = subprocess.CompletedProcess([], 4, stdout=b'', stderr=b'login required')
        with patch("github_api.subprocess.run", return_value=response), \
                patch("urllib.request.urlopen") as anonymous:
            with self.assertRaisesRegex(OSError, "gh auth status"):
                github_api.read_github("https://api.github.com/repos/a/b")
            anonymous.assert_not_called()


class GitHubRefreshTests(unittest.TestCase):
    def test_github_only_preserves_x_and_keeps_stars_on_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            data = pathlib.Path(directory)
            cases = [{"sourceUrl": "https://github.com/a/good", "stars": 1},
                     {"sourceUrl": "https://github.com/a/unavailable", "stars": 9},
                     {"sourceUrl": "https://x.com/a/status/123", "likes": 10}]
            (data / "all_cases.json").write_text(json.dumps({"cases": cases}))
            (data / "extra_github.json").write_text(json.dumps(cases[:2]))
            x_patch = '{"meta": {"refreshedAt": "old"}, "cases": []}\n'
            (data / "metric_refreshes.json").write_text(x_patch)

            def mock_fetch(job):
                key, url = job
                self.assertTrue(key.startswith("github:"))
                return {"key": key, "url": url, "ok": key == "github:a/good",
                        "metrics": {"stars": 12}, "checkedAt": "2026-10-01T04:00:00+00:00"}

            with patch.object(refresh_metrics, "DATA", data), \
                    patch.object(refresh_metrics, "fetch", side_effect=mock_fetch), \
                    patch("sys.argv", ["refresh_metrics", "--only", "github", "--output-dir", str(data / "receipts")]), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(refresh_metrics.main(), 1)
            refreshed = json.loads((data / "extra_github.json").read_text())
            self.assertEqual([row["stars"] for row in refreshed], [12, 9])
            self.assertEqual((data / "metric_refreshes.json").read_text(), x_patch)

    def test_pr_issue_and_file_never_fetch_parent_stars_or_retain_bad_fallbacks(self):
        with tempfile.TemporaryDirectory() as directory:
            data = pathlib.Path(directory)
            cases = [{"sourceUrl": "https://github.com/a/b/pull/1", "stars": 900000},
                     {"sourceUrl": "https://github.com/a/b/issues/2", "stars": 900000,
                      "reactions": 3, "comments": 4, "metricsCheckedAt": "old",
                      "metricsSourceUrl": "https://api.github.com/repos/a/b/issues/2"},
                     {"sourceUrl": "https://github.com/a/b/issues/3", "stars": 900000,
                      "metricsCheckedAt": "incorrect-repo-time"},
                     {"sourceUrl": "https://github.com/a/b/blob/main/file.md", "stars": 900000}]
            (data / "all_cases.json").write_text(json.dumps({"cases": cases}))
            (data / "extra_github.json").write_text(json.dumps(cases))
            jobs = []

            def fetch(job):
                jobs.append(job)
                return {"key": job[0], "url": job[1], "ok": job[0].endswith('/pull/1'),
                        "metrics": {"reactions": 0, "comments": 5}, "checkedAt": "new"}

            with patch.object(refresh_metrics, "DATA", data), patch.object(refresh_metrics, "fetch", side_effect=fetch), \
                    patch("sys.argv", ["refresh_metrics", "--only", "github", "--output-dir", str(data / "receipts")]), \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(refresh_metrics.main(), 1)
            self.assertEqual(set(jobs), {("github:a/b/pull/1", "https://api.github.com/repos/a/b/issues/1"),
                                        ("github:a/b/issues/2", "https://api.github.com/repos/a/b/issues/2"),
                                        ("github:a/b/issues/3", "https://api.github.com/repos/a/b/issues/3")})
            rows = json.loads((data / "extra_github.json").read_text())
            self.assertTrue(all('stars' not in r for r in rows))
            self.assertEqual((rows[0]['reactions'], rows[0]['comments']), (0, 5))
            self.assertEqual((rows[1]['reactions'], rows[1]['metricsCheckedAt']), (3, 'old'))
            self.assertNotIn('reactions', rows[2])
            self.assertNotIn('metricsCheckedAt', rows[2])


if __name__ == "__main__":
    unittest.main()
