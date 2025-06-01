from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cli.factories import GeneratorFactory, LlmServiceFactory, ServiceDiscovery
from config import Config
from llm_services.llm_service import LlmProvider, LlmService
from tests.test_constants import (
    ANTHROPIC_SERVICE_FILE,
    GENERATOR_DIR,
    LLM_SERVICE_BASE_FILE,
    LLM_SERVICES_DIR,
    OPENROUTER_SERVICE_FILE,
    PASSWORD_GENERATOR_FILE,
    SUBDOMAIN_GENERATOR_FILE,
    TEST_API_KEY,
    TEST_MODEL_NAME,
)
from wordlist_generators.password_wordlist_generator import PasswordWordlistGenerator
from wordlist_generators.subdomain_wordlist_generator import (
    SubdomainWordlistGenerator,
)


class TestServiceDiscovery:

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_discover_wordlist_generators_success(self, mock_glob, mock_exists):
        mock_exists.return_value = True
        mock_glob.return_value = [
            Path(f"{GENERATOR_DIR}/{PASSWORD_GENERATOR_FILE}"),
            Path(f"{GENERATOR_DIR}/{SUBDOMAIN_GENERATOR_FILE}"),
        ]

        generators = ServiceDiscovery.discover_wordlist_generators()

        assert "password" in generators
        assert "subdomain" in generators
        assert generators["password"] == PasswordWordlistGenerator
        assert generators["subdomain"] == SubdomainWordlistGenerator

    @patch("pathlib.Path.exists")
    def test_discover_wordlist_generators_no_directory(self, mock_exists):
        mock_exists.return_value = False

        generators = ServiceDiscovery.discover_wordlist_generators()
        assert generators == {}

    @patch("pathlib.Path.exists")
    def test_discover_wordlist_generators_permission_error(self, mock_exists):
        mock_exists.side_effect = PermissionError("Access denied")

        with patch("rich.console.Console.print") as mock_print:
            generators = ServiceDiscovery.discover_wordlist_generators()

        assert generators == {}
        mock_print.assert_called_once()
        assert "Cannot access generators directory" in str(mock_print.call_args)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_discover_wordlist_generators_import_error(self, mock_glob, mock_exists):
        mock_exists.return_value = True
        mock_glob.return_value = [Path(f"{GENERATOR_DIR}/broken_generator.py")]

        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")
            generators = ServiceDiscovery.discover_wordlist_generators()

        assert generators == {}

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_discover_llm_services_success(self, mock_glob, mock_exists):
        mock_exists.return_value = True
        mock_glob.return_value = [
            Path(f"{LLM_SERVICES_DIR}/{OPENROUTER_SERVICE_FILE}"),
            Path(f"{LLM_SERVICES_DIR}/{ANTHROPIC_SERVICE_FILE}"),
        ]

        services = ServiceDiscovery.discover_llm_services()

        assert "openrouter" in services
        assert "anthropic" in services
        assert len(services["openrouter"]) > 0
        assert len(services["anthropic"]) > 0

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_discover_llm_services_skip_base_class(self, mock_glob, mock_exists):
        mock_exists.return_value = True
        mock_glob.return_value = [
            Path(f"{LLM_SERVICES_DIR}/{LLM_SERVICE_BASE_FILE}"),
            Path(f"{LLM_SERVICES_DIR}/{OPENROUTER_SERVICE_FILE}"),
        ]

        services = ServiceDiscovery.discover_llm_services()

        assert "openrouter" in services
        assert len(services) == 1

    def test_get_provider_name_success(self):
        class TestService(LlmService):
            @property
            def model_name(self) -> str:
                return TEST_MODEL_NAME

            @property
            def provider(self) -> LlmProvider:
                return LlmProvider.ANTHROPIC

            def _call_api(self, prompt: str, max_tokens: int) -> str:
                return ""

        result = ServiceDiscovery._get_provider_name(TestService)
        assert result == "anthropic"

    def test_get_provider_name_fallback(self):
        class AnthropicTestService:
            pass

        result = ServiceDiscovery._get_provider_name(AnthropicTestService)
        assert result == "anthropic"

    def test_get_provider_name_unknown(self):
        class UnknownService:
            pass

        result = ServiceDiscovery._get_provider_name(UnknownService)
        assert result is None

    @pytest.mark.parametrize(
        "class_name,expected",
        [
            ("OpenRouterClaudeOpusLlmService", "claude-opus"),
            ("AnthropicClaude3HaikuLlmService", "claude-3-haiku"),
            ("OpenRouterGpt4LlmService", "gpt-4"),
            ("AnthropicClaude35SonnetLlmService", "claude-35-sonnet"),
            ("SimpleLlmService", "simple"),
        ],
    )
    def test_extract_model_name(self, class_name, expected):
        result = ServiceDiscovery._extract_model_name(class_name)
        assert result == expected


