import re
from pathlib import Path
from textwrap import dedent

from wordlist_generators.prompt_templates import (
    CommonPromptFragments,
    PromptTemplate,
    create_simple_prompt,
)
from wordlist_generators.wordlist_generator import WordlistGenerator


class SubdomainWordlistGenerator(WordlistGenerator):
    """Generator for subdomain enumeration wordlists."""

    MIN_LENGTH = 1
    MAX_LENGTH = 63  # DNS label limit
    VALID_CHARS_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$")

    def __init__(self, output_file: Path | None = None):
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

    def _process_generated_words(self, words: list[str]) -> list[str]:
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
            "You are a red team operator specializing in subdomain "
            "enumeration, DNS reconnaissance, and organizational infrastructure "
            "discovery for authorized penetration testing. You understand how "
            "organizations actually name their infrastructure versus how they should."
        )

        task = (
            "Generate a targeted subdomain wordlist based on organizational "
            "intelligence provided as seed words. Focus on realistic patterns "
            "including typos, legacy systems, shadow IT, and regional variations "
            "that organizations actually use."
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
            + "\n\n"
            + CommonPromptFragments.cultural_variation_instructions()
        )

        methodology_steps = [
            "**Chain-of-Thought Analysis**:\n"
            + CommonPromptFragments.chain_of_thought_instructions(),
            "**Parse organizational context** from seed words to understand:\n"
            "   - Primary business focus and industry\n"
            "   - Technology ecosystem and platforms used\n"
            "   - Geographic footprint and regional structure\n"
            "   - Product/service portfolio\n"
            "   - Potential acquisitions and legacy systems",
            "**Apply realistic naming patterns**:\n"
            "   - **Core infrastructure**: api, dev, staging, prod, test, admin\n"
            "   - **Shadow IT patterns**: test1, dev2, temp, demo, poc\n"
            "   - **Legacy indicators**: old, new, v1, v2, legacy, classic\n"
            "   - **Emergency/temporary**: backup, dr, failover, temp-prod\n"
            "   - **Developer shortcuts**: myapp, testapp, devbox, sandbox",
            "**Regional and cultural variations**:\n"
            "   - Date formats: dev-2024-01-15 vs dev-15-01-2024\n"
            "   - Language variations: centre vs center, analyse vs analyze\n"
            "   - Local office patterns: [city]-office, [country-code]-prod\n"
            "   - Time zones: pst-api, gmt-portal, est-dev",
            "**Company-specific patterns**:\n"
            "   - [company]-[service]: acme-api, acme-portal\n"
            "   - [brand]-[env]: brand1-dev, brand2-staging\n"
            "   - [acquisition]-[legacy]: oldcompany-api, merged-portal\n"
            "   - Internal project codenames: project-phoenix, operation-sunset",
            "**Technology-based naming**:\n"
            "   - Platform specific: aws-prod, azure-dev, gcp-staging\n"
            "   - Container patterns: k8s-cluster, docker-registry\n"
            "   - Service mesh: istio-gateway, consul-ui\n"
            "   - CDN/Edge: edge1, cdn-origin, cache-west",
            "**Adversarial patterns**:\n"
            + CommonPromptFragments.adversarial_thinking_instructions(),
        ]
        methodology = PromptTemplate.format_numbered_list(methodology_steps)

        good_examples = [
            ("api", "standard API endpoint"),
            ("api-v2", "versioned API - very common"),
            ("dev", "development environment"),
            ("dev1", "numbered dev environment - indicates multiple"),
            ("test-api", "test version of API service"),
            ("staging", "pre-production environment"),
            ("legacy-api", "old API kept for compatibility"),
            ("api-staging", "staging environment for API"),
            ("payment-gateway", "service-specific subdomain from fintech context"),
            ("aws-prod", "cloud provider specific naming"),
            ("dev-mgmt", "management abbreviation"),
            ("api2", "numbered API instance"),
            ("temp-prod", "emergency/temporary production"),
        ]

        bad_examples = [
            ("123random", "random numbers without context"),
            ("aaaaaa", "repeated characters without meaning"),
            ("subdomain1", "generic without organizational context"),
            ("test-test-test", "excessive repetition"),
            ("thisisaverylongsubdomainthatexceedsthelimit", "exceeds DNS limits"),
        ]

        examples_section = CommonPromptFragments.create_few_shot_examples(
            good_examples, bad_examples
        )

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
            CommonPromptFragments.diversity_requirements(),
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
            additional_sections={
                "context_analysis": context,
                "examples": examples_section,
            },
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
