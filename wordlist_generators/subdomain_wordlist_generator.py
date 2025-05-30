import re
from pathlib import Path
from textwrap import dedent
from typing import List, Optional

from wordlist_generators.wordlist_generator import WordlistGenerator


class SubdomainWordlistGenerator(WordlistGenerator):
    """Generator for subdomain enumeration wordlists."""

    MIN_LENGTH = 1
    MAX_LENGTH = 63  # DNS label limit
    VALID_CHARS_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$")

    def __init__(self, output_file: Optional[Path] = None):
        super().__init__(output_file)

    def _get_default_output_path(self) -> Path:
        """Return the default output path for subdomain wordlists."""
        return Path("subdomain_wordlist.txt")

    def _get_system_prompt(self) -> str:
        """Return the system prompt for subdomain generation."""
        return dedent(
            """\
            You are an expert in generating subdomain wordlists for penetration testing.

            Given these seed words: {seed_words}

            Generate exactly {wordlist_length} potential subdomains.

            Focus on:
            - Common subdomain patterns (api, dev, staging, prod, test)
            - Department names (hr, finance, it, sales)
            - Geographic indicators (us-east, eu-west, asia)
            - Service indicators (mail, ftp, vpn, portal)
            - Version indicators (v1, v2, new, old, legacy)
            - Environment indicators (uat, qa, demo)
            - Combinations with seed words
            - Industry-specific subdomains based on the seed context

            Output ONLY valid subdomain labels (lowercase, alphanumeric, hyphens allowed
            but not at start/end).
            One subdomain per line, no explanations.\
        """
        )

    def _validate_word(self, word: str) -> bool:
        """Validate a word as a valid subdomain label."""
        if not word:
            return False

        word = word.lower()

        if len(word) < self.MIN_LENGTH or len(word) > self.MAX_LENGTH:
            return False

        return bool(self.VALID_CHARS_PATTERN.match(word))

    def _process_generated_words(self, words: List[str]) -> List[str]:
        """Process generated words, ensuring they're lowercase."""
        lowercase_words = [word.lower() for word in words]
        return super()._process_generated_words(lowercase_words)