class TestGeneratorFactory:

    @patch.object(ServiceDiscovery, "discover_wordlist_generators")
    def test_factory_initialization_and_discovery(self, mock_discover):
        mock_discover.return_value = {
            "password": PasswordWordlistGenerator,
            "subdomain": SubdomainWordlistGenerator,
        }

        factory = GeneratorFactory()
        mock_discover.assert_called_once()

        available = factory.available_types
        assert "password" in available
        assert "subdomain" in available
        assert len(available) == 2

    @patch.object(ServiceDiscovery, "discover_wordlist_generators")
    def test_create_success(self, mock_discover):
        mock_discover.return_value = {"password": PasswordWordlistGenerator}

        factory = GeneratorFactory()
        generator = factory.create("password")

        assert isinstance(generator, PasswordWordlistGenerator)

    @patch.object(ServiceDiscovery, "discover_wordlist_generators")
    def test_create_with_output_file(self, mock_discover):
        mock_discover.return_value = {"password": PasswordWordlistGenerator}

        factory = GeneratorFactory()
        output_file = Path("/custom/output.txt")
        generator = factory.create("password", output_file)

        assert generator.output_file == output_file

    @patch.object(ServiceDiscovery, "discover_wordlist_generators")
    def test_create_unknown_type(self, mock_discover):
        mock_discover.return_value = {}

        factory = GeneratorFactory()
        generator = factory.create("unknown")

        assert generator is None

    @patch.object(ServiceDiscovery, "discover_wordlist_generators")
    def test_create_exception(self, mock_discover):
        class BrokenGenerator:
            def __init__(self, *args):
                raise ValueError("Broken")

        mock_discover.return_value = {"broken": BrokenGenerator}

        factory = GeneratorFactory()
        with patch("rich.console.Console.print") as mock_print:
            generator = factory.create("broken")

        assert generator is None
        mock_print.assert_called_once()
        assert "Failed to create" in str(mock_print.call_args)

    @patch.object(ServiceDiscovery, "discover_wordlist_generators")
    def test_get_description_behavior(self, mock_discover):
        mock_discover.return_value = {
            "password": PasswordWordlistGenerator,
            "subdomain": SubdomainWordlistGenerator,
        }

        factory = GeneratorFactory()

        password_desc = factory.get_description("password")
        assert "password" in password_desc.lower()

        subdomain_desc = factory.get_description("subdomain")
        assert "subdomain" in subdomain_desc.lower()

        unknown_desc = factory.get_description("unknown")
        assert "unknown" in unknown_desc.lower()


