import pytest

from llm_services.llm_service import LlmConfig, LlmProvider, LlmService
from tests.test_constants import CUSTOM_API_URL as TEST_API_URL
from tests.test_constants import (
    TEST_API_KEY,
    TEST_MAX_RETRIES,
    TEST_MODEL_NAME,
    TEST_TIMEOUT,
)

TEST_TEMPERATURE = 0.7


class ConcreteLlmService(LlmService):

    def __init__(self, config: LlmConfig, model_name: str = TEST_MODEL_NAME):
        self._model_name = model_name
        super().__init__(config)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider(self) -> LlmProvider:
        return LlmProvider.CUSTOM

    def _call_api(self, prompt: str, max_tokens: int) -> str:
        return "word1\nword2\nword3"


class TestLlmProvider:

    def test_provider_enum_behavior(self):
        openai = LlmProvider.OPEN_AI
        assert openai.requires_api_key
        assert openai.env_var is not None
        assert "openai" in openai.internal_name.lower()

        local = LlmProvider.LOCAL
        assert not local.requires_api_key
        assert local.env_var is None

    def test_get_by_name(self):
        assert LlmProvider.get_by_name("openai") == LlmProvider.OPEN_AI
        assert LlmProvider.get_by_name("OPENAI") == LlmProvider.OPEN_AI
        assert LlmProvider.get_by_name("anthropic") == LlmProvider.ANTHROPIC
        assert LlmProvider.get_by_name("nonexistent") is None

    def test_requiring_api_keys(self):
        providers_with_keys = LlmProvider.requiring_api_keys()

        assert LlmProvider.OPEN_AI in providers_with_keys
        assert LlmProvider.ANTHROPIC in providers_with_keys
        assert LlmProvider.OPEN_ROUTER in providers_with_keys
        assert LlmProvider.CUSTOM in providers_with_keys
        assert LlmProvider.LOCAL not in providers_with_keys

    def test_requires_api_key_property(self):
        assert LlmProvider.OPEN_AI.requires_api_key is True
        assert LlmProvider.ANTHROPIC.requires_api_key is True
        assert LlmProvider.LOCAL.requires_api_key is False


class TestLlmConfig:

    def test_config_defaults_and_customization(self):
        default_config = LlmConfig()
        assert default_config.api_key is None
        assert default_config.timeout > 0
        assert default_config.max_retries >= 0

        custom_config = LlmConfig(
            api_key=TEST_API_KEY,
            timeout=TEST_TIMEOUT,
            max_retries=TEST_MAX_RETRIES,
        )
        assert custom_config.api_key == TEST_API_KEY
        assert custom_config.timeout == TEST_TIMEOUT
        assert custom_config.max_retries == TEST_MAX_RETRIES

    def test_custom_config(self):
        config = LlmConfig(
            api_key=TEST_API_KEY,
            api_url=TEST_API_URL,
            timeout=TEST_TIMEOUT,
            max_retries=TEST_MAX_RETRIES,
            additional_params={"temperature": TEST_TEMPERATURE},
        )

        assert config.api_key == TEST_API_KEY
        assert config.api_url == TEST_API_URL
        assert config.timeout == TEST_TIMEOUT
        assert config.max_retries == TEST_MAX_RETRIES
        assert config.additional_params == {"temperature": TEST_TEMPERATURE}


class TestLlmService:

    @pytest.fixture
    def valid_config(self):
        return LlmConfig(api_key=TEST_API_KEY)

    @pytest.fixture
    def service(self, valid_config):
        return ConcreteLlmService(valid_config)

    def test_initialization_valid(self, valid_config):
        service = ConcreteLlmService(valid_config)
        assert service._config == valid_config
        assert service.model_name == TEST_MODEL_NAME
        assert service.provider == LlmProvider.CUSTOM

    def test_initialization_missing_api_key(self):
        config = LlmConfig()
        with pytest.raises(ValueError, match="requires an API key"):
            ConcreteLlmService(config)

    def test_initialization_invalid_timeout(self):
        config = LlmConfig(api_key=TEST_API_KEY, timeout=0)
        with pytest.raises(ValueError, match="Timeout must be positive"):
            ConcreteLlmService(config)

        config = LlmConfig(api_key=TEST_API_KEY, timeout=-10)
        with pytest.raises(ValueError, match="Timeout must be positive"):
            ConcreteLlmService(config)

    def test_initialization_invalid_retries(self):
        config = LlmConfig(api_key=TEST_API_KEY, max_retries=-1)
        with pytest.raises(ValueError, match="Max retries must be non-negative"):
            ConcreteLlmService(config)

    def test_requires_api_key_property(self, service):
        assert service.requires_api_key is True

    def test_generate_words_success(self, service):
        prompt = "Generate words related to test"
        words = service.generate_words(prompt, expected_count=3)

        assert words == ["word1", "word2", "word3"]

    def test_generate_words_empty_response(self, valid_config):
        class EmptyResponseService(ConcreteLlmService):
            def _call_api(self, prompt: str, max_tokens: int) -> str:
                return ""

        service = EmptyResponseService(valid_config)
        with pytest.raises(ValueError, match="LLM returned empty response"):
            service.generate_words("test prompt", 10)

    def test_generate_words_whitespace_response(self, valid_config):
        class WhitespaceResponseService(ConcreteLlmService):
            def _call_api(self, prompt: str, max_tokens: int) -> str:
                return "   \n\t   "

        service = WhitespaceResponseService(valid_config)
        with pytest.raises(ValueError, match="LLM returned empty response"):
            service.generate_words("test prompt", 10)

    def test_parse_word_list_basic(self, service):
        response = "word1\nword2\nword3"
        words = service._parse_word_list(response)
        assert words == ["word1", "word2", "word3"]

    def test_parse_word_list_with_whitespace(self, service):
        response = "  word1  \n\n  word2\n\t word3  \n"
        words = service._parse_word_list(response)
        assert words == ["word1", "word2", "word3"]

    def test_parse_word_list_filter_patterns(self, service):
        response = """word1
Category: Test
word2
(explanation)
word3
[note]
-> arrow
#comment
* bullet
word4"""
        words = service._parse_word_list(response)
        assert words == ["word1", "word2", "word3", "word4"]

    def test_parse_word_list_multi_word_entries(self, service):
        response = """single
two words
hyphenated-word
three word phrase
another-hyphen"""
        words = service._parse_word_list(response)
        assert words == ["single", "hyphenated-word", "another-hyphen"]

    def test_parse_word_list_punctuation_cleanup(self, service):
        response = """word1.
"word2"
'word3'
word4,
word5;
word6!
word7?"""
        words = service._parse_word_list(response)
        expected = ["word1", "word2", "word3", "word4", "word5", "word6", "word7"]
        assert words == expected

    def test_token_estimation(self, valid_config):
        class TokenTestService(ConcreteLlmService):
            def _call_api(self, prompt: str, max_tokens: int) -> str:
                assert max_tokens <= 4000
                assert max_tokens > 100
                return "word1"

        service = TokenTestService(valid_config)
        service.generate_words("Short prompt", expected_count=10)
