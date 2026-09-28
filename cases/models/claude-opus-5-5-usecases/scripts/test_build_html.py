import unittest

from build_html import apply_enrichments, case_key, norm_url


class SourceIdentityTests(unittest.TestCase):
    def test_same_tweet_with_renamed_handle_and_video_suffix(self):
        a = {"sourceUrl": "https://twitter.com/old/status/123?utm_source=feed", "title": "First"}
        b = {"sourceUrl": "https://x.com/new/status/123/video/1", "title": "Retitled"}
        self.assertEqual(case_key(a), case_key(b))

    def test_same_reddit_post_with_different_slugs(self):
        self.assertEqual(norm_url("https://old.reddit.com/r/ClaudeAI/comments/abc123/old/"),
                         norm_url("https://www.reddit.com/r/ClaudeAI/comments/abc123/new/?utm_source=share"))

    def test_youtube_aliases_and_case_sensitive_ids(self):
        canonical = norm_url("https://youtube.com/watch?v=AbCdEfGh123&feature=share")
        self.assertEqual(canonical, norm_url("https://youtu.be/AbCdEfGh123?si=abc"))
        self.assertEqual(canonical, norm_url("https://youtube.com/shorts/AbCdEfGh123"))
        self.assertNotEqual(canonical, norm_url("https://youtube.com/watch?v=abcdefgh123"))

    def test_distinct_hn_comments_survive(self):
        self.assertNotEqual(norm_url("https://news.ycombinator.com/item?id=1"),
                            norm_url("https://news.ycombinator.com/item?id=2"))

    def test_multiple_customer_results_on_one_article_survive(self):
        a = {"sourceUrl": "https://example.com/launch", "title_en": "Customer A"}
        b = {"sourceUrl": a["sourceUrl"], "title_en": "Customer B"}
        self.assertNotEqual(case_key(a), case_key(b))

    def test_web_paths_remain_case_sensitive(self):
        self.assertNotEqual(norm_url("https://example.com/Case"), norm_url("https://example.com/case"))

    def test_repository_aliases(self):
        self.assertEqual(norm_url("https://github.com/Owner/Repo.git"),
                         norm_url("https://github.com/owner/repo/"))

    def test_bilibili_tracking_does_not_duplicate_video(self):
        self.assertEqual(norm_url("https://www.bilibili.com/video/BV123?spm_id_from=search"),
                         norm_url("https://www.bilibili.com/video/BV123/"))


class EnrichmentTests(unittest.TestCase):
    def test_survives_rebuild_and_unions_resources_without_duplicates(self):
        import copy
        original = [{"sourceUrl": "https://x.com/original/status/123", "title": "Original",
                     "resources": [{"url": "https://example.com/guide", "label": "Guide"}]}]
        patch = {"sourceUrl": "https://twitter.com/renamed/status/123/video/1", "resources": [
            {"url": "https://example.com/guide", "label": "Guide again"},
            {"url": "https://example.com/guide#prompt", "label": "Prompt"}]}
        first = apply_enrichments(copy.deepcopy(original), [patch])
        self.assertEqual(first, apply_enrichments(copy.deepcopy(original), [patch]))
        self.assertEqual(first, apply_enrichments(copy.deepcopy(first), [patch]))
        self.assertEqual(len(first[0]["resources"]), 2)
        self.assertEqual(first[0]["title"], "Original")

    def test_rejects_missing_targets_and_identity_changes(self):
        cases = [{"sourceUrl": "https://x.com/a/status/123"}]
        with self.assertRaises(ValueError):
            apply_enrichments(cases, [{"sourceUrl": "https://x.com/a/status/124"}])
        with self.assertRaises(ValueError):
            apply_enrichments(cases, [{"sourceUrl": cases[0]["sourceUrl"], "author": "Someone else"}])

    def test_older_metrics_cannot_replace_newer_values(self):
        case = {"sourceUrl": "https://x.com/a/status/123", "likes": 15, "metricsCheckedAt": "2026-09-28T14:00:00+00:00"}
        apply_enrichments([case], [{"sourceUrl": case["sourceUrl"], "likes": 10,
                                   "metricsCheckedAt": "2026-09-27T14:00:00+00:00"}])
        self.assertEqual(case["likes"], 15)


if __name__ == "__main__":
    unittest.main()
