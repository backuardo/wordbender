import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv, set_key

from llm_services.llm_service import LlmProvider


class Config:
    """Local configuration management using .env files."""

    def __init__(self, env_file: Optional[Path] = None):
        self._env_file = env_file or self._find_env_file()
        self._config_file = Path.home() / ".wordbender" / "config.json"
        self._load_env()
        self._ensure_config_dir()
        self._check_first_run()

    @staticmethod
    def _find_env_file() -> Path:
        """Find .env file in current directory or home directory."""
        # Check current directory first
        local_env = Path(".env")
        if local_env.exists():
            return local_env

        # Check home directory
        home_env = Path.home() / ".wordbender" / ".env"
        if home_env.exists():
            return home_env

        # Default to current directory
        return local_env

    def _check_first_run(self) -> None:
        """Check if this is first run and create example if needed."""
        if not self._env_file.exists() and not Path(".env.example").exists():
            self.create_example_env()
            print("\nNo .env file found. Created .env.example")
            print("Please copy it to .env and add your API keys")

    def _load_env(self) -> None:
        """Load environment variables from .env file."""
        if self._env_file.exists():
            load_dotenv(self._env_file)

    def _ensure_config_dir(self) -> None:
        """Create config directory for preferences."""
        self._config_file.parent.mkdir(parents=True, exist_ok=True)

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key from environment variables."""
        # Get provider enum
        provider_enum = LlmProvider.get_by_name(provider)
        if not provider_enum:
            return None

        # Check if provider needs API key
        if not provider_enum.requires_api_key:
            return None

        # At this point, env_var cannot be None due to requires_api_key check
        env_var = provider_enum.env_var
        if not env_var:  # This should never happen
            return None

        # Check primary env var
        value = os.getenv(env_var)
        if value:
            return value

        # Check with WORDBENDER_ prefix for namespace safety
        prefixed_var = f"WORDBENDER_{env_var}"
        return os.getenv(prefixed_var)

    def set_api_key(self, provider: str, api_key: str) -> None:
        """Set API key in .env file."""
        provider_enum = LlmProvider.get_by_name(provider)
        if not provider_enum:
            raise ValueError(f"Unknown provider: {provider}")

        if not provider_enum.requires_api_key:
            raise ValueError(f"Provider {provider} does not use API keys")

        env_var = provider_enum.env_var
        if not env_var:  # This should never happen due to requires_api_key check
            raise ValueError(f"Provider {provider} has no environment variable defined")

        # Create .env if it doesn't exist
        if not self._env_file.exists():
            self._env_file.touch()
            print(f"Created {self._env_file}")

        # Update .env file
        set_key(str(self._env_file), env_var, api_key)

        # Also set in current environment
        os.environ[env_var] = api_key

        print(f"Set {env_var} in {self._env_file}")

    def list_configured_providers(self) -> Dict[str, bool]:
        """List providers and their configuration status."""
        return {
            provider.internal_name: self.get_api_key(provider.internal_name) is not None
            for provider in LlmProvider.requiring_api_keys()
        }

    def get_available_providers(self) -> List[str]:
        """Get list of all available provider names."""
        return [p.internal_name for p in LlmProvider]

    def get_preferences(self) -> Dict[str, Any]:
        """Load user preferences from JSON config file."""
        if not self._config_file.exists():
            return self._get_default_preferences()

        try:
            with open(self._config_file, "r") as f:
                return json.load(f)
        except Exception:
            return self._get_default_preferences()

    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        prefs = self.get_preferences()
        prefs[key] = value

        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_file, "w") as f:
            json.dump(prefs, f, indent=2)

    def reset_preferences(self) -> None:
        """Reset preferences to defaults."""
        defaults = self._get_default_preferences()
        self._config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_file, "w") as f:
            json.dump(defaults, f, indent=2)

    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default preferences."""
        return {
            "default_provider": "openrouter",
            "default_wordlist_type": "password",
            "default_wordlist_length": 100,
            "output_directory": str(Path.cwd()),
            "append_by_default": False,
        }

    def create_example_env(self) -> None:
        """Create an example .env file with all providers that need keys."""
        lines = ["# Wordbender API keys", "#", "# Add your API keys below:", ""]

        for provider in LlmProvider.requiring_api_keys():
            lines.append(f"# {provider.display_name}")
            if provider.env_var:
                lines.append(f"{provider.env_var}=")
            lines.append("")

        lines.extend(
            [
                "# Optional: default model preferences",
                "# DEFAULT_PROVIDER=openrouter",
                "# DEFAULT_MODEL=anthropic/claude-3-opus",
            ]
        )

        example_file = self._env_file.with_suffix(".env.example")
        with open(example_file, "w") as f:
            f.write("\n".join(lines))

        print(f"Created {example_file}")
        print(f"Copy to {self._env_file} and add your API keys")

    def check_api_keys(self) -> bool:
        """Check if at least one API key is configured."""
        status = self.list_configured_providers()

        if not any(status.values()):
            print("\nNo API keys configured!")
            print("Please add at least one API key to your .env file:")

            for provider in LlmProvider.requiring_api_keys():
                if provider.env_var:
                    print(f"    {provider.env_var}=your-key-here")

            return False

        print("\nConfigured providers:")
        for provider_name, configured in status.items():
            if configured:
                provider = LlmProvider.get_by_name(provider_name)
                if provider:
                    print(f"    - {provider.display_name}")

        return True

    def select_provider(self, provider_name: Optional[str] = None) -> Optional[str]:
        """Select a provider, either specified or from configured ones."""
        if provider_name:
            # Validate the specified provider
            provider = LlmProvider.get_by_name(provider_name)
            if not provider:
                print(f"Unknown provider: {provider_name}")
                print(
                    f"Available providers: {
                        ', '.join(p.internal_name for p in LlmProvider)
                    }"
                )
                return None

            if provider.requires_api_key and not self.get_api_key(provider_name):
                print(f"No API key configured for {provider.display_name}")
                if provider.env_var:
                    print(f"Please set {provider.env_var} in your .env file")
                return None

            return provider_name

        # No provider specified, use default or prompt
        configured = self.list_configured_providers()
        available = [name for name, has_key in configured.items() if has_key]

        if not available:
            print("No providers configured with API keys")
            return None

        # Check default preference
        prefs = self.get_preferences()
        default = prefs.get("default_provider")

        if default in available:
            return default

        # Return first available
        return available[0]
