import httpx
from app.core.config import get_settings


class EmbeddingService:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.EMBEDDING_API_KEY
        self.model = settings.EMBEDDING_MODEL

    async def embed_text(self, text: str) -> list[float]:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "input": text},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]


embedding_service = EmbeddingService()
