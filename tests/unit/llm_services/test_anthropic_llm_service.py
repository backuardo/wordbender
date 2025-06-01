import json
from unittest.mock import Mock, patch

import pytest
import responses
from requests.exceptions import ConnectionError, Timeout

from llm_services.anthropic_llm_service import (
    AnthropicClaude3HaikuLlmService,
    AnthropicClaude3OpusLlmService,
    AnthropicClaude35SonnetLlmService,
    AnthropicLlmService,
)
from llm_services.llm_service import LlmConfig

TEST_API_KEY = "test-key"
TEST_MODEL_NAME = "claude-test-model"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CUSTOM_API_URL = "https://custom.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
CONTENT_TYPE = "application/json"


class TestAnthropicLlmService:

    @pytest.fixture
    def config(self):
        return LlmConfig(api_key=TEST_API_KEY, timeout=30, max_retries=3)

    @pytest.fixture
    def service(self, config):
        class TestAnthropicService(AnthropicLlmService):
            @property
            def model_name(self) -> str:
                return TEST_MODEL_NAME

        return TestAnthropicService(config)

    def test_initialization_default_url(self, config):
        class TestAnthropicService(AnthropicLlmService):
            @property
            def model_name(self) -> str:
                return TEST_MODEL_NAME

        TestAnthropicService(config)
        assert config.api_url == ANTHROPIC_API_URL

    def test_initialization_custom_url(self):
        config = LlmConfig(api_key=TEST_API_KEY, api_url=CUSTOM_API_URL)

        class TestAnthropicService(AnthropicLlmService):
            @property
            def model_name(self) -> str:
                return TEST_MODEL_NAME

        TestAnthropicService(config)
        assert config.api_url == CUSTOM_API_URL

    def test_build_payload(self, service):
        payload = service._build_payload("test prompt", 100)

        assert payload["model"] == TEST_MODEL_NAME
        assert payload["messages"] == [{"role": "user", "content": "test prompt"}]
        assert payload["max_tokens"] == 100
        assert payload["temperature"] == 0.7
        assert "security testing" in payload["system"]

    @responses.activate
    def test_call_api_success(self, service):
        expected_content = "word1\nword2\nword3"
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            json={"content": [{"type": "text", "text": expected_content}]},
            status=200,
        )

        result = service._call_api("test prompt", 100)
        assert result == expected_content

        assert len(responses.calls) == 1
        req = responses.calls[0].request
        assert req.headers["x-api-key"] == TEST_API_KEY
        assert req.headers["content-type"] == CONTENT_TYPE
        assert req.headers["anthropic-version"] == ANTHROPIC_VERSION

        body = json.loads(req.body)
        assert body["model"] == TEST_MODEL_NAME
        assert body["messages"][0]["content"] == "test prompt"

    @responses.activate
    def test_call_api_401_error(self, service):
        responses.add(responses.POST, ANTHROPIC_API_URL, status=401)

        with pytest.raises(RuntimeError, match="Invalid API key for Anthropic"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_403_error(self, service):
        responses.add(responses.POST, ANTHROPIC_API_URL, status=403)

        with pytest.raises(RuntimeError, match="Access forbidden"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_429_rate_limit(self, service):
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            status=429,
            headers={"Retry-After": "1"},
        )
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            json={"content": [{"type": "text", "text": "success"}]},
            status=200,
        )

        with patch("time.sleep"):
            result = service._call_api("test", 100)
        assert result == "success"
        assert len(responses.calls) == 2

    @responses.activate
    def test_call_api_400_error_with_message(self, service):
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            json={"error": {"message": "Invalid model specified"}},
            status=400,
        )

        with pytest.raises(RuntimeError, match="Invalid model specified"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_400_error_invalid_json(self, service):
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            body="not json",
            status=400,
        )

        with pytest.raises(RuntimeError, match="bad request"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_invalid_json_response(self, service):
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            body="not json",
            status=200,
        )

        with pytest.raises(RuntimeError, match="Invalid JSON response"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_missing_content(self, service):
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            json={"error": "missing content"},
            status=200,
        )

        with pytest.raises(RuntimeError, match="Invalid response format"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_empty_content(self, service):
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            json={"content": []},
            status=200,
        )

        with pytest.raises(RuntimeError, match="Invalid response format"):
            service._call_api("test", 100)

    @responses.activate
    def test_call_api_missing_text(self, service):
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            json={"content": [{"type": "image"}]},
            status=200,
        )

        with pytest.raises(RuntimeError, match="No text content"):
            service._call_api("test", 100)

    @patch("requests.post")
    def test_call_api_timeout_retry(self, mock_post, service):
        mock_response = Mock(
            status_code=200,
            json=lambda: {"content": [{"type": "text", "text": "success"}]},
        )
        mock_post.side_effect = [Timeout(), mock_response]

        with patch("time.sleep"):
            result = service._call_api("test", 100)
        assert result == "success"
        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_call_api_connection_error(self, mock_post, service):
        mock_response = Mock(
            status_code=200,
            json=lambda: {"content": [{"type": "text", "text": "success"}]},
        )
        mock_post.side_effect = [ConnectionError("Network error"), mock_response]

        with patch("time.sleep"):
            result = service._call_api("test", 100)
        assert result == "success"
        assert mock_post.call_count == 2

    @responses.activate
    def test_call_api_server_error_retry(self, service):
        responses.add(responses.POST, ANTHROPIC_API_URL, status=500)
        responses.add(
            responses.POST,
            ANTHROPIC_API_URL,
            json={"content": [{"type": "text", "text": "success"}]},
            status=200,
        )

        with patch("time.sleep"):
            result = service._call_api("test", 100)
        assert result == "success"
        assert len(responses.calls) == 2

    def test_call_api_no_url(self, service):
        service._config.api_url = None

        with pytest.raises(RuntimeError, match="API URL is not configured"):
            service._call_api("test", 100)

    @patch("requests.post")
    def test_call_api_exhausted_retries(self, mock_post, service):
        service._config.max_retries = 2
        mock_post.side_effect = [Timeout(), Timeout()]

        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="Request timeout"):
                service._call_api("test", 100)

        assert mock_post.call_count == 2


