"""Validated, explicit topic context; no process-wide current-topic state."""
from dataclasses import dataclass
import datetime
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "atlas" / "templates"


@dataclass(frozen=True)
class Topic:
    directory: Path
    spec: dict

    @property
    def id(self):
        return self.spec["id"]

    @property
    def data(self):
        return self.directory / "data"

    @property
    def public(self):
        return self.directory / "public"

    @property
    def content(self):
        return self.directory / "content"

    @property
    def page_url(self):
        return "https://www.waytoagi.com" + self.spec["publicPath"]

    @property
    def repo_url(self):
        return "https://github.com/waytoagi-team/gallery/tree/main/cases/models/" + self.directory.name

    @property
    def sources(self):
        entries = json.loads((self.directory / "sources.json").read_text())
        keys = [s["key"] for s in entries]
        if len(keys) != len(set(keys)):
            raise ValueError(f"Duplicate source keys: {self.id}")
        for source in entries:
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", source["key"]):
                raise ValueError("Source keys must be safe filenames")
            url = urlsplit(source["url"])
            if url.scheme != "https" or not url.hostname or url.username or url.password:
                raise ValueError("Discovery URLs must be public HTTPS URLs without credentials")
            if source["format"] not in ("json", "xml", "text"):
                raise ValueError("Unknown source format")
        return entries

    def content_path(self, relative):
        path = (self.content / relative).resolve()
        if not path.is_relative_to(self.content.resolve()):
            raise ValueError("Content path escapes topic directory")
        return path


def read_topic(path):
    spec = json.loads(path.read_text())
    if spec.get("schemaVersion") != 1:
        raise ValueError(f"Unsupported topic schema: {path}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", spec.get("id", "")):
        raise ValueError("Topic ID must be a stable lowercase slug")
    for field in ("name", "shortName"):
        if not isinstance(spec.get(field), str) or not spec[field].strip():
            raise ValueError(f"Missing {field}: {path}")
    if not re.fullmatch(r"/usecase-atlas/[a-z0-9-]+/", spec.get("publicPath", "")):
        raise ValueError("Topic must have its own usecase-atlas path")
    if spec.get("releasedAt"):
        datetime.date.fromisoformat(spec["releasedAt"])
    if not isinstance(spec.get("aliases"), list) or not spec["aliases"]:
        raise ValueError("A topic needs discovery aliases")
    if not isinstance(spec.get("monitor", {}).get("enabled"), bool):
        raise ValueError("monitor.enabled must be boolean")
    topic = Topic(path.parent, spec)
    topic.sources
    guide = spec.get("guide")
    if guide:
        for lang in ("zh", "en"):
            relative = guide[lang]
            if not relative.endswith("/") or not (topic.content_path(relative) / "index.html").is_file():
                raise ValueError(f"Missing {lang} guide for {topic.id}")
    return topic


def topics(root=ROOT):
    result = [read_topic(p) for p in sorted((root / "cases" / "models").glob("*/topic.json"))]
    for field in ("id", "publicPath"):
        values = [t.spec[field] for t in result]
        if len(values) != len(set(values)):
            raise ValueError(f"Duplicate topic {field}")
    return result


def load_topic(topic_id="opus-5-5", root=ROOT):
    for topic in topics(root):
        if topic.id == topic_id:
            return topic
    raise ValueError(f"Unknown topic: {topic_id}")
