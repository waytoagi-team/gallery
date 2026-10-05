"""Classify GitHub evidence and keep metrics attached to the actual linked object."""
import re
from urllib.parse import urlsplit


def github_target(url):
    parts = urlsplit(url or "")
    host = (parts.hostname or "").lower().removeprefix("www.")
    if host == "gist.github.com":
        return {"kind": "gist"}
    if host != "github.com" or parts.scheme not in ("http", "https"):
        return None
    path = parts.path.strip("/").split("/")
    if len(path) < 2 or not all(re.fullmatch(r"[\w.-]+", p) for p in path[:2]):
        return {"kind": "other"}
    repo = "/".join(path[:2]).lower().removesuffix(".git")
    target = {"kind": "other", "repo": repo}
    if len(path) == 2:
        target.update(kind="repository", key="github:" + repo,
                      api="https://api.github.com/repos/" + repo)
    elif path[2] in ("blob", "tree"):
        target["kind"] = "file"
    elif (len(path) >= 4 and path[2] in ("pull", "issues") and path[3].isdigit()
          and (len(path) == 4 or path[2] == "pull" and path[4:] in (["files"], ["commits"]))):
        # A link to a particular comment/review is not the whole PR/issue.
        if re.match(r"(?:issuecomment-|discussion_r|pullrequestreview-)", parts.fragment):
            target["kind"] = "comment"
        else:
            target.update(kind="pull_request" if path[2] == "pull" else "issue",
                          number=int(path[3]), key=f"github:{repo}/{path[2]}/{int(path[3])}",
                          api=f"https://api.github.com/repos/{repo}/issues/{int(path[3])}")
    return target


def sanitize_github_metrics(case):
    """Prevent old imports or failed refreshes from resurrecting repository stars on a PR.

    An object's previous metrics survive failures only with matching API provenance.
    Unknown counts stay unknown; they are never manufactured as zeros.
    """
    target = github_target(case.get("sourceUrl"))
    if not target:
        return case
    case["githubKind"] = target["kind"]
    if target["kind"] == "repository":
        case.pop("reactions", None)
        case.pop("comments", None)
    else:
        case.pop("stars", None)
        if not target.get("api") or case.get("metricsSourceUrl") != target["api"]:
            for field in ("reactions", "comments", "metricsCheckedAt", "metricsSourceUrl"):
                case.pop(field, None)
    return case


def github_response_metrics(value, key):
    """Validate object identity before accepting the count from GitHub's response."""
    if not isinstance(value, dict):
        raise ValueError("GitHub response must be an object")
    identity = key.removeprefix("github:").split("/")
    repo = "/".join(identity[:2])
    if len(identity) == 2:
        if value.get("full_name", "").lower() != repo:
            raise ValueError("Missing or mismatched repository identity")
        metrics = {"stars": value.get("stargazers_count")}
    else:
        kind, number = identity[2], int(identity[3])
        returned = github_target(value.get("html_url", "")) or {}
        if (returned.get("repo") != repo or returned.get("number") != number
                or returned.get("kind") != ("pull_request" if kind == "pull" else "issue")
                or value.get("number") != number
                or bool(value.get("pull_request")) != (kind == "pull")):
            raise ValueError("Missing or mismatched issue/PR identity")
        reactions = value.get("reactions")
        metrics = {"reactions": reactions.get("total_count") if isinstance(reactions, dict) else None,
                   "comments": value.get("comments")}
    if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in metrics.values()):
        raise ValueError("Invalid or missing GitHub metric count")
    return metrics
