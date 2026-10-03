import logging
import json
from typing import Optional, Dict, Any, List
import httpx
from app.config import settings
from app.llm.schemas import LLMStatusResponse

logger = logging.getLogger("queryguard.llm.client")

class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS
        self.enabled = settings.OLLAMA_ENABLED

    def get_status(self) -> LLMStatusResponse:
        """Check Ollama service connectivity and model presence."""
        if not self.enabled:
            return LLMStatusResponse(
                enabled=False,
                service_reachable=False,
                selected_model=self.model,
                model_available_locally=False,
                local_only_privacy_mode=True,
                message="Local SLM integration is disabled in configuration.",
                available_models=[],
            )

        try:
            with httpx.Client(timeout=3.0) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    data = res.json()
                    models_list = [m.get("name", "") for m in data.get("models", [])]
                    # Check if selected model or tag matches
                    is_available = any(
                        self.model in m or m.startswith(self.model) for m in models_list
                    )
                    msg = (
                        f"Ollama reachable. Model '{self.model}' is ready."
                        if is_available
                        else f"Ollama reachable, but model '{self.model}' is not pulled yet."
                    )
                    return LLMStatusResponse(
                        enabled=True,
                        service_reachable=True,
                        selected_model=self.model,
                        model_available_locally=is_available,
                        local_only_privacy_mode=True,
                        message=msg,
                        available_models=models_list,
                    )
                else:
                    return LLMStatusResponse(
                        enabled=True,
                        service_reachable=False,
                        selected_model=self.model,
                        model_available_locally=False,
                        local_only_privacy_mode=True,
                        message=f"Ollama returned HTTP status {res.status_code}.",
                        available_models=[],
                    )
        except Exception as e:
            logger.warning("Ollama connectivity check failed: %s", type(e).__name__)
            return LLMStatusResponse(
                enabled=True,
                service_reachable=False,
                selected_model=self.model,
                model_available_locally=False,
                local_only_privacy_mode=True,
                message="Local Ollama service unreachable at configured endpoint.",
                available_models=[],
            )

    def generate_json_rewrite(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Dict[str, Any]:
        """
        Calls Ollama chat endpoint requesting strict JSON output.
        Returns the parsed dictionary.
        """
        if not self.enabled:
            raise RuntimeError("Ollama SLM is disabled in configuration.")

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "format": "json",
            "stream": False,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
            },
        }

        try:
            with httpx.Client(timeout=float(self.timeout)) as client:
                res = client.post(url, json=payload)
                if res.status_code != 200:
                    logger.error("Ollama generate failed with status %d: %s", res.status_code, res.text[:200])
                    raise RuntimeError(f"Ollama API returned HTTP {res.status_code}")

                data = res.json()
                content = data.get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Ollama returned empty response content")

                # Parse JSON
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ValueError("Model output JSON is not a dictionary")
                return parsed

        except httpx.TimeoutException:
            logger.warning("Ollama request timed out after %d seconds", self.timeout)
            raise TimeoutError(f"Ollama request timed out after {self.timeout}s")
        except json.JSONDecodeError as jde:
            logger.warning("Ollama returned invalid JSON: %s", str(jde))
            raise ValueError(f"Model output is not valid JSON: {jde}")
        except Exception as e:
            logger.warning("Ollama call failed: %s", str(e))
            raise e

ollama_client = OllamaClient()
