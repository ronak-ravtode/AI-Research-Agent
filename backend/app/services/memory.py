from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.services.embeddings import embedding_service


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_finding(self, research_id: str, content: str, metadata: dict = None):
        embedding = await embedding_service.embed_text(content)
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        await self.db.execute(
            text("""INSERT INTO research_memory (research_id, content, embedding, metadata)
                   VALUES (:research_id, :content, :embedding::vector, :metadata)"""),
            {
                "research_id": research_id,
                "content": content,
                "embedding": embedding_str,
                "metadata": str(metadata or {}),
            },
        )

    async def search_similar(self, query: str, limit: int = 5) -> list[dict]:
        embedding = await embedding_service.embed_text(query)
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

        result = await self.db.execute(
            text("""SELECT content, metadata, 1 - (embedding <=> :embedding::vector) as similarity
                   FROM research_memory
                   ORDER BY embedding <=> :embedding::vector
                   LIMIT :limit"""),
            {"embedding": embedding_str, "limit": limit},
        )

        return [{"content": r[0], "metadata": r[1], "similarity": r[2]} for r in result]
