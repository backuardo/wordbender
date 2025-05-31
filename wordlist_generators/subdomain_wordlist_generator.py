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

        # DNS labels must be lowercase
        word_lower = word.lower()

        if len(word_lower) < self.MIN_LENGTH or len(word_lower) > self.MAX_LENGTH:
            return False

        # No consecutive hyphens
        if "--" in word_lower:
            return False

        return bool(self.VALID_CHARS_PATTERN.match(word_lower))

    def _process_generated_words(self, words: List[str]) -> List[str]:
        """Process generated words, ensuring they're lowercase."""
        # Convert to lowercase before processing (validation already does this)
        lowercase_words = [word.lower() for word in words]
        return super()._process_generated_words(lowercase_words)

    def get_seed_hints(self) -> str:
        """Return hints about what seed words to provide."""
        return dedent(
            """\
            For effective subdomain wordlists, provide information about the
            organization:
            • Company: Name, abbreviations, stock ticker, brand names
            • Industry: Sector keywords, industry-specific terms
            • Technology: Known tech stack, platforms, services used
            • Geographic: Office locations, regions served, country codes
            • Products: Product names, service names, project codenames
            • Structure: Department names, team names, business units
            • Partners: Vendor names, client names, integration partners

            Example: acmecorp acme fintech aws cloud newyork payment gateway\
            """
        )

    def get_usage_instructions(self) -> str:
        """Return instructions for using the generated wordlist."""
        return dedent(
            """\
            Next steps:
            1. Use with subdomain enumeration tools:
               • gobuster: gobuster dns -d target.com -w subdomain_wordlist.txt
               • ffuf: ffuf -u https://FUZZ.target.com -w subdomain_wordlist.txt
               • subfinder: subfinder -d target.com -wL subdomain_wordlist.txt

            2. Combine with other reconnaissance:
               • Passive DNS data from services like SecurityTrails
               • Certificate transparency logs
               • Search engine dorking

            3. Verify discovered subdomains:
               • Check for wildcard DNS
               • Probe for live hosts
               • Screenshot interesting services

            Tip: Many organizations use predictable patterns - the AI helps find these!\
            """
        )
