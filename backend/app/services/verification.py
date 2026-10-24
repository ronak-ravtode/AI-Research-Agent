"""Verifier agent — remove claims the retrieved sources do not support.

The writer is instructed to cite every claim, but instructions are not proof. This second
agent reads the finished draft against the same numbered source material and returns a
revised body with unsupported claims removed or qualified.

It is fail-open on purpose: verification improves a report, but an unavailable verifier
must not throw away a usable answer. The original draft survives every failure path.
"""

from dataclasses import dataclass

from app.core.logging import logger
from app.services.extraction import RetrievedSource
from app.services.llm import llm_service
from app.services.report import build_source_material

SYSTEM_PROMPT = (
    "You verify a research answer against the numbered sources it cites.\n"
    "Reply with JSON only:\n"
    '{"supported": true|false, "revised_body": "...", "removed_claims": 0, '
    '"note": "..."}\n'
    "Rules:\n"
    "- Check the factual claims in the draft against the provided sources.\n"
    "- If every claim is supported, set supported=true and return revised_body as an "
    "empty string.\n"
    "- Otherwise set supported=false and return the full revised Markdown body with "
    "unsupported claims removed or explicitly qualified.\n"
    "- Preserve supported wording and structure. Keep existing [n] citations on claims "
    "that remain. Never add new facts, citations, URLs, or a reference list.\n"
    "- Do not use raw HTML. Keep the note to one sentence."
)


@dataclass
class VerificationResult:
    body: str
    revised: bool
    removed_claims: int = 0
    note: str = ""


def _as_int(value) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return 0


class VerificationService:
    async def verify(
        self,
        question: str,
        body: str,
        sources: list[RetrievedSource],
    ) -> VerificationResult:
        """Return a checked body, or the original if checking is not possible."""
        if not body.strip() or not sources:
            return VerificationResult(
                body=body,
                revised=False,
                note="Verification skipped: no draft or no sources.",
            )

        material = build_source_material(sources)
        if not material.strip():
            return VerificationResult(
                body=body,
                revised=False,
                note="Verification skipped: no readable source material.",
            )

        prompt = (
            f"Research question:\n{question}\n\n"
            f"Draft answer to verify:\n\n{body}\n\n"
            f"Numbered source material:\n\n{material}"
        )

        try:
            payload = await llm_service.structured_generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.1,
                max_tokens=4096,
            )
        except Exception as exc:
            logger.warning(
                "Verification failed, keeping the draft",
                data={"error": type(exc).__name__},
            )
            return VerificationResult(
                body=body,
                revised=False,
                note="Verification unavailable; the draft was kept.",
            )

        if not isinstance(payload, dict) or not isinstance(
            payload.get("supported"), bool
        ):
            logger.warning("Verification returned an unusable payload")
            return VerificationResult(
                body=body,
                revised=False,
                note="Verification returned no usable result; the draft was kept.",
            )

        note = " ".join(str(payload.get("note") or "").split()).strip()

        if payload["supported"]:
            return VerificationResult(
                body=body,
                revised=False,
                note=note or "All checked claims are supported by the retrieved sources.",
            )

        revised_body = str(payload.get("revised_body") or "").strip()
        if not revised_body:
            return VerificationResult(
                body=body,
                revised=False,
                note=note or "Verification proposed no usable revision; the draft was kept.",
            )

        return VerificationResult(
            body=revised_body,
            revised=revised_body != body.strip(),
            removed_claims=_as_int(payload.get("removed_claims")),
            note=note or "Unsupported claims were removed or qualified.",
        )


verification_service = VerificationService()
