import time
from typing import Any, Dict

import requests
from requests.exceptions import HTTPError, RequestException

from llm_services.llm_service import LlmConfig, LlmProvider, LlmService


class OpenRouterLlmService(LlmService):
    """Base class for OpenRouter LLM services."""

    def __init__(self, config: LlmConfig):
        if not config.api_url:
            config.api_url = "https://openrouter.ai/api/v1/chat/completions"
        super().__init__(config)

    @property
    def provider(self) -> LlmProvider:
        return LlmProvider.OPEN_ROUTER

    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """Call the OpenRouter API."""
        if not self._config.api_url:
            raise RuntimeError("API URL is not configured")

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

        max_retries = self._config.max_retries
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self._config.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self._config.timeout,
                )
                response.raise_for_status()

                data = response.json()
                if "choices" not in data or not data["choices"]:
                    raise RuntimeError("Invalid response format from OpenRouter API")

                content = data["choices"][0].get("message", {}).get("content", "")
                if not content:
                    raise RuntimeError("Empty response from OpenRouter API")

                return content

            except HTTPError as e:
                if e.response and e.response.status_code == 429:  # Rate limited
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        raise RuntimeError(
                            f"OpenRouter API rate limit exceeded after {
                                max_retries
                            } attempts"
                        )
                else:
                    raise RuntimeError(f"OpenRouter API HTTP error: {e}")

            except RequestException as e:
                raise RuntimeError(f"OpenRouter API request failed: {e}")

            except Exception as e:
                raise RuntimeError(f"Unexpected error calling OpenRouter API: {e}")

        raise RuntimeError(f"Failed to get response after {max_retries} attempts")


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
