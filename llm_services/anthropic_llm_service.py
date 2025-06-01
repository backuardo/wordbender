import json
import time
from typing import Any

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from llm_services.llm_service import LlmConfig, LlmProvider, LlmService


class AnthropicLlmService(LlmService):
    """Base class for Anthropic LLM services."""

    def __init__(self, config: LlmConfig):
        if not config.api_url:
            config.api_url = "https://api.anthropic.com/v1/messages"
        super().__init__(config)

    @property
    def provider(self) -> LlmProvider:
        return LlmProvider.ANTHROPIC

    def _build_payload(self, prompt: str, max_tokens: int) -> dict[str, Any]:
        """Build the request payload for Anthropic API."""
        return {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "system": (
                "You are a helpful assistant that generates wordlists "
                "for security testing."
            ),
        }

    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """Make the API call to Anthropic."""
        if not self._config.api_url:
            raise RuntimeError("API URL is not configured")

        headers = {
            "x-api-key": self._config.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = self._build_payload(prompt, max_tokens)

        max_retries = self._config.max_retries
        retry_delay = 1
        last_error = None

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
                    raise RuntimeError("Invalid API key for Anthropic")
                elif response.status_code == 403:
                    raise RuntimeError("Access forbidden - check API key permissions")
                elif response.status_code == 429:
                    # Rate limited - check headers for retry info
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and attempt < max_retries - 1:
                        wait_time = int(retry_after)
                        time.sleep(wait_time)
                        retry_delay *= 2
                        continue
                    else:
                        raise RuntimeError(
                            f"Anthropic API rate limit exceeded after "
                            f"{attempt + 1} attempts"
                        )
                elif response.status_code == 400:
                    # Bad request - parse error message
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get(
                            "message", "Bad request"
                        )
                        raise RuntimeError(f"Anthropic API error: {error_msg}")
                    except json.JSONDecodeError:
                        raise RuntimeError(
                            f"Anthropic API bad request: {response.text}"
                        ) from None

                response.raise_for_status()

                # Parse JSON response with error handling
                try:
                    data = response.json()
                except json.JSONDecodeError as e:
                    raise RuntimeError(
                        f"Invalid JSON response from Anthropic: {e}"
                    ) from e

                # Extract content from Anthropic's response format
                if "content" not in data or not data["content"]:
                    raise RuntimeError(
                        f"Invalid response format from Anthropic API: {data}"
                    )

                # Anthropic returns content as a list of content blocks
                content_blocks = data["content"]
                if not content_blocks or "text" not in content_blocks[0]:
                    raise RuntimeError(f"No text content in Anthropic response: {data}")

                text_content = content_blocks[0]["text"]
                return str(text_content) if text_content else ""

            except Timeout:
                last_error = RuntimeError(
                    f"Request timeout after {self._config.timeout}s"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue

            except ConnectionError as e:
                last_error = RuntimeError(f"Connection error to Anthropic API: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue

            except HTTPError as e:
                # Already handled specific status codes above
                last_error = RuntimeError(
                    f"Anthropic API HTTP error: {e.response.status_code} - {e}"
                )
                if attempt < max_retries - 1 and e.response.status_code >= 500:
                    # Retry on server errors
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise last_error from None

            except RequestException as e:
                last_error = RuntimeError(f"Anthropic API request failed: {e}")
                raise last_error from e

            except RuntimeError:
                # Re-raise our custom runtime errors
                raise

            except Exception as e:
                last_error = RuntimeError(
                    f"Unexpected error calling Anthropic API: {type(e).__name__} - {e}"
                )
                raise last_error from e

        # If we exhausted all retries
        if last_error:
            raise last_error
        else:
            raise RuntimeError(
                f"Failed to get response from Anthropic after {max_retries} attempts"
            )


class AnthropicClaude3OpusLlmService(AnthropicLlmService):
    """Claude 3 Opus via Anthropic API."""

    @property
    def model_name(self) -> str:
        return "claude-3-opus-20240229"


class AnthropicClaude3SonnetLlmService(AnthropicLlmService):
    """Claude 3 Sonnet via Anthropic API."""

    @property
    def model_name(self) -> str:
        return "claude-3-sonnet-20240229"


class AnthropicClaude3HaikuLlmService(AnthropicLlmService):
    """Claude 3 Haiku via Anthropic API."""

    @property
    def model_name(self) -> str:
        return "claude-3-haiku-20240307"


class AnthropicClaude35SonnetLlmService(AnthropicLlmService):
    """Claude 3.5 Sonnet via Anthropic API."""

    @property
    def model_name(self) -> str:
        return "claude-3-5-sonnet-20241022"  # Latest version


class AnthropicClaude35HaikuLlmService(AnthropicLlmService):
    """Claude 3.5 Haiku via Anthropic API."""

    @property
    def model_name(self) -> str:
        return "claude-3-5-haiku-20241022"


class AnthropicClaudeOpus4LlmService(AnthropicLlmService):
    """Claude Opus 4 via Anthropic API."""

    @property
    def model_name(self) -> str:
        return "claude-opus-4-20250514"


class AnthropicClaudeSonnet4LlmService(AnthropicLlmService):
    """Claude Sonnet 4 via Anthropic API."""

    @property
    def model_name(self) -> str:
        return "claude-sonnet-4-20250514"