class TestLlmServiceFactory:

    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.get_api_key.return_value = TEST_API_KEY
        config.get_preferences.return_value = {}
        return config

    @pytest.fixture
    def mock_service_class(self):
        class MockService(LlmService):
            @property
            def model_name(self) -> str:
                return TEST_MODEL_NAME

            @property
            def provider(self) -> LlmProvider:
                return LlmProvider.ANTHROPIC

            def _call_api(self, prompt: str, max_tokens: int) -> str:
                return "test response"

        return MockService

    @patch.object(ServiceDiscovery, "discover_llm_services")
    def test_initialization(self, mock_discover, mock_config):
        mock_services = {"anthropic": {"claude": Mock()}}
        mock_discover.return_value = mock_services

        factory = LlmServiceFactory(mock_config)
        assert factory._config == mock_config
        assert factory._services == mock_services

    @patch.object(ServiceDiscovery, "discover_llm_services")
    def test_available_providers(self, mock_discover, mock_config):
        mock_discover.return_value = {
            "anthropic": {"claude": Mock()},
            "openrouter": {"gpt4": Mock()},
        }

        factory = LlmServiceFactory(mock_config)
        assert factory.available_providers == ["anthropic", "openrouter"]

    @patch.object(ServiceDiscovery, "discover_llm_services")
    def test_get_available_models(self, mock_discover, mock_config):
        mock_discover.return_value = {
            "anthropic": {
                "claude-3-opus": Mock(),
                "claude-3-sonnet": Mock(),
            }
        }

        factory = LlmServiceFactory(mock_config)
        models = factory.get_available_models("anthropic")
        assert models == ["claude-3-opus", "claude-3-sonnet"]

    @patch.object(ServiceDiscovery, "discover_llm_services")
    def test_create_success(self, mock_discover, mock_config, mock_service_class):
        mock_discover.return_value = {"anthropic": {"claude": mock_service_class}}

        factory = LlmServiceFactory(mock_config)
        service = factory.create("anthropic", "claude")

        assert isinstance(service, mock_service_class)

    @patch.object(ServiceDiscovery, "discover_llm_services")
    def test_create_unknown_provider(self, mock_discover, mock_config):
        mock_discover.return_value = {}

        factory = LlmServiceFactory(mock_config)
        service = factory.create("unknown")

        assert service is None

    @patch.object(ServiceDiscovery, "discover_llm_services")
    def test_create_no_api_key(self, mock_discover, mock_config, mock_service_class):
        mock_discover.return_value = {"anthropic": {"claude": mock_service_class}}
        mock_config.get_api_key.return_value = None

        factory = LlmServiceFactory(mock_config)
        with patch("rich.console.Console.print") as mock_print:
            service = factory.create("anthropic")

        assert service is None
        mock_print.assert_called_once()
        assert "No API key configured" in str(mock_print.call_args)

    @patch.object(ServiceDiscovery, "discover_llm_services")
    def test_create_with_default_model(
        self, mock_discover, mock_config, mock_service_class
    ):
        mock_discover.return_value = {
            "anthropic": {
                "claude-opus": mock_service_class,
                "claude-sonnet": Mock(),
            }
        }
        mock_config.get_preferences.return_value = {
            "default_anthropic_model": "claude-opus"
        }

        factory = LlmServiceFactory(mock_config)
        service = factory.create("anthropic")  # No model specified

        assert isinstance(service, mock_service_class)

    @patch.object(ServiceDiscovery, "discover_llm_services")
    def test_create_value_error(self, mock_discover, mock_config):
        class BrokenService:
            def __init__(self, config):
                raise ValueError("Invalid config")

        mock_discover.return_value = {"broken": {"model": BrokenService}}

        factory = LlmServiceFactory(mock_config)

        service = factory.create("broken", "model")
        assert service is None

    def test_determine_model_requested(self, mock_config):
        factory = LlmServiceFactory(mock_config)
        available = {"model1": Mock(), "model2": Mock()}

        result = factory._determine_model("provider", "model1", available)
        assert result == "model1"

    def test_determine_model_default_preference(self, mock_config):
        mock_config.get_preferences.return_value = {"default_provider_model": "model2"}

        factory = LlmServiceFactory(mock_config)
        available = {"model1": Mock(), "model2": Mock()}

        result = factory._determine_model("provider", None, available)
        assert result == "model2"

    def test_determine_model_first_available(self, mock_config):
        factory = LlmServiceFactory(mock_config)
        available = {"model1": Mock(), "model2": Mock()}

        result = factory._determine_model("provider", None, available)
        assert result == "model1"

    def test_determine_model_none_available(self, mock_config):
        factory = LlmServiceFactory(mock_config)
        available = {}

        result = factory._determine_model("provider", None, available)
        assert result is None
