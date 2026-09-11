from sqlalchemy.ext.asyncio import AsyncSession
from app.services.embeddings import embedding_service


class MemoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def store_finding(self, research_id: str, content: str, metadata: dict = None):
        embedding = await embedding_service.embed_text(content)

        await self.db.execute(
            """INSERT INTO research_memory (research_id, content, embedding, metadata)
               VALUES (:research_id, :content, :embedding, :metadata)""",
            {
                "research_id": research_id,
                "content": content,
                "embedding": str(embedding),
                "metadata": str(metadata or {}),
            },
        )

    async def search_similar(self, query: str, limit: int = 5) -> list[dict]:
        embedding = await embedding_service.embed_text(query)

        result = await self.db.execute(
            """SELECT content, metadata, 1 - (embedding <=> :embedding) as similarity
               FROM research_memory
               ORDER BY embedding <=> :embedding
               LIMIT :limit""",
            {"embedding": str(embedding), "limit": limit},
        )

        return [{"content": r[0], "metadata": r[1], "similarity": r[2]} for r in result]
