from abc import ABC, abstractmethod
from pathlib import Path


class WordlistGenerator(ABC):
    """Abstract base class for generating targeted wordlists."""

    def __init__(self, output_file: Path | None = None):
        self._seed_words: list[str] = []
        self._generated_words: list[str] = []
        self._output_file = output_file or self._get_default_output_path()
        self._wordlist_length = 100
        self._additional_instructions: str | None = None

    @property
    def seed_words(self) -> list[str]:
        """Get the current seed words."""
        return self._seed_words.copy()

    @property
    def generated_words(self) -> list[str]:
        """Get the generated words."""
        return self._generated_words.copy()

    @property
    def wordlist_length(self) -> int:
        """Get the target wordlist length."""
        return self._wordlist_length

    @wordlist_length.setter
    def wordlist_length(self, value: int) -> None:
        """Set the target wordlist length."""
        if value < 1:
            raise ValueError("Wordlist length must be positive")
        self._wordlist_length = value

    @property
    def output_file(self) -> Path:
        """Get the output file path."""
        return self._output_file

    @output_file.setter
    def output_file(self, path: Path) -> None:
        """Set the output file path."""
        self._output_file = path

    @property
    def additional_instructions(self) -> str | None:
        """Get additional instructions for the LLM."""
        return self._additional_instructions

    @additional_instructions.setter
    def additional_instructions(self, value: str | None) -> None:
        """Set additional instructions for the LLM."""
        self._additional_instructions = value

    @abstractmethod
    def _get_default_output_path(self) -> Path:
        """Return the default output file path for this generator type."""
        pass

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Return the system prompt specific to this generator type."""
        pass

    @abstractmethod
    def _validate_word(self, word: str) -> bool:
        """Validate a single word according to generator-specific rules."""
        pass

    @abstractmethod
    def get_seed_hints(self) -> str:
        """Return hints about what seed words to provide."""
        pass

    @abstractmethod
    def get_usage_instructions(self) -> str:
        """Return instructions for using the generated wordlist."""
        pass

    def add_seed_words(self, *words: str) -> None:
        """Add seed words to the generator."""
        # Allow any non-empty seed words - they're just context for the LLM
        valid_words = [word.strip() for word in words if word.strip()]
        if not valid_words:
            raise ValueError("No valid seed words provided")
        self._seed_words.extend(valid_words)

    def clear_seed_words(self) -> None:
        """Clear all seed words."""
        self._seed_words.clear()

    def build_prompt(self) -> str:
        """Build the complete prompt for the LLM."""
        if not self._seed_words:
            raise ValueError("No seed words provided")

        base_prompt = self._get_system_prompt().format(
            seed_words=", ".join(self._seed_words),
            wordlist_length=self._wordlist_length,
        )

        if self._additional_instructions:
            return (
                f"{base_prompt}\n\n"
                f"Additional instructions: {self._additional_instructions}"
            )

        return base_prompt

    def generate(self, llm_service) -> list[str]:
        """Generate the wordlist using the provided LLM service."""
        prompt = self.build_prompt()

        try:
            raw_words = llm_service.generate_words(prompt, self._wordlist_length)
        except Exception as e:
            raise RuntimeError(f"Failed to generate words from LLM: {e}") from e

        if not raw_words:
            raise ValueError("LLM returned empty response")

        self._generated_words = self._process_generated_words(raw_words)

        if not self._generated_words:
            raise ValueError("No valid words generated after processing")

        return self.generated_words

    def _process_generated_words(self, words: list[str]) -> list[str]:
        """Process and validate generated words."""
        seen = set()
        processed = []
        invalid_count = 0

        for word in words:
            word = word.strip()
            if not word:
                continue

            if word in seen:
                continue

            if self._validate_word(word):
                seen.add(word)
                processed.append(word)
            else:
                invalid_count += 1

        # Log validation summary
        if invalid_count > 0:
            print(f"Warning: {invalid_count} words failed validation")

        return processed

    def save(self, path: Path | None = None, append: bool = False) -> None:
        """Save the generated wordlist to a file."""
        if not self._generated_words:
            raise ValueError("No words have been generated")

        output_path = path or self._output_file

        # Ensure parent directory exists with error handling
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise OSError(
                f"Failed to create directory {output_path.parent}: {e}"
            ) from e

        mode = "a" if append else "w"
        try:
            with output_path.open(mode, encoding="utf-8") as f:
                for word in self._generated_words:
                    f.write(f"{word}\n")
        except OSError as e:
            raise OSError(f"Failed to write to file {output_path}: {e}") from e
        except UnicodeEncodeError as e:
            raise ValueError(f"Failed to encode word to UTF-8: {e}") from e
