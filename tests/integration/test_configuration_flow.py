import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cli.factories import LlmServiceFactory
from config import Config

TEST_OPENROUTER_KEY = "test-openrouter-key"
TEST_ANTHROPIC_KEY = "test-anthropic-key"


class TestConfigurationFlow:

    @pytest.fixture
    def temp_config_env(self, tmp_path, monkeypatch):
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        work_dir = tmp_path / "work"
        work_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))
        monkeypatch.chdir(work_dir)

        return {
            "home_dir": home_dir,
            "work_dir": work_dir,
            "config_dir": home_dir / ".wordbender",
            "env_file": work_dir / ".env",
        }

    @pytest.mark.integration
    def test_first_run_setup_flow(self, temp_config_env):
        with patch("builtins.print") as mock_print:
            config = Config()

        example_file = temp_config_env["work_dir"] / ".env.example"
        assert example_file.exists()

        example_content = example_file.read_text()
        assert "OPENROUTER_API_KEY=" in example_content
        assert "ANTHROPIC_API_KEY=" in example_content

        mock_print.assert_any_call("\nNo .env file found. Created .env.example")

    @pytest.mark.integration
    def test_api_key_configuration_flow(self, temp_config_env):
        config = Config()

        assert not config.check_api_keys()

        config.set_api_key("openrouter", TEST_OPENROUTER_KEY)
        config.set_api_key("anthropic", TEST_ANTHROPIC_KEY)

        assert config.get_api_key("openrouter") == TEST_OPENROUTER_KEY
        assert config.get_api_key("anthropic") == TEST_ANTHROPIC_KEY
        assert config.check_api_keys()

        # Note: python-dotenv's set_key writes values with single quotes
        env_content = temp_config_env["env_file"].read_text()
        assert f"OPENROUTER_API_KEY='{TEST_OPENROUTER_KEY}'" in env_content
        assert f"ANTHROPIC_API_KEY='{TEST_ANTHROPIC_KEY}'" in env_content

    @pytest.mark.integration
    def test_provider_selection_flow(self, temp_config_env, monkeypatch):
        for provider in ["OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
            monkeypatch.delenv(provider, raising=False)
            monkeypatch.delenv(f"WORDBENDER_{provider}", raising=False)

        config = Config()

        with patch("builtins.print"):
            assert config.select_provider() is None

        with patch("builtins.print"):
            config.set_api_key("anthropic", "test-key")
            assert config.select_provider() == "anthropic"

            config.set_api_key("openrouter", "test-key-2")

        config.set_preference("default_provider", "openrouter")
        assert config.select_provider() == "openrouter"

        assert config.select_provider("anthropic") == "anthropic"

        with patch("builtins.print"):
            assert config.select_provider("unknown") is None

    @pytest.mark.integration
    def test_preference_persistence_flow(self, temp_config_env):
        config1 = Config()
        config1.set_preference("default_wordlist_type", "subdomain")
        config1.set_preference("default_wordlist_length", 200)
        config1.set_preference("custom_setting", "test_value")

        config2 = Config()
        prefs = config2.get_preferences()

        assert prefs["default_wordlist_type"] == "subdomain"
        assert prefs["default_wordlist_length"] == 200
        assert prefs["custom_setting"] == "test_value"

    @pytest.mark.integration
    def test_environment_precedence_flow(self, temp_config_env, monkeypatch):
        config = Config()

        config.set_api_key("openrouter", "env-file-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "env-var-key")
        assert config.get_api_key("openrouter") == "env-var-key"

        monkeypatch.delenv("OPENROUTER_API_KEY")
        monkeypatch.setenv("WORDBENDER_OPENROUTER_API_KEY", "prefixed-key")

        assert config.get_api_key("openrouter") == "prefixed-key"

    @pytest.mark.integration
    def test_service_creation_with_config(self, temp_config_env):
        # Set up config with API key
        config = Config()
        config.set_api_key("openrouter", "test-api-key")

        # Create factory and service
        factory = LlmServiceFactory(config)

        # Mock the service discovery to avoid import issues
        with patch.object(
            factory,
            "_services",
            {"openrouter": {"test-model": Mock(return_value=Mock())}},
        ):
            service = factory.create("openrouter", "test-model")
            assert service is not None

    @pytest.mark.integration
    def test_config_error_recovery_flow(self, temp_config_env):
        config = Config()

        # Create corrupted config file
        config_file = temp_config_env["config_dir"] / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        config_file.write_text("invalid json{")

        # Should fall back to defaults
        with patch("rich.console.Console.print"):
            prefs = config.get_preferences()

        assert prefs == config._get_default_preferences()

        # Should be able to set new preferences
        config.set_preference("test", "value")

        # Config file should be fixed
        new_prefs = json.loads(config_file.read_text())
        assert new_prefs["test"] == "value"

    @pytest.mark.integration
    def test_multi_location_env_flow(self, temp_config_env, monkeypatch):
        for provider in ["OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"]:
            monkeypatch.delenv(provider, raising=False)
            monkeypatch.delenv(f"WORDBENDER_{provider}", raising=False)

        home_env = temp_config_env["config_dir"] / ".env"
        home_env.parent.mkdir(parents=True, exist_ok=True)
        home_env.write_text("ANTHROPIC_API_KEY=home-key\n")

        local_env = temp_config_env["work_dir"] / ".env"
        local_env.write_text("OPENROUTER_API_KEY=local-key\n")

        config = Config()
        # Config stores relative path, not absolute
        assert config._env_file == Path(".env")
        assert config.get_api_key("openrouter") == "local-key"

        local_env.unlink()
        config2 = Config()
        # When local doesn't exist, it uses the home directory one
        assert config2._env_file == home_env
        assert config2.get_api_key("anthropic") == "home-key"

    @pytest.mark.integration
    def test_quoted_api_key_rejection(self, temp_config_env):
        config = Config()

        with pytest.raises(ValueError, match="should not be quoted"):
            config.set_api_key("openrouter", '"quoted-key"')

        with pytest.raises(ValueError, match="should not be quoted"):
            config.set_api_key("openrouter", "'quoted-key'")

    @pytest.mark.integration
    @patch("builtins.print")
    def test_provider_listing_flow(self, mock_print, temp_config_env):
        config = Config()

        config.set_api_key("openrouter", "key1")
        config.set_api_key("anthropic", "key2")
        config.check_api_keys()

        mock_print.assert_any_call("\nConfigured providers:")
        mock_print.assert_any_call("    - OpenRouter")
        mock_print.assert_any_call("    - Anthropic")
