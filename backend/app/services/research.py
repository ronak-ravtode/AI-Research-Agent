from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import (
    ResearchSession, ResearchTask, Source, Evidence,
    Citation, Report, AgentLog, ResearchStatus
)
from app.agents.planner import planner_agent
from app.agents.researcher import researcher_agent
from app.agents.extractor import extractor_agent
from app.agents.verifier import verifier_agent
from app.agents.analyst import sufficiency_agent, analyst_agent
from app.agents.conflict_detector import conflict_detector_agent
from app.agents.writer import writer_agent
from app.services.citations import map_citations
from app.services.confidence import calculate_confidence
from app.agents.state import ResearchState


class ResearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def start_research(self, query: str, depth: str = "standard") -> str:
        research_id = uuid4()

        session = ResearchSession(
            id=research_id,
            query=query,
            status=ResearchStatus.PLANNING.value,
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
            state = {**state, **await planner_agent(state)}
            await self._log(research_id, "planner", "Created research plan")

            task_ids = {}
            for subtask in state.get("research_plan", []):
                task_id = uuid4()
                task_ids[subtask.get("id")] = task_id
                db_task = ResearchTask(
                    id=task_id,
                    session_id=research_id,
                    title=subtask.get("task", ""),
                    description=subtask.get("task", ""),
                )
                self.db.add(db_task)

            state = {**state, **await researcher_agent(state)}
            await self._log(research_id, "researcher", "Searched web sources")

            source_id_map = {}
            for src in state.get("sources", []):
                source_db_id = uuid4()
                source_url = src.get("url", "")
                source_id_map[source_url] = source_db_id
                db_source = Source(
                    id=source_db_id,
                    session_id=research_id,
                    title=src.get("title", ""),
                    url=source_url,
                    content=src.get("content"),
                    relevance_score=src.get("relevance_score", 0.0),
                )
                self.db.add(db_source)

            state = {**state, **await extractor_agent(state)}
            await self._log(research_id, "extractor", "Extracted evidence")

            first_task_id = list(task_ids.values())[0] if task_ids else uuid4()
            for ev in state.get("evidence", []):
                source_url = ev.get("source_url", "")
                source_db_id = source_id_map.get(source_url)
                if not source_db_id:
                    continue
                claim_text = ev.get("claim", "")
                evidence_text = ev.get("evidence_text", "")
                db_evidence = Evidence(
                    task_id=first_task_id,
                    source_id=source_db_id,
                    content=f"{claim_text}\n\n{evidence_text}".strip(),
                    confidence_score=ev.get("confidence_score", 0.5),
                )
                self.db.add(db_evidence)

            state = {**state, **await verifier_agent(state)}
            await self._log(research_id, "verifier", "Verified claims")

            state = {**state, **await sufficiency_agent(state)}

            if state.get("status") == "researching":
                state = {**state, **await researcher_agent(state)}
                for src in state.get("sources", []):
                    source_url = src.get("url", "")
                    if source_url not in source_id_map:
                        source_db_id = uuid4()
                        source_id_map[source_url] = source_db_id
                        db_source = Source(
                            id=source_db_id,
                            session_id=research_id,
                            title=src.get("title", ""),
                            url=source_url,
                            content=src.get("content"),
                            relevance_score=src.get("relevance_score", 0.0),
                        )
                        self.db.add(db_source)

                state = {**state, **await extractor_agent(state)}
                for ev in state.get("evidence", []):
                    source_url = ev.get("source_url", "")
                    source_db_id = source_id_map.get(source_url)
                    if not source_db_id:
                        continue
                    claim_text = ev.get("claim", "")
                    evidence_text = ev.get("evidence_text", "")
                    db_evidence = Evidence(
                        task_id=first_task_id,
                        source_id=source_db_id,
                        content=f"{claim_text}\n\n{evidence_text}".strip(),
                        confidence_score=ev.get("confidence_score", 0.5),
                    )
                    self.db.add(db_evidence)

                state = {**state, **await verifier_agent(state)}

            state = {**state, **await analyst_agent(state)}
            await self._log(research_id, "analyst", "Analyzed findings")

            state = {**state, **await conflict_detector_agent(state)}
            await self._log(research_id, "conflict_detector", "Detected conflicts")

            citations = map_citations(state.get("verified_claims", []), state.get("sources", []))
            state["citations"] = citations
            state["confidence_scores"] = calculate_confidence(state.get("verified_claims", []))

            state = {**state, **await writer_agent(state)}
            await self._log(research_id, "writer", "Generated report")

            await self._save_results(research_id, state, source_id_map, first_task_id)

            session.status = ResearchStatus.COMPLETED.value

        except Exception as e:
            session.status = ResearchStatus.FAILED.value
            await self._log(research_id, "system", f"Error: {str(e)}")

        return str(research_id)

    async def _log(self, research_id, agent_name, action):
        log = AgentLog(
            session_id=research_id,
            agent_name=agent_name,
            action=action,
        )
        self.db.add(log)

    async def _save_results(self, research_id, state, source_id_map, task_id):
        for citation in state.get("citations", []):
            source_url = citation.get("source_url", "")
            source_db_id = source_id_map.get(source_url)
            if not source_db_id:
                continue
            claim_text = citation.get("claim", "")
            db_citation = Citation(
                evidence_id=task_id,
                source_id=source_db_id,
                quote=claim_text,
            )
            self.db.add(db_citation)

        report_data = state.get("report", {})
        if report_data:
            report = Report(
                session_id=research_id,
                title=report_data.get("title", "Research Report"),
                content=report_data.get("content", ""),
            )
            self.db.add(report)
