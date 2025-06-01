import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from config import Config
from llm_services.llm_service import LlmProvider


class TestConfig:

    @pytest.fixture
    def temp_env_file(self, tmp_path):
        env_file = tmp_path / ".env"
        return env_file

    @pytest.fixture
    def config(self, temp_env_file, monkeypatch):
        mock_home = temp_env_file.parent / "home"
        mock_home.mkdir()
        monkeypatch.setenv("HOME", str(mock_home))
        monkeypatch.chdir(temp_env_file.parent)
        return Config(env_file=temp_env_file)

    def test_env_file_discovery_behavior(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        home_dir = tmp_path / "home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))

        local_env = tmp_path / ".env"
        local_env.touch()
        result = Config._find_env_file()
        assert result == Path(".env")

        local_env.unlink()
        home_env = home_dir / ".wordbender" / ".env"
        home_env.parent.mkdir(parents=True)
        home_env.touch()
        result = Config._find_env_file()
        assert result == home_env

        home_env.unlink()
        result = Config._find_env_file()
        assert result == Path(".env")

    @patch("builtins.print")
    def test_check_first_run_creates_example(self, mock_print, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        example_file = tmp_path / ".env.example"
        if example_file.exists():
            example_file.unlink()

        Config(env_file=tmp_path / ".env")

        assert example_file.exists()
        assert mock_print.call_count >= 1
        mock_print.assert_any_call("\nNo .env file found. Created .env.example")

    def test_load_env(self, temp_env_file, monkeypatch):
        temp_env_file.write_text("TEST_VAR=test_value\n")
        Config(env_file=temp_env_file)

        assert os.getenv("TEST_VAR") == "test_value"

    def test_get_api_key_exists(self, config, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        assert config.get_api_key("openrouter") == "test-key"

    def test_get_api_key_prefixed(self, config, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.setenv("WORDBENDER_OPENROUTER_API_KEY", "prefixed-key")
        assert config.get_api_key("openrouter") == "prefixed-key"

    def test_get_api_key_not_exists(self, config, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        monkeypatch.delenv("WORDBENDER_OPENROUTER_API_KEY", raising=False)
        assert config.get_api_key("openrouter") is None

    def test_get_api_key_unknown_provider(self, config):
        assert config.get_api_key("unknown") is None

    def test_get_api_key_no_key_required(self, config):
        assert config.get_api_key("local") is None

    def test_set_api_key_valid(self, config, temp_env_file):
        config.set_api_key("openrouter", "new-key")

        assert temp_env_file.exists()
        content = temp_env_file.read_text()
        assert "OPENROUTER_API_KEY" in content
        assert "new-key" in content
        assert os.getenv("OPENROUTER_API_KEY") == "new-key"

    def test_set_api_key_creates_env_file(self, config, temp_env_file):
        assert not temp_env_file.exists()
        config.set_api_key("openrouter", "new-key")
        assert temp_env_file.exists()

    def test_set_api_key_unknown_provider(self, config):
        with pytest.raises(ValueError, match="Unknown provider"):
            config.set_api_key("unknown", "key")

    def test_set_api_key_no_key_required(self, config):
        with pytest.raises(ValueError, match="does not use API keys"):
            config.set_api_key("local", "key")

    def test_set_api_key_quoted(self, config):
        with pytest.raises(ValueError, match="should not be quoted"):
            config.set_api_key("openrouter", '"quoted-key"')

    def test_list_configured_providers(self, config, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key1")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key2")

        status = config.list_configured_providers()
        assert status["openrouter"] is True
        assert status["anthropic"] is True
        assert status["openai"] is False

    def test_get_available_providers(self, config):
        providers = config.get_available_providers()
        assert "openrouter" in providers
        assert "anthropic" in providers
        assert "local" in providers

    def test_preferences_behavior(self, config):
        prefs = config.get_preferences()
        assert "default_provider" in prefs
        assert "default_wordlist_type" in prefs
        assert isinstance(prefs["default_wordlist_length"], int)
        assert prefs["default_wordlist_length"] > 0

    def test_preferences_persistence(self, config):
        config.set_preference("custom_setting", "test_value")
        config.set_preference("default_provider", "anthropic")

        new_prefs = config.get_preferences()
        assert new_prefs["custom_setting"] == "test_value"
        assert new_prefs["default_provider"] == "anthropic"

    def test_get_preferences_invalid_json(self, config):
        config._config_file.parent.mkdir(parents=True, exist_ok=True)
        config._config_file.write_text("invalid json")

        with patch("rich.console.Console.print"):
            prefs = config.get_preferences()
        assert prefs == config._get_default_preferences()

    def test_set_preference(self, config):
        config.set_preference("custom_key", "custom_value")

        prefs = config.get_preferences()
        assert prefs["custom_key"] == "custom_value"

        saved_prefs = json.loads(config._config_file.read_text())
        assert saved_prefs["custom_key"] == "custom_value"

    def test_reset_preferences(self, config):
        config.set_preference("custom", "value")
        config.reset_preferences()

        prefs = config.get_preferences()
        assert prefs == config._get_default_preferences()
        assert "custom" not in prefs

    def test_create_example_env(self, config, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        config._env_file = tmp_path / ".env"
        config.create_example_env()

        example_file = tmp_path / ".env.example"
        assert example_file.exists()
        content = example_file.read_text()

        for provider in LlmProvider.requiring_api_keys():
            if provider.env_var:
                assert provider.env_var in content

    @patch("builtins.print")
    def test_check_api_keys_none_configured(self, mock_print, config, monkeypatch):
        for provider in LlmProvider.requiring_api_keys():
            if provider.env_var:
                monkeypatch.delenv(provider.env_var, raising=False)
                monkeypatch.delenv(f"WORDBENDER_{provider.env_var}", raising=False)

        result = config.check_api_keys()
        assert result is False
        mock_print.assert_any_call("\nNo API keys configured!")

    @patch("builtins.print")
    def test_check_api_keys_some_configured(self, mock_print, config, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key1")

        result = config.check_api_keys()
        assert result is True
        mock_print.assert_any_call("\nConfigured providers:")
        mock_print.assert_any_call("    - OpenRouter")

    def test_select_provider_specified_valid(self, config, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key")
        result = config.select_provider("anthropic")
        assert result == "anthropic"

    @patch("builtins.print")
    def test_select_provider_specified_unknown(self, mock_print, config):
        result = config.select_provider("unknown")
        assert result is None
        mock_print.assert_any_call("Unknown provider: unknown")

    @patch("builtins.print")
    def test_select_provider_specified_no_key(self, mock_print, config, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("WORDBENDER_ANTHROPIC_API_KEY", raising=False)

        result = config.select_provider("anthropic")
        assert result is None
        mock_print.assert_any_call("No API key configured for Anthropic")

    def test_select_provider_auto_default(self, config, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "key1")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "key2")
        config.set_preference("default_provider", "anthropic")

        result = config.select_provider()
        assert result == "anthropic"

    def test_select_provider_auto_first_available(self, config, monkeypatch):
        for provider in LlmProvider.requiring_api_keys():
            if provider.env_var:
                monkeypatch.delenv(provider.env_var, raising=False)

        monkeypatch.setenv("ANTHROPIC_API_KEY", "key")

        result = config.select_provider()
        assert result == "anthropic"

    @patch("builtins.print")
    def test_select_provider_none_configured(self, mock_print, config, monkeypatch):
        for provider in LlmProvider.requiring_api_keys():
            if provider.env_var:
                monkeypatch.delenv(provider.env_var, raising=False)
                monkeypatch.delenv(f"WORDBENDER_{provider.env_var}", raising=False)

        result = config.select_provider()
        assert result is None
        mock_print.assert_any_call("No providers configured with API keys")
