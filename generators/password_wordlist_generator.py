import re
from pathlib import Path
from textwrap import dedent
from typing import Optional

from generators.wordlist_generator import WordlistGenerator


class PasswordWordlistGenerator(WordlistGenerator):
    """Generator for password wordlists"""

    MIN_LENGTH = 3
    MAX_LENGTH = 30
    VALID_CHARS_PATTERN = re.compile(r"^[a-zA-Z0-9]+$")

    def __init__(self, output_file: Optional[Path] = None):
        super().__init__(output_file)

    def _get_default_output_path(self) -> Path:
        """Return the default output path for password wordlists"""
        return Path("password_base_wordlist.txt")


def _get_system_prompt(self) -> str:
    """Return the system prompt for password base word generation"""
    return dedent(
        """\
        You are an expert in generating base wordlists for password cracking.

        Given these seed words: {seed_words}

        Generate exactly {wordlist_length} base words that could be used with
        mutation rules in tools like Hashcat.

        Focus on:
        - Words semantically related to the seeds (synonyms, associated concepts)
        - Common variations in spelling (color/colour, center/centre)
        - Related proper nouns (brands, locations, cultural references)
        - Compound words using the seeds
        - Industry or context-specific terminology
        - Pop culture references related to the seeds

        Output ONLY alphanumeric base words, one per line.
        Do NOT include:
        - Special characters or numbers (Hashcat will handle mutations)
        - Explanations or categories
        - Duplicate words
        - Very short (less than 3 chars) or very long (over 30 chars) words\
    """
    )

    def _validate_word(self, word: str) -> bool:
        """Validate a single word for password wordlist inclusion"""
        if not word:
            return False

        # Check length constraints
        if len(word) < self.MIN_LENGTH or len(word) > self.MAX_LENGTH:
            return False

        # Only allow alphanumeric characters
        return bool(self.VALID_CHARS_PATTERN.match(word))
