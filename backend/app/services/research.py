from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import (
    ResearchSession, ResearchTask, Source, Evidence,
    Citation, Report, AgentLog,
)
from app.agents.graph import create_research_graph
from app.services.citations import map_citations
from app.services.confidence import calculate_confidence
from app.agents.state import ResearchState
from app.core.logging import logger


class ResearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_research(self, query: str, depth: str = "standard", research_id=None) -> str:
        if research_id is None:
            research_id = uuid4()
        else:
            from uuid import UUID
            research_id = UUID(research_id) if not isinstance(research_id, UUID) else research_id

        # Fetch existing session (created by API endpoint) or create new one
        result = await self.db.execute(
            select(ResearchSession).where(ResearchSession.id == research_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            session = ResearchSession(
                id=research_id,
                query=query,
                research_depth=depth,
                status="planning",
                started_at=datetime.now(timezone.utc),
            )
            self.db.add(session)
            await self.db.flush()

        state = ResearchState(
            research_id=str(research_id),
            user_query=query,
            research_plan=[],
            current_task="",
            completed_tasks=[],
            search_queries=[],
            sources=[],
            evidence=[],
            verified_claims=[],
            conflicts=[],
            analysis="",
            citations=[],
            confidence_scores={},
            report={},
            iteration=0,
            status="planning",
            errors=[],
            research_depth=depth,
        )

        try:
            graph = create_research_graph()
            final_state = await graph.ainvoke(state)

            task_ids = {}
            for i, subtask in enumerate(final_state.get("research_plan", [])):
                task_id = uuid4()
                task_ids[subtask.get("id")] = task_id
                db_task = ResearchTask(
                    id=task_id,
                    session_id=research_id,
                    task_number=i + 1,
                    title=subtask.get("task", ""),
                    description=subtask.get("task", ""),
                    status="completed",
                    completed_at=datetime.now(timezone.utc),
                )
                self.db.add(db_task)

            source_id_map = {}
            for src in final_state.get("sources", []):
                source_db_id = uuid4()
                source_url = src.get("url", "")
                source_str_id = src.get("id", "")
                source_id_map[source_url] = source_db_id
                if source_str_id:
                    source_id_map[source_str_id] = source_db_id
                db_source = Source(
                    id=source_db_id,
                    session_id=research_id,
                    title=src.get("title", ""),
                    url=source_url,
                    domain=src.get("domain"),
                    source_type=src.get("source_type", "unknown"),
                    search_query=src.get("search_query"),
                    content=src.get("content"),
                    relevance_score=src.get("relevance_score", 0.0),
                    reliability_score=src.get("reliability_score", 0.0),
                    retrieved_at=datetime.now(timezone.utc),
                )
                self.db.add(db_source)

            evidence_db_ids = {}
            for ev in final_state.get("evidence", []):
                source_url = ev.get("source_url", "")
                source_db_id = source_id_map.get(source_url)
                if not source_db_id:
                    continue

                task_key = ev.get("task_id")
                task_db_id = task_ids.get(task_key) if task_key else list(task_ids.values())[0] if task_ids else uuid4()

                evidence_db_id = uuid4()
                db_evidence = Evidence(
                    id=evidence_db_id,
                    session_id=research_id,
                    task_id=task_db_id,
                    source_id=source_db_id,
                    claim=ev.get("claim", ""),
                    evidence_text=ev.get("evidence_text", ""),
                    evidence_type=ev.get("evidence_type", "factual"),
                    confidence_score=ev.get("confidence_score", 0.5),
                )
                self.db.add(db_evidence)
                evidence_db_ids[ev.get("claim", "")] = evidence_db_id

            citations = map_citations(
                final_state.get("verified_claims", []),
                final_state.get("sources", []),
            )

            for citation in citations:
                source_url = citation.get("source_url", "")
                source_db_id = source_id_map.get(source_url)
                if not source_db_id:
                    continue

                claim_text = citation.get("claim", "")
                evidence_db_id = evidence_db_ids.get(claim_text)

                if not evidence_db_id:
                    evidence_db_id = uuid4()
                    db_evidence = Evidence(
                        id=evidence_db_id,
                        session_id=research_id,
                        task_id=list(task_ids.values())[0] if task_ids else uuid4(),
                        source_id=source_db_id,
                        claim=claim_text,
                        evidence_text="",
                        evidence_type="factual",
                    )
                    self.db.add(db_evidence)

                db_citation = Citation(
                    session_id=research_id,
                    evidence_id=evidence_db_id,
                    source_id=source_db_id,
                    claim=claim_text,
                    citation_number=citation.get("citation_number", 1),
                    quote=claim_text,
                )
                self.db.add(db_citation)

            report_data = final_state.get("report", {})
            if report_data:
                report_content = report_data.get("content", "")
                report_references = "\n".join([
                    f"[{c.get('citation_number', i+1)}] {c.get('source_url', '')}"
                    for i, c in enumerate(report_data.get("citations", []))
                ])
                report = Report(
                    session_id=research_id,
                    title=report_data.get("title", "Research Report"),
                    content=report_content,
                    executive_summary=report_content[:500] if report_content else None,
                    references=report_references if report_references else None,
                )
                self.db.add(report)

            self._log_agent(research_id, "planner", "Created research plan")
            self._log_agent(research_id, "researcher", "Searched web sources")
            self._log_agent(research_id, "extractor", "Extracted evidence")
            self._log_agent(research_id, "verifier", "Verified claims")
            self._log_agent(research_id, "analyst", "Analyzed findings")
            self._log_agent(research_id, "conflict_detector", "Detected conflicts")
            self._log_agent(research_id, "writer", "Generated report")

            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)
            session.summary = report_data.get("content", "")[:500] if report_data else ""

        except Exception as e:
            logger.error(f"Research failed: {e}", data={"research_id": str(research_id)})
            session.status = "failed"
            session.completed_at = datetime.now(timezone.utc)
            self._log_agent(research_id, "system", f"Error: {str(e)}", status="failed")

        return str(research_id)

    def _log_agent(self, research_id, agent_name, action, status="completed"):
        log = AgentLog(
            session_id=research_id,
            agent_name=agent_name,
            action=action[:250],
            status=status,
        )
        self.db.add(log)
