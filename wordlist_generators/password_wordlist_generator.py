import re
from pathlib import Path
from textwrap import dedent
from typing import Optional

from wordlist_generators.wordlist_generator import WordlistGenerator


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

        if len(word) < self.MIN_LENGTH or len(word) > self.MAX_LENGTH:
            return False

        return bool(self.VALID_CHARS_PATTERN.match(word))

    def get_seed_hints(self) -> str:
        """Return hints about what seed words to provide."""
        return dedent(
            """\
            For effective password wordlists, provide diverse information about the
            target:
            • Personal info: First name, last name, nicknames, usernames
            • Important dates: Birthdays (e.g., "May 3 1989"), anniversaries
            • Family & pets: Spouse name, children's names, pet names
            • Locations: Cities lived in, favorite vacation spots, birthplace
            • Interests: Hobbies, favorite sports teams, bands, movies
            • Work: Company name, job title, department, projects
            • Numbers: Lucky numbers, phone area codes, zip codes

            Example: john smith may31989 fluffy chicago bears accounting\
            """
        )

    def get_usage_instructions(self) -> str:
        """Return instructions for using the generated wordlist."""
        return dedent(
            """\
            Next steps:
            1. Feed this wordlist into a password mutation tool like Hashcat:
               hashcat -a 0 -m <hash_type> <hash_file> password_base_wordlist.txt \\
                 -r rules/best64.rule

            2. Common Hashcat rule files to try:
               - rules/best64.rule (good balance of mutations)
               - rules/d3ad0ne.rule (extensive mutations)
               - rules/dive.rule (targeted mutations)

            3. You can also combine with masks for hybrid attacks:
               hashcat -a 6 -m <hash_type> <hash_file> password_base_wordlist.txt \\
                 ?d?d?d?d

            Tip: The generated words are base words - Hashcat will create variations
            with numbers, special characters, capitalization, etc.\
            """
        )
