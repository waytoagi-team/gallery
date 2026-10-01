"""Read GitHub's API through the active GitHub CLI login.

Credentials stay with gh; only response bodies and public rate-limit metadata
are returned to the collectors.
"""
import email
import os
import re
import subprocess
import urllib.error
import urllib.parse


def response_metadata(status, headers):
    result = {"status": status, "transport": "gh"}
    limits = {name: headers[name] for name in
              ("x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset", "retry-after")
              if headers.get(name) is not None}
    if limits:
        result["rateLimit"] = limits
    return result


def read_github(url, timeout=30):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.netloc != "api.github.com":
        raise ValueError("GitHub authentication is restricted to https://api.github.com")
    env = dict(os.environ, GH_PROMPT_DISABLED="1")
    env.pop("GH_DEBUG", None)
    env.pop("GH_FORCE_TTY", None)
    try:
        result = subprocess.run(
            ["gh", "api", "--hostname", "github.com", "--method", "GET", "--include", url],
            capture_output=True, timeout=timeout, env=env)
    except FileNotFoundError:
        raise OSError("GitHub CLI is required: install gh and run gh auth login") from None
    except subprocess.TimeoutExpired:
        raise OSError("GitHub API request timed out") from None
    chunks = re.split(br"\r?\n\r?\n", result.stdout, maxsplit=1)
    match = re.match(br"HTTP/\S+ (\d{3})", chunks[0])
    if len(chunks) != 2 or not match:
        raise OSError("GitHub CLI request failed; check gh auth status and network connectivity")
    status = int(match[1])
    headers = email.message_from_bytes(chunks[0].split(b"\n", 1)[1])
    if status >= 400:
        raise urllib.error.HTTPError(url, status, "GitHub API request failed", headers, None)
    if result.returncode or not 200 <= status < 300:
        raise OSError("GitHub CLI returned an incomplete or unsuccessful response")
    return chunks[1], response_metadata(status, headers)
