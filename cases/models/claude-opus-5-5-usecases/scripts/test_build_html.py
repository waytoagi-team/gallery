import unittest

import json

from build_html import apply_enrichments, apply_poster_enrichments, boot_summary, case_key, compact_zh, fill_i18n, norm_url, page_poster, render_page, to_script


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


class PosterEnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.case = {"id": "web-001", "sourceUrl": "https://example.com/launch",
                     "title_en": "Experiment A", "poster": None, "mediaKind": "none", "likes": 42}
        self.patch = {"id": self.case["id"], "sourceUrl": self.case["sourceUrl"],
                      "title_en": self.case["title_en"], "poster": "https://example.com/result.png",
                      "mediaKind": "image", "posterEvidence": {
                          "reviewStatus": "accepted", "sourcePage": self.case["sourceUrl"],
                          "checkedAt": "2026-10-01T08:00:00+00:00", "method": "page-body-image",
                          "relation": "primary-page", "width": 800, "height": 600,
                          "imageSha256": "a" * 64}}

    def test_only_selected_experiment_on_shared_page_is_patched_and_rebuild_is_stable(self):
        import copy
        other = {**self.case, "id": "web-002", "title_en": "Experiment B"}
        cases = [copy.deepcopy(self.case), other]
        first = copy.deepcopy(apply_poster_enrichments(cases, [self.patch]))
        self.assertEqual(first, apply_poster_enrichments(cases, [self.patch]))
        self.assertEqual(first, apply_poster_enrichments([copy.deepcopy(self.case), other], [self.patch]))
        self.assertEqual(first[0]["likes"], 42)
        self.assertEqual(first[0]["poster"], self.patch["poster"])
        self.assertIsNone(first[1]["poster"])

    def test_existing_upstream_poster_and_its_evidence_win(self):
        self.case.update(poster="https://example.com/new.png", mediaKind="video", posterEvidence={"original": True})
        apply_poster_enrichments([self.case], [self.patch])
        self.assertEqual(self.case["poster"], "https://example.com/new.png")
        self.assertEqual(self.case["mediaKind"], "video")
        self.assertEqual(self.case["posterEvidence"], {"original": True})

    def test_rejects_reused_id_changed_editorial_title_missing_and_duplicate_targets(self):
        for change in ({"sourceUrl": "https://example.com/other"}, {"title_en": "Experiment B"}, {"id": "absent"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                apply_poster_enrichments([self.case], [{**self.patch, **change}])
        with self.assertRaises(ValueError):
            apply_poster_enrichments([self.case], [self.patch, self.patch])

    def test_rejects_unreviewed_media_and_unrelated_field_changes(self):
        for change in ({"poster": "javascript:alert(1)"}, {"mediaKind": "none"}, {"likes": 99},
                       {"posterEvidence": {**self.patch["posterEvidence"], "reviewStatus": "candidate"}},
                       {"posterEvidence": {**self.patch["posterEvidence"], "imageSha256": ""}}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                apply_poster_enrichments([self.case], [{**self.patch, **change}])


class PageBuildTests(unittest.TestCase):
    def test_github_payload_strips_legacy_stars_but_keeps_zero_thread_counts(self):
        import re
        meta = {"categories": {"coding": {"zh": "代码", "en": "Code"}}, "count": 1, "asOf": "2026-10-03"}
        c = {"id": "github-001", "source": "github", "platform": "GitHub", "category": "coding",
             "evidenceType": "集成", "title": "PR", "sourceUrl": "https://github.com/a/b/pull/1",
             "stars": 900000, "reactions": 0, "comments": 0,
             "metricsSourceUrl": "https://api.github.com/repos/a/b/issues/1"}
        page = render_page(meta, [c])
        payloads = re.findall(r'<script[^>]+type="application/json"[^>]*>(.*?)</script>', page, re.S)
        data = next(json.loads(p) for p in payloads if '"cases":' in p)
        row = data['cases'][0]
        self.assertNotIn('stars', row)
        self.assertEqual((row['githubKind'], row['reactions'], row['comments']), ('pull_request', 0, 0))
        self.assertNotIn('/*__RANKING__*/', page)

    def test_posters_request_card_sized_webp(self):
        self.assertEqual(page_poster("https://pbs.twimg.com/amplify_video_thumb/1/img/Ab-C.jpg"),
                         "https://pbs.twimg.com/amplify_video_thumb/1/img/Ab-C?format=webp&name=small")
        self.assertEqual(page_poster("https://pbs.twimg.com/media/Xyz?format=jpg&name=large"),
                         "https://pbs.twimg.com/media/Xyz?format=webp&name=small")
        self.assertEqual(page_poster("https://i0.hdslb.com/bfs/archive/a.jpg"), "https://i0.hdslb.com/bfs/archive/a.jpg@640w_360h_1c.webp")
        for untouched in ("https://i.ytimg.com/vi/abc/hqdefault.jpg", "https://preview.redd.it/a.jpeg?width=140",
                          "https://i0.hdslb.com/bfs/archive/a.jpg@320w.webp", None, ""):
            self.assertEqual(page_poster(untouched), untouched)

    def test_i18n_prefill_only_fills_empty_elements_and_escapes(self):
        markup = '<span data-i18n="a"></span><b class="sr" data-i18n="b">kept</b><p data-i18n="c"></p><i data-i18n="missing"></i>'
        out = fill_i18n(markup, {"a": "A & <B>", "b": "new", "c": "C"})
        self.assertIn('<span data-i18n="a">A &amp; &lt;B&gt;</span>', out)
        self.assertIn('<b class="sr" data-i18n="b">kept</b>', out)
        self.assertIn('<p data-i18n="c">C</p>', out)
        self.assertIn('<i data-i18n="missing"></i>', out)

    def test_boot_summary_counts_and_most_liked_order(self):
        meta = {"categories": {"games": {}, "web": {}}, "count": 4, "asOf": "2026-09-30",
                "refreshedAt": "2026-09-30T07:38:18+00:00", "refreshScope": {"zh": "范围", "en": "Scope"}}
        cases = [{"source": "x", "category": "games", "evidenceType": "演示", "title": "a", "sourceUrl": "u1", "likes": 5},
                 {"source": "x", "category": "web", "evidenceType": "限制", "title": "b", "sourceUrl": "u2", "likes": 9},
                 {"source": "reddit", "category": "games", "evidenceType": "演示", "title": "c", "sourceUrl": "u3", "likes": 9},
                 {"source": "github", "category": "web", "evidenceType": "集成", "title": "d", "sourceUrl": "u4", "stars": 99}]
        boot = boot_summary(meta, cases)
        self.assertEqual(boot["counts"]["src"], {"x": 2, "reddit": 1, "github": 1})
        self.assertEqual(boot["counts"]["ev"]["限制"], 1)
        self.assertEqual(boot["xLikes"], 14)
        self.assertEqual([t["title"] for t in boot["tops"]], ["b", "c", "a"])  # ties keep input order
        self.assertEqual(boot["info"]["refreshed"], {"zh": "2026-09-30 15:38 北京时间", "en": "2026-09-30 15:38 UTC+8"})
        self.assertEqual(boot["cube"], {"x|games|演示": 1, "x|web|限制": 1, "reddit|games|演示": 1, "github|web|集成": 1})

    def test_inline_json_cannot_close_or_comment_out_the_script(self):
        obj = {"title": "</script><!--<script>alert(1)</script>"}
        out = to_script(obj)
        self.assertNotIn("</", out)
        self.assertNotIn("<!--", out)
        self.assertEqual(json.loads(out), obj)

    def test_rendered_page_has_no_leftover_placeholders(self):
        meta = {"categories": {"games": {"zh": "游戏开发", "en": "Game Development"}}, "count": 1, "asOf": "2026-09-30"}
        cases = [{"id": "x-001", "source": "x", "platform": "X", "category": "games", "evidenceType": "演示", "title": "t",
                  "sourceUrl": "https://x.com/a/status/1", "likes": 3}]
        page = render_page(meta, cases)
        for marker in ("{{", "/*__", "<p class=\"tagline\" id=\"tagline\"></p>", "<div class=\"stats\" id=\"stats\"></div>"):
            self.assertNotIn(marker, page)
        self.assertIn('href="data/all_cases.csv"', page)
        self.assertRegex(page, r'og:image" content="https://www\.waytoagi\.com/usecase-atlas/opus5-5/assets/og-image\.png\?v=[0-9a-f]{10}"')
        self.assertIn('收录 1 条公开案例', page)  # og:image:alt filled from the same numbers as the card

    def test_guide_links_carry_both_editions(self):
        meta = {"categories": {"games": {"zh": "游戏开发", "en": "Game Development"}}, "count": 1, "asOf": "2026-09-30"}
        cases = [{"id": "x-001", "source": "x", "platform": "X", "category": "games", "evidenceType": "演示", "title": "t",
                  "sourceUrl": "https://x.com/a/status/1", "likes": 3}]
        page = render_page(meta, cases)
        # Chinese edition in the markup; the script swaps in the English edition in English mode
        self.assertEqual(page.count('href="blog/opus55-beginner-guide/" hreflang="zh-CN" data-guide-en="blog/opus55-beginner-guide/en/"'), 2)
        self.assertNotIn("(in Chinese)", page)

    def test_compact_zh_matches_intl_output(self):
        self.assertEqual(compact_zh(1142600), "114.3万")
        self.assertEqual(compact_zh(1000000), "100万")
        self.assertEqual(compact_zh(230000000), "2.3亿")
        self.assertEqual(compact_zh(9717), "9717")
        for n, text in ((1142500, "114.3万"), (114500, "11.5万"), (12500, "1.3万"), (99999999, "1亿"), (99994999, "9999.5万")):
            self.assertEqual(compact_zh(n), text)


if __name__ == "__main__":
    unittest.main()
