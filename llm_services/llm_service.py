from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class LlmProvider(Enum):
    """Enumeration of all LLM providers."""

    # Format: (internal_name, display_name, env_var_name)
    OPEN_AI = ("openai", "OpenAI", "OPENAI_API_KEY")
    ANTHROPIC = ("anthropic", "Anthropic", "ANTHROPIC_API_KEY")
    LOCAL = ("local", "Local", None)
    OPEN_ROUTER = ("openrouter", "OpenRouter", "OPENROUTER_API_KEY")
    CUSTOM = ("custom", "Custom", "CUSTOM_API_KEY")

    def __init__(self, internal_name: str, display_name: str, env_var: Optional[str]):
        self.internal_name = internal_name
        self.display_name = display_name
        self.env_var = env_var

    @classmethod
    def get_by_name(cls, name: str) -> Optional["LlmProvider"]:
        """Get provider by internal name (case-sensitive)."""
        name_lower = name.lower()
        for provider in cls:
            if provider.internal_name == name_lower:
                return provider
        return None

    @classmethod
    def requiring_api_keys(cls) -> List["LlmProvider"]:
        """Get all providers that require API keys."""
        return [p for p in cls if p.env_var is not None]

    @property
    def requires_api_key(self) -> bool:
        """Check if this provider requires an API key."""
        return self.env_var is not None


@dataclass
class LlmConfig:
    """Configuration for an LLM service."""

    api_key: Optional[str] = None
    api_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    additional_params: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}


class LlmService(ABC):
    """Abstract base class for LLM services."""

    def __init__(self, config: LlmConfig):
        self._config = config
        self._validate_config()

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier."""
        pass

    @property
    @abstractmethod
    def provider(self) -> LlmProvider:
        """Return the LLM provider."""
        pass

    @property
    def requires_api_key(self) -> bool:
        """Whether this service requires an API key."""
        return True

    def _validate_config(self) -> None:
        """Validate the configuration for this service."""
        if self.requires_api_key and not self._config.api_key:
            raise ValueError(f"{self.__class__.__name__} requires an API key")

    @abstractmethod
    def _call_api(self, prompt: str, max_tokens: int) -> str:
        """Make the API call to the LLM."""
        pass

    def generate_words(self, prompt: str, expected_count: int) -> List[str]:
        """Generate a list of words from the LLM."""
        prompt_tokens = len(prompt.split()) * 1.5
        output_tokens = expected_count * 2
        estimated_tokens = int(prompt_tokens + output_tokens) + 50
        max_allowed_tokens = 4000
        estimated_tokens = min(estimated_tokens, max_allowed_tokens)

        raw_response = self._call_api(prompt, estimated_tokens)
        return self._parse_word_list(raw_response)

    def _parse_word_list(self, response: str) -> List[str]:
        """Parse the LLM response into a list of words."""
        words = [line.strip() for line in response.strip().split("\n") if line.strip()]
        filtered_words = []
        for word in words:
            if any(char in word for char in [":", "(", ")", "[", "]", "->"]):
                continue
            if " " in word and "-" not in word:
                continue
            filtered_words.append(word)

        return filtered_words
