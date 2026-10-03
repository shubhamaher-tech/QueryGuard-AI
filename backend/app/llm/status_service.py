import logging
from app.llm.client import ollama_client
from app.llm.schemas import LLMStatusResponse

logger = logging.getLogger("queryguard.llm.status")

class LLMStatusService:
    """Provides health and readiness status for the local SLM service."""

    def get_status(self) -> LLMStatusResponse:
        return ollama_client.get_status()

llm_status_service = LLMStatusService()
