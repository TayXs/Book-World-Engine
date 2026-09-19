"""Command line: check one link, print the result, optionally speak it."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from .config import get_settings
from .ingest.errors import IngestError
from .llm import LLMError
from .models import Digest, JobState
from .pipeline import run as run_pipeline
from .tts import TTSError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="truthcast",
        description="Check what a video or podcast claims, and keep only what holds up.",
    )
    parser.add_argument("url", help="YouTube link, podcast RSS feed, or audio file URL")
    parser.add_argument(
        "-i", "--interest", action="append", default=[],
        help="A topic you care about; repeat for more. Facts are ranked against these.",
    )
    parser.add_argument("--speak", action="store_true", help="Also render an MP3.")
    parser.add_argument("--json", action="store_true", help="Print the digest as JSON.")
    parser.add_argument("--script", action="store_true", help="Print only the audio script.")
    parser.add_argument("-q", "--quiet", action="store_true", help="No progress output.")
    return parser


async def _run(args: argparse.Namespace) -> int:
    settings = get_settings()

    async def on_progress(state: JobState, message: str, progress: float) -> None:
        if not args.quiet:
            print(f"  [{progress:>5.0%}] {message}", file=sys.stderr, flush=True)

    try:
        digest, audio_path = await run_pipeline(
            args.url,
            interests=args.interest,
            speak=args.speak,
            on_progress=None if args.quiet else on_progress,
            settings=settings,
        )
    except (IngestError, LLMError, TTSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(json.loads(digest.model_dump_json()), indent=2))
    elif args.script:
        print(digest.audio_script)
    else:
        print(render(digest))

    if audio_path:
        print(f"\nAudio: {audio_path}", file=sys.stderr)
    return 0


def render(digest: Digest) -> str:
    lines = [
        "",
        digest.source.title,
        "=" * min(len(digest.source.title), 72),
        "",
        digest.intro,
        "",
    ]

    if digest.facts:
        lines.append("WHAT CHECKED OUT")
        lines.append("")
        for fact in digest.facts:
            lines.extend(_render_fact(fact))

    if digest.corrections:
        lines.append("WHAT DIDN'T HOLD UP")
        lines.append("")
        for fact in digest.corrections:
            lines.extend(_render_fact(fact))

    lines.append(
        f"Checked {digest.claims_examined} claims, kept "
        f"{len(digest.facts) + len(digest.corrections)}, dropped {digest.claims_dropped}."
    )
    for reason, count in sorted(digest.dropped_reasons.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {count} x {reason}")
    lines.append(f"Reading level: grade {digest.reading_grade}")
    return "\n".join(lines)


def _render_fact(fact) -> list[str]:
    marker = "!" if fact.kind == "correction" else "*"
    stamp = f"  [{fact.said_at}]" if fact.said_at else ""
    lines = [f"{marker} {fact.headline}{stamp}", f"  {fact.explanation}"]
    if fact.real_world_link:
        lines.append(f"  Why it matters: {fact.real_world_link}")
    for source in fact.sources[:3]:
        lines.append(f"  - {source.domain}  {source.url}")
    lines.append("")
    return lines


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    raise SystemExit(asyncio.run(_run(build_parser().parse_args())))


def serve() -> None:
    """`truthcast-serve` - the web app on http://127.0.0.1:8000"""
    import uvicorn

    parser = argparse.ArgumentParser(prog="truthcast-serve", description="Run the web app.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run("truthcast.api:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
