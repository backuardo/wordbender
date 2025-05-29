from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class LlmProvider(Enum):
    """Enumeration of all LLM providers."""

    OPEN_AI = auto()
    ANTHROPIC = auto()
    LOCAL = auto()
    GOOGLE = auto()
    OPEN_ROUTER = auto()
    CUSTOM = auto()


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
        # Estimate tokens needed (rough heuristic: 1.5 tokens per word + prompt)
        estimated_tokens = int(expected_count * 1.5) + 100

        raw_response = self._call_api(prompt, estimated_tokens)
        return self._parse_word_list(raw_response)

    def _parse_word_list(self, response: str) -> List[str]:
        """Parse the LLM response into a list of words."""
        # Split by newlines and filter out empty lines
        words = [line.strip() for line in response.strip().split("\n") if line.strip()]

        # Remove common LLM artifacts
        filtered_words = []
        for word in words:
            # Skip lines that look like explanations or categories
            if any(char in word for char in [":", "(", ")", "[", "]", "->"]):
                continue
            # Skip lines with multiple words (unless hyphenated)
            if " " in word and "-" not in word:
                continue
            filtered_words.append(word)

        return filtered_words
