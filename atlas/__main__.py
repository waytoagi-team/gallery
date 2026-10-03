"""Run with python -m atlas; topic scope is always explicit for mutations."""
import argparse
import json
from pathlib import Path
import sys

from .config import ROOT, load_topic, topics


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List configured topic IDs")
    listing.add_argument("--enabled", action="store_true")
    listing.add_argument("--json", action="store_true")
    for name in ("build", "validate"):
        command = commands.add_parser(name)
        scope = command.add_mutually_exclusive_group(required=True)
        scope.add_argument("--topic")
        scope.add_argument("--all", action="store_true")
        if name == "build":
            command.add_argument("--check", action="store_true", help="Offline check of committed public output")
            command.add_argument("--render-card", action="store_true", help="Force regenerating the share card")
    collect = commands.add_parser("collect", help="Fetch candidates and receipts; never import cases")
    collect.add_argument("--topic", required=True)
    collect.add_argument("--since")
    collect.add_argument("--only")
    collect.add_argument("--output-dir", type=Path)
    collect.add_argument("--report", type=Path)
    collect.add_argument("--dry-run", action="store_true")
    collect.add_argument("--workers", type=int, default=2)
    metrics = commands.add_parser("metrics")
    metrics.add_argument("--topic", required=True)
    metrics.add_argument("--only", choices=("github", "x"))
    metrics.add_argument("--github-kind", choices=("repository", "thread"))
    metrics.add_argument("--workers", type=int, default=2)
    metrics.add_argument("--output-dir", type=Path, required=True)
    base = commands.add_parser("fetch-base")
    base.add_argument("--topic", required=True)
    normalize = commands.add_parser("normalize-base", help="Write a candidate snapshot for editorial review")
    normalize.add_argument("--topic", required=True)
    normalize.add_argument("--raw", type=Path, required=True)
    normalize.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "list":
            selected = [t.id for t in topics() if not args.enabled or t.spec["monitor"]["enabled"]]
            print(json.dumps(selected) if args.json else "\n".join(selected))
            return 0
        if args.command in ("build", "validate"):
            from .build import build_topic
            from .validate import validate_public
            selected = topics() if args.all else [load_topic(args.topic)]
            for topic in selected:
                result = (build_topic(topic, check=args.check, render_card=args.render_card)
                          if args.command == "build" else validate_public(topic, topic.public))
                print(json.dumps(result, ensure_ascii=False))
            return 0
        topic = load_topic(args.topic)
        if args.command == "collect":
            from .collectors.discovery import run_discovery
            result, status = run_discovery(topic, since=args.since, only=args.only,
                output_dir=args.output_dir, report_path=args.report, dry_run=args.dry_run, workers=args.workers)
            print(json.dumps(result, ensure_ascii=False))
            return status
        if args.command == "metrics":
            from .metrics import main as refresh
            options = ["--output-dir", str(args.output_dir), "--workers", str(args.workers)]
            for flag, value in (("--only", args.only), ("--github-kind", args.github_kind)):
                if value:
                    options += [flag, value]
            return refresh(options, topic=topic)
        if args.command == "fetch-base":
            from .collectors.base import fetch_base
            result = fetch_base(topic)
        else:
            from .normalize import normalize_base
            args.output.parent.mkdir(parents=True, exist_ok=True)
            if args.output.resolve().is_relative_to(topic.data.resolve()) or args.output.resolve().is_relative_to(topic.public.resolve()):
                raise ValueError("Normalize to a candidate file outside accepted data/public; review before importing")
            result = normalize_base(topic, args.raw, args.output)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError) as error:
        print(f"atlas: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
