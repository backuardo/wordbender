import re
from pathlib import Path
from textwrap import dedent

from wordlist_generators.prompt_templates import (
    CommonPromptFragments,
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
            "You are a red team operator specializing in password pattern "
            "analysis and social engineering-based wordlist generation for "
            "authorized penetration testing. You understand how real people "
            "create passwords under pressure and convenience."
        )

        task = (
            "Generate base words from personal intelligence that will be fed into "
            "hashcat for mutation. Focus on single meaningful words with personal "
            "significance. Do NOT create combinations - generate individual words "
            "that hashcat can then combine, modify, and mutate with rules."
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
            "including:\n"
            + PromptTemplate.format_list(intelligence_items)
            + "\n\n"
            + CommonPromptFragments.cultural_variation_instructions()
        )

        methodology_parts = [
            "**Chain-of-Thought Analysis**:\n"
            + CommonPromptFragments.chain_of_thought_instructions(),
            "**Name Variations**: Generate individual name-based words:\n"
            "   - Nicknames and diminutives\n"
            "   - Alternative spellings and variations\n"
            "   - Maiden names and family names\n"
            "   - Usernames and handles",
            "**Semantic Expansion**: Extract meaningful related words:\n"
            "   - Sports teams → team names, mascots, cities\n"
            "   - Locations → landmarks, neighborhoods, regional terms\n"
            "   - Professions → industry terms, certifications, tools\n"
            "   - Hobbies → equipment names, terminology, brands",
            "**Personal Significance**: Focus on emotionally meaningful words:\n"
            "   - Pet names and animal types\n"
            "   - School names and alma maters\n"
            "   - Achievement and milestone terms\n"
            "   - Cultural and identity markers",
            "**Contextual Terms**: Generate words from implied context:\n"
            "   - Military → ranks, units, terminology, slang\n"
            "   - Academic → subjects, degrees, institutions\n"
            "   - Geographic → climate, features, local culture\n"
            "   - Temporal → seasons, months, decades, eras",
            "**Base Word Selection**: Choose single words that:\n"
            "   - Have personal emotional significance\n"
            "   - Are easy to remember and meaningful\n"
            "   - Represent core concepts from the seeds\n"
            "   - Will serve as good mutation bases for hashcat",
        ]
        methodology = (
            "Analyze the personal intelligence to generate words people actually "
            "use in passwords:\n\n"
            + PromptTemplate.format_numbered_list(methodology_parts)
        )

        good_examples = [
            ("johnny", "nickname variant - personal emotional connection"),
            ("fluffy", "pet name - strong emotional attachment"),
            ("chicago", "location - place significance"),
            ("bears", "sports team - passion/interest"),
            ("marine", "military service - professional identity"),
            ("lakeside", "location descriptor - meaningful place"),
            ("guitarist", "hobby identity - personal interest"),
            ("rookie", "contextual term - sports/military background"),
            ("semper", "military motto - cultural significance"),
            ("blue", "color - could be team colors, eyes, etc"),
        ]

        bad_examples = [
            ("johnsmith123", "mechanical combination - hashcat will do this"),
            ("password", "generic word unrelated to seeds"),
            ("admin", "generic term with no personal connection"),
            ("qwerty", "keyboard pattern not derived from seeds"),
            ("bearschitown85", "complex combination - generate base words instead"),
        ]

        examples_section = CommonPromptFragments.create_few_shot_examples(
            good_examples, bad_examples
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
            CommonPromptFragments.diversity_requirements(),
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
            additional_sections={
                "intelligence_context": intelligence_context,
                "examples": examples_section,
            },
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
