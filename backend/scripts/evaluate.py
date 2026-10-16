"""Run a set of research questions end to end and report what actually came back.

This is the manual-review harness from the simple implementation plan §11: it exercises
the real providers (no mocks) and prints the facts a reviewer needs to judge each run —
did it finish, how many sources, are the citations all pointing at real stored sources,
and does the answer contain any URL the model invented.

    python scripts/evaluate.py
    python scripts/evaluate.py --questions questions.txt
    python scripts/evaluate.py --csv results.csv
"""

import argparse
import asyncio
import csv
import os
import re
import sys
import time
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.database.database import Base, _get_engine, _get_session_factory  # noqa: E402
from app.database.models import (  # noqa: E402
    STATUS_COMPLETED,
    Report,
    ResearchActivity,
    ResearchSession,
    Source,
)
from app.services.research import ResearchService  # noqa: E402

DEFAULT_QUESTIONS = [
    "What are the main cybersecurity risks of generative AI?",
    "How does retrieval-augmented generation improve factual accuracy in LLMs?",
    "What is the evidence that spaced repetition improves long-term memory retention?",
    "How does climate change affect monsoon rainfall patterns in South Asia?",
    "What are the tradeoffs between REST and GraphQL for large web applications?",
    "Why did the Chernobyl disaster happen and what were its main consequences?",
    "What is the difference between machine learning and deep learning?",
    "How do vaccines train the immune system to recognise a virus?",
]


async def ensure_schema() -> None:
    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def run_one(question: str) -> dict:
    factory = _get_session_factory()
    started = time.perf_counter()

    async with factory() as db:
        session = ResearchSession(id=uuid4(), query=question, status="queued")
        db.add(session)
        await db.commit()
        session_id = session.id

    async with factory() as db:
        await ResearchService(db).run(session_id)

    elapsed = time.perf_counter() - started

    async with factory() as db:
        session = await db.get(ResearchSession, session_id)
        sources = (
            await db.execute(
                select(Source).where(Source.session_id == session_id)
            )
        ).scalars().all()
        report = (
            await db.execute(select(Report).where(Report.session_id == session_id))
        ).scalar_one_or_none()
        activity = (
            await db.execute(
                select(ResearchActivity)
                .where(ResearchActivity.session_id == session_id)
                .order_by(ResearchActivity.id.asc())
            )
        ).scalars().all()

        markdown = report.answer_markdown if report else ""
        stored_urls = {s.url for s in sources}

        # Every citation in the body must point at a real stored source.
        body = markdown.split("## References")[0]
        citations = {int(n) for n in re.findall(r"\[(\d{1,3})\]", body)}
        dangling = sorted(n for n in citations if n < 1 or n > len(sources))

        # Any URL the model wrote itself, outside the backend-built reference list.
        references = markdown.split("## References")[-1] if "## References" in markdown else ""
        model_urls = set(re.findall(r"https?://[^\s)\]]+", body))
        invented = model_urls - stored_urls

        return {
            "question": question,
            "status": session.status,
            "error": session.error_message or "",
            "sources": len(sources),
            "full_pages": sum(1 for s in sources if s.retrieval_method == "firecrawl"),
            "citations": len(citations),
            "dangling_citations": ",".join(map(str, dangling)),
            "invented_urls": ",".join(sorted(invented)),
            "answer_chars": len(markdown),
            "stages": len(activity),
            "seconds": round(elapsed, 1),
        }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, help="file with one question per line")
    parser.add_argument("--csv", type=Path, help="write results to this CSV")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    settings = get_settings()
    missing = settings.missing_required_keys()
    if missing:
        print(f"Cannot run: missing configuration for {', '.join(missing)}", file=sys.stderr)
        return 2

    questions = DEFAULT_QUESTIONS
    if args.questions:
        questions = [
            line.strip()
            for line in args.questions.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
    if args.limit:
        questions = questions[: args.limit]

    print(f"Database: {settings.DATABASE_URL.split('@')[-1].split('/')[0]}")
    print(f"Model:    {settings.GROQ_MODEL}")
    print(f"Running {len(questions)} question(s) against live providers...\n")

    await ensure_schema()

    rows = []
    for index, question in enumerate(questions, start=1):
        try:
            row = await run_one(question)
        except Exception as exc:  # noqa: BLE001 - report and continue
            row = {
                "question": question,
                "status": "harness-error",
                "error": f"{type(exc).__name__}: {exc}"[:200],
                "sources": 0, "full_pages": 0, "citations": 0,
                "dangling_citations": "", "invented_urls": "",
                "answer_chars": 0, "stages": 0, "seconds": 0,
            }
        rows.append(row)

        flag = "ok " if row["status"] == STATUS_COMPLETED else "FAIL"
        print(
            f"[{index}/{len(questions)}] {flag} {row['seconds']:>5}s "
            f"sources={row['sources']} (pages={row['full_pages']}) "
            f"cites={row['citations']} chars={row['answer_chars']}  {row['question'][:60]}"
        )
        if row["error"]:
            print(f"        error: {row['error']}")
        if row["dangling_citations"]:
            print(f"        !! dangling citations: {row['dangling_citations']}")
        if row["invented_urls"]:
            print(f"        !! URLs not in stored sources: {row['invented_urls']}")

    completed = sum(1 for r in rows if r["status"] == STATUS_COMPLETED)
    bad_cites = sum(1 for r in rows if r["dangling_citations"])
    invented = sum(1 for r in rows if r["invented_urls"])

    print("\n--- summary ---")
    print(f"completed        : {completed}/{len(rows)}")
    print(f"dangling citations: {bad_cites}")
    print(f"invented URLs     : {invented}")
    print(f"avg seconds       : {round(sum(r['seconds'] for r in rows) / len(rows), 1)}")
    print(f"avg sources       : {round(sum(r['sources'] for r in rows) / len(rows), 1)}")

    if args.csv:
        with args.csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nwrote {args.csv}")

    return 0 if completed == len(rows) and bad_cites == 0 and invented == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
