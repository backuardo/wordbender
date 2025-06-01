import re
from pathlib import Path
from textwrap import dedent
from typing import List, Optional

from wordlist_generators.prompt_templates import (
    PromptTemplate,
    create_simple_prompt,
)
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
        focus_areas = [
            "Common subdomain patterns (api, dev, staging, prod, test)",
            "Department names (hr, finance, it, sales)",
            "Geographic indicators (us-east, eu-west, asia)",
            "Service indicators (mail, ftp, vpn, portal)",
            "Version indicators (v1, v2, new, old, legacy)",
            "Environment indicators (uat, qa, demo)",
            "Combinations with seed words",
            "Industry-specific subdomains based on the seed context",
        ]

        return create_simple_prompt(
            """\
            You are an expert in generating subdomain wordlists for penetration testing.

            Given these seed words: {seed_words}

            Generate exactly {wordlist_length} potential subdomains.

            Focus on:
            {focus_areas}

            Output ONLY valid subdomain labels (lowercase, alphanumeric, hyphens allowed
            but not at start/end).
            One subdomain per line, no explanations.\
            """,
            seed_words="{seed_words}",
            wordlist_length="{wordlist_length}",
            focus_areas=PromptTemplate.format_list(focus_areas),
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

    def _get_detailed_system_prompt(self) -> str:
        """Return the detailed system prompt for subdomain generation."""
        role = (
            "You are a cybersecurity expert specializing in subdomain "
            "enumeration and organizational infrastructure naming patterns "
            "for ethical penetration testing."
        )

        task = (
            "Generate a targeted subdomain wordlist based on organizational "
            "intelligence provided as seed words. Reflect realistic corporate "
            "subdomain naming conventions by analyzing the organizational "
            "context and applying appropriate naming patterns."
        )

        context_items = [
            "Company names, abbreviations, stock tickers, brand names",
            "Industry sector and specialized terminology",
            "Technology stack, platforms, and services",
            "Geographic locations and regional presence",
            "Product names, services, and project codenames",
            "Organizational structure (departments, teams, business units)",
            "Partner and vendor relationships",
        ]
        context = (
            "The seed words represent organizational intelligence including:\n"
            + PromptTemplate.format_list(context_items)
        )

        methodology_steps = [
            "**Parse organizational context** from seed words to understand:\n"
            "   - Primary business focus and industry\n"
            "   - Technology ecosystem and platforms used\n"
            "   - Geographic footprint and regional structure\n"
            "   - Product/service portfolio",
            "**Apply naming pattern hierarchy**:\n"
            "   - **Core infrastructure**: Standard patterns "
            "(api, dev, staging, prod, test, admin, portal, mail)\n"
            "   - **Company-specific**: [company]-[service], "
            "[brand]-[environment]\n"
            "   - **Product-focused**: [product]-api, [service]-dev, "
            "[project]-staging\n"
            "   - **Geographic**: [location]-prod, [region]-portal, "
            "[country]-api\n"
            "   - **Technology-based**: [platform]-[env], [stack]-test "
            "(e.g., aws-prod, k8s-staging)\n"
            "   - **Department-oriented**: [dept]-portal, [team]-dev, "
            "[unit]-api\n"
            "   - **Industry-specific**: Apply domain-relevant patterns "
            "(fintech: payment-api, compliance-portal)",
            "**Prioritize by likelihood**: More common patterns first, then "
            "context-specific variations",
        ]
        methodology = PromptTemplate.format_numbered_list(methodology_steps)

        input_spec = (
            "Seed words: {seed_words}\n"
            "Target output length: {wordlist_length} subdomains"
        )

        output_requirements = [
            "Output exactly {wordlist_length} subdomain labels",
            "One subdomain per line, no other text",
            "Lowercase alphanumeric characters and hyphens only",
            "Hyphens not at start or end of labels",
            "Length: 1-63 characters per label",
            "No duplicates",
            "Prioritize most realistic patterns based on organizational context",
        ]

        constraints = [
            "Do NOT include invalid DNS characters",
            "Do NOT include generic subdomains unrelated to organizational context",
            "Do NOT include explanations or categories in output",
            "Do NOT start or end labels with hyphens",
            "Do NOT exceed DNS label length limits",
        ]

        return PromptTemplate.create_prompt(
            role=role,
            task=task,
            context=context,
            methodology=methodology,
            input_spec=input_spec,
            output_requirements=PromptTemplate.format_list(output_requirements),
            constraints=PromptTemplate.format_list(constraints),
            additional_sections={"context_analysis": context},
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
