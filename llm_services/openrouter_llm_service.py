import json
import time
from typing import Any

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

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
        """Call the OpenRouter API with comprehensive error handling."""
        if not self._config.api_url:
            raise RuntimeError("API URL is not configured")

        additional_params: dict[str, Any] = self._config.additional_params or {}
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
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self._config.api_url,
                    json=payload,
                    headers=headers,
                    timeout=self._config.timeout,
                )

                # Check for specific HTTP errors
                if response.status_code == 401:
                    raise RuntimeError("Invalid API key for OpenRouter")
                elif response.status_code == 403:
                    raise RuntimeError("Access forbidden - check API key permissions")
                elif response.status_code == 429:
                    # Rate limited - check headers for retry info
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and attempt < max_retries - 1:
                        wait_time = float(retry_after) if retry_after else retry_delay
                        time.sleep(wait_time)
                        retry_delay *= 2
                        continue
                    else:
                        raise RuntimeError(
                            f"OpenRouter API rate limit exceeded after {
                                attempt + 1
                            } attempts"
                        )

                response.raise_for_status()

                # Parse JSON response with error handling
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    raise RuntimeError(
                        f"Invalid JSON response from OpenRouter: {e}"
                    ) from e

                # Validate response structure
                if "choices" not in data or not data["choices"]:
                    raise RuntimeError(
                        f"Invalid response format from OpenRouter API: {data}"
                    )

                # Extract content
                content = data["choices"][0].get("message", {}).get("content", "")
                if not content or not isinstance(content, str) or not content.strip():
                    raise RuntimeError("Empty response content from OpenRouter API")

                return str(content)

            except Timeout:
                last_error = RuntimeError(
                    f"Request timeout after {self._config.timeout}s"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue

            except ConnectionError as e:
                last_error = RuntimeError(f"Connection error to OpenRouter API: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue

            except HTTPError as e:
                # Already handled specific status codes above
                last_error = RuntimeError(
                    f"OpenRouter API HTTP error: {e.response.status_code} - {e}"
                )
                if attempt < max_retries - 1 and e.response.status_code >= 500:
                    # Retry on server errors
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise last_error from None

            except RequestException as e:
                last_error = RuntimeError(f"OpenRouter API request failed: {e}")
                raise last_error from e

            except RuntimeError:
                # Re-raise our custom runtime errors
                raise

            except Exception as e:
                last_error = RuntimeError(
                    f"Unexpected error calling OpenRouter API: {type(e).__name__} - {e}"
                )
                raise last_error from e

        # If we exhausted all retries
        if last_error:
            raise RuntimeError(
                f"Failed after {max_retries} attempts. Last error: {last_error}"
            )
        else:
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
