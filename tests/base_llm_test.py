"""Base test class for LLM service tests to reduce duplication."""

import json
from unittest.mock import Mock, patch

import pytest
import responses
from requests.exceptions import ConnectionError, Timeout

from .test_constants import (
    TEST_API_KEY,
    TEST_MAX_RETRIES,
    TEST_TIMEOUT,
)


class BaseLlmServiceTest:

    def setup_basic_config(self):
        from llm_services.llm_service import LlmConfig

        return LlmConfig(
            api_key=TEST_API_KEY, timeout=TEST_TIMEOUT, max_retries=TEST_MAX_RETRIES
        )

    def assert_request_headers(self, request, expected_headers):
        for header, value in expected_headers.items():
            assert request.headers[header] == value

    def assert_request_body(self, request, expected_fields):
        body = json.loads(request.body)
        for field, value in expected_fields.items():
            assert body[field] == value

    def test_api_success_pattern(
        self, service, api_url, success_response, expected_content
    ):
        responses.add(
            responses.POST,
            api_url,
            json=success_response,
            status=200,
        )

        result = service._call_api("test prompt", 100)
        assert result == expected_content
        assert len(responses.calls) == 1

    def test_api_401_error_pattern(self, service, api_url, provider_name):
        responses.add(responses.POST, api_url, status=401)

        with pytest.raises(RuntimeError, match=f"Invalid API key for {provider_name}"):
            service._call_api("test", 100)

    def test_api_403_error_pattern(self, service, api_url):
        responses.add(responses.POST, api_url, status=403)

        with pytest.raises(RuntimeError, match="Access forbidden"):
            service._call_api("test", 100)

    def test_api_429_rate_limit_pattern(
        self, service, api_url, success_response, expected_content
    ):
        responses.add(
            responses.POST,
            api_url,
            status=429,
            headers={"Retry-After": "0.1"},
        )
        responses.add(
            responses.POST,
            api_url,
            json=success_response,
            status=200,
        )

        result = service._call_api("test", 100)
        assert result == expected_content
        assert len(responses.calls) == 2

    def test_api_timeout_retry_pattern(
        self, service, success_response, expected_content
    ):
        with patch("requests.post") as mock_post:
            mock_response = Mock(
                status_code=200,
                json=lambda: success_response,
            )
            mock_post.side_effect = [Timeout(), mock_response]

            with patch("time.sleep"):
                result = service._call_api("test", 100)

            assert result == expected_content
            assert mock_post.call_count == 2

    def test_api_connection_error_retry_pattern(
        self, service, success_response, expected_content
    ):
        with patch("requests.post") as mock_post:
            mock_response = Mock(
                status_code=200,
                json=lambda: success_response,
            )
            mock_post.side_effect = [ConnectionError("Network error"), mock_response]

            with patch("time.sleep"):
                result = service._call_api("test", 100)

            assert result == expected_content
            assert mock_post.call_count == 2

    def test_api_server_error_retry_pattern(
        self, service, api_url, success_response, expected_content
    ):
        responses.add(responses.POST, api_url, status=500)
        responses.add(
            responses.POST,
            api_url,
            json=success_response,
            status=200,
        )

        with patch("time.sleep"):
            result = service._call_api("test", 100)

        assert result == expected_content
        assert len(responses.calls) == 2

    def test_api_invalid_json_pattern(self, service, api_url):
        responses.add(
            responses.POST,
            api_url,
            body="not json",
            status=200,
        )

        with pytest.raises(RuntimeError, match="Invalid JSON response"):
            service._call_api("test", 100)

    def test_api_no_url_pattern(self, service):
        service._config.api_url = None

        with pytest.raises(RuntimeError, match="API URL is not configured"):
            service._call_api("test", 100)

    def test_api_exhausted_retries_pattern(self, service):
        service._config.max_retries = 2

        with patch("requests.post") as mock_post:
            mock_post.side_effect = [Timeout(), Timeout()]

            with patch("time.sleep"):
                with pytest.raises(RuntimeError, match="Request timeout"):
                    service._call_api("test", 100)

            assert mock_post.call_count == 2
