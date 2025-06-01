import re
from pathlib import Path
from textwrap import dedent

from wordlist_generators.prompt_templates import (
    PromptTemplate,
    create_simple_prompt,
)
from wordlist_generators.wordlist_generator import WordlistGenerator


class PasswordWordlistGenerator(WordlistGenerator):
    """Generator for password wordlists"""

    MIN_LENGTH = 3
    MAX_LENGTH = 30
    VALID_CHARS_PATTERN = re.compile(r"^[a-zA-Z0-9]+$")

    def __init__(self, output_file: Path | None = None):
        super().__init__(output_file)

    def _get_default_output_path(self) -> Path:
        """Return the default output path for password wordlists"""
        return Path("password_base_wordlist.txt")

    def _get_system_prompt(self) -> str:
        """Return the system prompt for password base word generation"""
        focus_areas = [
            "Words semantically related to the seeds (synonyms, associated concepts)",
            "Common variations in spelling (color/colour, center/centre)",
            "Related proper nouns (brands, locations, cultural references)",
            "Compound words using the seeds",
            "Industry or context-specific terminology",
            "Pop culture references related to the seeds",
        ]

        do_not_include = [
            "Special characters or numbers (Hashcat will handle mutations)",
            "Explanations or categories",
            "Duplicate words",
            "Very short (less than 3 chars) or very long (over 30 chars) words",
        ]

        return create_simple_prompt(
            """\
            You are an expert in generating base wordlists for password cracking.

            Given these seed words: {seed_words}

            Generate exactly {wordlist_length} base words that could be used with
            mutation rules in tools like Hashcat.

            Focus on:
            {focus_areas}

            Output ONLY alphanumeric base words, one per line.
            Do NOT include:
            {do_not_include}\
            """,
            seed_words="{seed_words}",
            wordlist_length="{wordlist_length}",
            focus_areas=PromptTemplate.format_list(focus_areas),
            do_not_include=PromptTemplate.format_list(do_not_include),
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

    def _get_detailed_system_prompt(self) -> str:
        """Return the detailed system prompt for password generation."""
        role = (
            "You are a cybersecurity expert specializing in password pattern "
            "analysis and social engineering-based wordlist generation for "
            "ethical penetration testing."
        )

        task = (
            "Generate a targeted password base wordlist from personal intelligence "
            "about a specific individual. Focus on realistic human password "
            "selection behaviors based on personal significance and emotional "
            "attachment, not linguistic associations."
        )

        intelligence_items = [
            "Personal identifiers (names, nicknames, usernames)",
            "Significant dates and time periods "
            "(birthdays, anniversaries, graduation years)",
            "Personal relationships (family members, pets, close friends)",
            "Geographic connections (hometowns, places lived, vacation spots)",
            "Personal interests and passions (hobbies, sports teams, music, movies)",
            "Professional context (employers, job roles, departments, projects)",
            "Meaningful numbers and identifiers (area codes, lucky numbers, addresses)",
        ]
        intelligence_context = (
            "The seed words represent personal intelligence about the target "
            "including:\n" + PromptTemplate.format_list(intelligence_items)
        )

        methodology_parts = [
            "**Name variations**: Full names, nicknames, shortened versions, "
            "combinations\n"
            '   - If "john": include john, johnny, johnnie, johny, jr\n'
            '   - If "smith": include smith, smiths, smithy',
            "**Personal significance expansion**:\n"
            "   - Family/pet names and their common variations\n"
            "   - Favorite teams → team names, mascots, cities, rivalries\n"
            "   - Hobbies → equipment, terminology, famous figures\n"
            "   - Places → city names, nicknames, zip codes, area codes",
            "**Emotional connections**:\n"
            "   - Combine related personal elements "
            "(petname + hometown, team + birthyear)\n"
            "   - Important life events and associated terms\n"
            "   - Childhood memories and references",
            "**Professional identity**:\n"
            "   - Company names, abbreviations, department names\n"
            "   - Job titles, project names, industry terms",
            "**Common password psychology**:\n"
            "   - Things they're proud of or emotionally attached to\n"
            "   - Easy-to-remember personal combinations\n"
            "   - Seasonal or temporal references from their life",
        ]
        methodology = (
            "Analyze the personal intelligence to generate words people actually "
            "use in passwords:\n\n"
            + PromptTemplate.format_numbered_list(methodology_parts)
        )

        input_spec = (
            "Personal intelligence seed words: {seed_words}\n"
            "Target output length: {wordlist_length} words"
        )

        output_requirements = [
            "Output exactly {wordlist_length} base words",
            "One word per line, no other text",
            "Only alphanumeric characters (hashcat handles mutations)",
            "Length: 3-30 characters per word",
            "No duplicates",
            "All words must have personal significance to the target based on "
            "provided intelligence",
        ]

        constraints = [
            "Do NOT include generic passwords unrelated to personal intelligence",
            "Do NOT include leetspeak or character substitutions",
            "Do NOT include random names unconnected to the target",
            "Do NOT include dictionary words without personal connection",
            "Do NOT include explanations or categories in output",
        ]

        return PromptTemplate.create_prompt(
            role=role,
            task=task,
            methodology=methodology,
            input_spec=input_spec,
            output_requirements=PromptTemplate.format_list(output_requirements),
            constraints=PromptTemplate.format_list(constraints),
            additional_sections={"intelligence_context": intelligence_context},
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