class TestAnthropicModelServices:

    @pytest.fixture
    def config(self):
        return LlmConfig(api_key=TEST_API_KEY)

    def test_claude3_opus_model_name(self, config):
        service = AnthropicClaude3OpusLlmService(config)
        assert service.model_name == "claude-3-opus-20240229"

    def test_claude3_sonnet_model_name(self, config):
        from llm_services.anthropic_llm_service import AnthropicClaude3SonnetLlmService

        service = AnthropicClaude3SonnetLlmService(config)
        assert service.model_name == "claude-3-sonnet-20240229"

    def test_claude3_haiku_model_name(self, config):
        service = AnthropicClaude3HaikuLlmService(config)
        assert service.model_name == "claude-3-haiku-20240307"

    def test_claude35_sonnet_model_name(self, config):
        service = AnthropicClaude35SonnetLlmService(config)
        assert service.model_name == "claude-3-5-sonnet-20241022"

    def test_claude35_haiku_model_name(self, config):
        from llm_services.anthropic_llm_service import AnthropicClaude35HaikuLlmService

        service = AnthropicClaude35HaikuLlmService(config)
        assert service.model_name == "claude-3-5-haiku-20241022"

    def test_claude_opus4_model_name(self, config):
        from llm_services.anthropic_llm_service import AnthropicClaudeOpus4LlmService

        service = AnthropicClaudeOpus4LlmService(config)
        assert service.model_name == "claude-opus-4-20250514"

    def test_claude_sonnet4_model_name(self, config):
        from llm_services.anthropic_llm_service import AnthropicClaudeSonnet4LlmService

        service = AnthropicClaudeSonnet4LlmService(config)
        assert service.model_name == "claude-sonnet-4-20250514"
