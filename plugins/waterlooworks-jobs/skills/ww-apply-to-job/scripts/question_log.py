#!/usr/bin/env python3
"""Record and inspect user input questions for WaterlooWorks applications."""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_LOG_FILE = ".codex_user_input_log.jsonl"
DEFAULT_SKILL = "ww-apply-to-job"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_log_path(args: argparse.Namespace) -> Path:
    base = Path(args.cwd).expanduser() if args.cwd else Path.cwd()
    log_file = Path(args.log_file).expanduser()
    return log_file if log_file.is_absolute() else base / log_file


def parse_context(pairs: list[str]) -> dict[str, str]:
    context: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"context must be key=value, got: {pair}")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise SystemExit(f"context key cannot be empty: {pair}")
        context[key] = value
    return context


def load_entries(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    entries: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                entry = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{path}:{line_number}: invalid JSONL entry: {exc}") from exc
            if not isinstance(entry, dict):
                raise SystemExit(f"{path}:{line_number}: entry must be a JSON object")
            entries.append(entry)
    return entries


def cmd_add(args: argparse.Namespace) -> int:
    path = resolve_log_path(args)
    now = utc_now()
    entry = {
        "id": str(uuid.uuid4()),
        "created_at": now,
        "updated_at": now,
        "skill": args.skill,
        "job_id": args.job_id,
        "question": args.question,
        "answer": args.answer,
        "context": parse_context(args.context),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"status": "added", "path": str(path), "entry": entry}, ensure_ascii=False))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    path = resolve_log_path(args)
    entries = load_entries(path)
    if args.json:
        print(json.dumps({"path": str(path), "entries": entries}, ensure_ascii=False, indent=2))
        return 0

    print(f"path: {path}")
    if not entries:
        print("(no entries)")
        return 0

    for index, entry in enumerate(entries, start=1):
        context = entry.get("context")
        context_text = ""
        if isinstance(context, dict) and context:
            context_text = " " + " ".join(f"{key}={value}" for key, value in sorted(context.items()))
        print(f"{index}. id={entry.get('id')} job_id={entry.get('job_id')} skill={entry.get('skill')}{context_text}")
        print(f"   Q: {entry.get('question')}")
        print(f"   A: {entry.get('answer')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Record user input questions and answers in the current working directory.")
    parser.add_argument("--cwd", help="Directory where the log file should live. Defaults to the current working directory.")
    parser.add_argument("--log-file", default=DEFAULT_LOG_FILE, help=f"Log file path, relative to --cwd unless absolute. Default: {DEFAULT_LOG_FILE}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    add = subparsers.add_parser("add", help="Append a new question/answer entry.")
    add.add_argument("--question", required=True, help="Exact question asked to the user.")
    add.add_argument("--answer", required=True, help="Exact answer received from the user.")
    add.add_argument("--job-id", help="WaterlooWorks job ID related to the question.")
    add.add_argument("--skill", default=DEFAULT_SKILL, help=f"Skill name. Default: {DEFAULT_SKILL}")
    add.add_argument("--context", action="append", default=[], help="Additional metadata as key=value. May be repeated.")
    add.set_defaults(func=cmd_add)

    list_cmd = subparsers.add_parser("list", help="List recorded questions and answers.")
    list_cmd.add_argument("--json", action="store_true", help="Print JSON instead of a readable list.")
    list_cmd.set_defaults(func=cmd_list)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
