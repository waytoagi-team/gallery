import unittest
from atlas.github_metrics import github_target, github_response_metrics, sanitize_github_metrics


class GitHubMetricTests(unittest.TestCase):
    def test_url_scope_not_parent_repository_determines_metric(self):
        examples = {
            'https://www.github.com/A/B.git/?tab=readme': ('repository', 'https://api.github.com/repos/a/b'),
            'https://github.com/A/B/pull/12/files': ('pull_request', 'https://api.github.com/repos/a/b/issues/12'),
            'https://github.com/a/b/issues/7#issue-123': ('issue', 'https://api.github.com/repos/a/b/issues/7'),
            'https://github.com/a/b/pull/12#issuecomment-99': ('comment', None),
            'https://github.com/a/b/pull/12#discussion_r123': ('comment', None),
            'https://github.com/a/b/blob/main/demo.md': ('file', None),
            'https://github.com/a/b/tree/main/demo': ('file', None),
            'https://github.com/a/b/releases/tag/v1': ('other', None),
            'https://github.com/a/b/discussions/1': ('other', None),
            'https://gist.github.com/a/123': ('gist', None),
        }
        for url, (kind, api) in examples.items():
            with self.subTest(url=url):
                target = github_target(url)
                self.assertEqual((target['kind'], target.get('api')), (kind, api))
        self.assertIsNone(github_target('https://github.com.evil.test/a/b'))

    def test_response_identity_type_and_counts_must_match(self):
        pr = {'number': 12, 'html_url': 'https://github.com/a/b/pull/12',
              'pull_request': {'url': 'https://api.github.com/repos/a/b/pulls/12'},
              'reactions': {'total_count': 0}, 'comments': 5, 'stargazers_count': 900000}
        self.assertEqual(github_response_metrics(pr, 'github:a/b/pull/12'), {'reactions': 0, 'comments': 5})
        for bad in [{**pr, 'number': 13}, {**pr, 'html_url': 'https://github.com/a/other/pull/12'},
                    {**pr, 'pull_request': None}, {**pr, 'reactions': {'total_count': True}},
                    {**pr, 'comments': -1}, {**pr, 'reactions': {}}, {**pr, 'comments': None}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                github_response_metrics(bad, 'github:a/b/pull/12')
        self.assertEqual(github_response_metrics({'full_name': 'A/B', 'stargazers_count': 0}, 'github:a/b'), {'stars': 0})

    def test_reimport_cannot_restore_pr_stars_or_invent_metrics(self):
        row = {'sourceUrl': 'https://github.com/a/b/pull/12', 'stars': 900000, 'metricsCheckedAt': 'repo-time'}
        sanitize_github_metrics(row)
        self.assertNotIn('stars', row)
        self.assertNotIn('metricsCheckedAt', row)
        self.assertNotIn('reactions', row)
        row.update(stars=999999, reactions=0, comments=2, metricsCheckedAt='thread-time',
                   metricsSourceUrl='https://api.github.com/repos/a/b/issues/12')
        sanitize_github_metrics(row)
        self.assertNotIn('stars', row)
        self.assertEqual((row['reactions'], row['metricsCheckedAt']), (0, 'thread-time'))


if __name__ == '__main__':
    unittest.main()
