import json
from unittest.mock import Mock, patch

import pytest
import responses
from requests.exceptions import ConnectionError, Timeout

from llm_services.llm_service import LlmConfig
from llm_services.openrouter_llm_service import (
    OpenRouterClaudeOpusLlmService,
    OpenRouterGpt4LlmService,
    OpenRouterLlmService,
)

TEST_API_KEY = "test-key"
TEST_MODEL_NAME = "test/model"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
CUSTOM_API_URL = "https://custom.api.com/v1/chat"
DEFAULT_REFERER = "http://localhost"
DEFAULT_TITLE = "Wordlist Generator"


class TestOpenRouterLlmService:
    @pytest.fixture
    def config(self):
        return LlmConfig(api_key=TEST_API_KEY, timeout=30, max_retries=3)

    @pytest.fixture
    def service(self, config):
        class TestOpenRouterService(OpenRouterLlmService):
            @property
            def model_name(self) -> str:
                return TEST_MODEL_NAME

        return TestOpenRouterService(config)

    def test_initialization_default_url(self, config):
        class TestOpenRouterService(OpenRouterLlmService):
            @property
            def model_name(self) -> str:
                return TEST_MODEL_NAME

        TestOpenRouterService(config)
        assert config.api_url == OPENROUTER_API_URL

    def test_initialization_custom_url(self):
        config = LlmConfig(api_key=TEST_API_KEY, api_url=CUSTOM_API_URL)

        class TestOpenRouterService(OpenRouterLlmService):
            @property
            def model_name(self) -> str:
                return TEST_MODEL_NAME

        TestOpenRouterService(config)
        assert config.api_url == CUSTOM_API_URL

    @responses.activate
    def test_call_api_success(self, service):
        expected_content = "word1\nword2\nword3"
        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            json={"choices": [{"message": {"content": expected_content}}]},
            status=200,
        )

        result = service._call_api("test prompt", 100)
        assert result == expected_content

        assert len(responses.calls) == 1
        req = responses.calls[0].request
        assert req.headers["Authorization"] == f"Bearer {TEST_API_KEY}"
        assert req.headers["HTTP-Referer"] == DEFAULT_REFERER
        assert req.headers["X-Title"] == DEFAULT_TITLE

        body = json.loads(req.body or "")
        assert body["model"] == TEST_MODEL_NAME
        assert body["messages"][0]["content"] == "test prompt"
        assert body["max_tokens"] == 100

    @responses.activate
    def test_call_api_custom_headers(self, config):
        config.additional_params = {
            "referer": "https://myapp.com",
            "app_title": "My App",
        }
        service = type(self).MockOpenRouterService(config)

        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            json={"choices": [{"message": {"content": "test"}}]},
            status=200,
        )

        service._call_api("test", 100)

        req = responses.calls[0].request
        assert req.headers["HTTP-Referer"] == "https://myapp.com"
        assert req.headers["X-Title"] == "My App"

    @responses.activate
    def test_call_api_401_error(self, service):
        responses.add(responses.POST, OPENROUTER_API_URL, status=401)

        with pytest.raises(RuntimeError, match="Invalid API key for OpenRouter"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_403_error(self, service):
        responses.add(responses.POST, OPENROUTER_API_URL, status=403)

        with pytest.raises(RuntimeError, match="Access forbidden"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_429_rate_limit(self, service):
        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            status=429,
            headers={"Retry-After": "0.1"},
        )
        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            json={"choices": [{"message": {"content": "success"}}]},
            status=200,
        )

        result = service._call_api("test", 100)
        assert result == "success"
        assert len(responses.calls) == 2

    @responses.activate
    def test_call_api_429_exhausted_retries(self, service):
        service._config.max_retries = 2

        for _ in range(2):
            responses.add(
                responses.POST,
                OPENROUTER_API_URL,
                status=429,
            )

        with pytest.raises(RuntimeError, match="rate limit exceeded"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_invalid_json(self, service):
        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            body="not json",
            status=200,
        )

        with pytest.raises(RuntimeError, match="Invalid JSON response"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_invalid_response_format(self, service):
        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            json={"error": "missing choices"},
            status=200,
        )

        with pytest.raises(RuntimeError, match="Invalid response format"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_empty_choices(self, service):
        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            json={"choices": []},
            status=200,
        )

        with pytest.raises(RuntimeError, match="Invalid response format"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_empty_content(self, service):
        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            json={"choices": [{"message": {"content": "  "}}]},
            status=200,
        )

        with pytest.raises(RuntimeError, match="Empty response content"):
            service._call_api("test", 100)

    @patch("requests.post")
    def test_call_api_timeout_retry(self, mock_post, service):
        mock_post.side_effect = [
            Timeout(),
            Mock(
                status_code=200,
                json=lambda: {"choices": [{"message": {"content": "success"}}]},
            ),
        ]

        result = service._call_api("test", 100)
        assert result == "success"
        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_call_api_connection_error_retry(self, mock_post, service):
        mock_post.side_effect = [
            ConnectionError("Network error"),
            Mock(
                status_code=200,
                json=lambda: {"choices": [{"message": {"content": "success"}}]},
            ),
        ]

        result = service._call_api("test", 100)
        assert result == "success"
        assert mock_post.call_count == 2

    @responses.activate
    def test_call_api_server_error_retry(self, service):
        responses.add(responses.POST, OPENROUTER_API_URL, status=500)
        responses.add(
            responses.POST,
            OPENROUTER_API_URL,
            json={"choices": [{"message": {"content": "success"}}]},
            status=200,
        )

        result = service._call_api("test", 100)
        assert result == "success"
        assert len(responses.calls) == 2

    def test_call_api_no_url(self, service):
        service._config.api_url = None

        with pytest.raises(RuntimeError, match="API URL is not configured"):
            service._call_api("test", 100)

    class MockOpenRouterService(OpenRouterLlmService):
        @property
        def model_name(self) -> str:
            return "test/model"


class TestOpenRouterClaudeOpusLlmService:
    def test_model_name(self):
        config = LlmConfig(api_key=TEST_API_KEY)
        service = OpenRouterClaudeOpusLlmService(config)
        assert service.model_name == "anthropic/claude-3-opus"


class TestOpenRouterGpt4LlmService:
    def test_model_name(self):
        config = LlmConfig(api_key=TEST_API_KEY)
        service = OpenRouterGpt4LlmService(config)
        assert service.model_name == "openai/gpt-4-turbo-preview"
