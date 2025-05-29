from pathlib import Path
from typing import Optional

from config.config import Config
from llm_services.llm_service import LlmProvider


def setup_config() -> Config:
    """Set up configuration, checking multiple locations."""
    # Check for .env in current directory first
    local_env = Path(".env")

    # Then check in home directory
    home_env = Path.home() / ".wordbender" / ".env"

    if local_env.exists():
        return Config(local_env)
    elif home_env.exists():
        return Config(home_env)
    else:
        # Create example and prompt user
        config = Config()
        if not local_env.exists() and not Path(".env.example").exists():
            config.create_example_env()
            print("\nNo .env file found. Created .env.example")
            print("Please copy it to .env and add your API keys")
        return config


def check_api_keys(config: Config) -> bool:
    """Check if at least one API key is configured."""
    status = config.list_configured_providers()

    if not any(status.values()):
        print("\nNo API keys configured!")
        print("Please add at least one API key to your .env file:")

        for provider in LlmProvider.requiring_api_keys():
            if provider.env_var:
                print(f"  {provider.env_var}=your-key-here")

        return False

    print("\nConfigured providers:")
    for provider_name, configured in status.items():
        if configured:
            provider = LlmProvider.get_by_name(provider_name)
            if provider:
                print(f"  - {provider.display_name}")

    return True


def select_provider(
    config: Config, provider_name: Optional[str] = None
) -> Optional[str]:
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

        if provider.requires_api_key and not config.get_api_key(provider_name):
            print(f"No API key configured for {provider.display_name}")
            if provider.env_var:
                print(f"Please set {provider.env_var} in your .env file")
            return None

        return provider_name

    # No provider specified, use default or prompt
    configured = config.list_configured_providers()
    available = [name for name, has_key in configured.items() if has_key]

    if not available:
        print("No providers configured with API keys")
        return None

    # Check default preference
    prefs = config.get_preferences()
    default = prefs.get("default_provider")

    if default in available:
        return default

    # Return first available
    return available[0]
