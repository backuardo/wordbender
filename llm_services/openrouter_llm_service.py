from typing import Any, Dict

import requests

from llm_services.llm_service import LlmConfig, LlmProvider, LlmService


class OpenRouterLlmService(LlmService):
    """Base class for OpenRouter LLM services."""

    def __init__(self, config: LlmConfig):
        # Set default OpenRouter API URL if not provided
        if not config.api_url:
            config.api_url = "https://openrouter.ai/api/v1/chat/completions"
        super().__init__(config)

    @property
    def provider(self) -> LlmProvider:
        return LlmProvider.OPEN_ROUTER

    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """Call the OpenRouter API."""
        additional_params: Dict[str, Any] = self._config.additional_params or {}
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "HTTP-Referer": additional_params.get("referer", "http://localhost"),
            "X-Title": additional_params.get("app_title", "Wordlist Generator"),
        }

        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        try:
            # api_url is guaranteed to be not None
            assert self._config.api_url is not None

            response = requests.post(
                self._config.api_url,
                json=payload,
                headers=headers,
                timeout=self._config.timeout,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"OpenRouter API call failed: {e}")


class OpenRouterClaudeOpusLlmService(OpenRouterLlmService):
    """Claude 3 Opus via OpenRouter."""

    @property
    def model_name(self) -> str:
        return "anthropic/claude-3-opus"


class OpenRouterGpt4LlmService(OpenRouterLlmService):
    """GPT-4 via OpenRouter."""

    @property
    def model_name(self) -> str:
        return "openai/gpt-4-turbo-preview"
