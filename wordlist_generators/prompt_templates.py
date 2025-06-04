from textwrap import dedent


class PromptTemplate:
    """Base class for creating structured prompts with XML-like formatting."""

    @staticmethod
    def wrap_section(tag: str, content: str) -> str:
        """Wrap content in XML-like tags."""
        return f"<{tag}>\n{content}\n</{tag}>"

    @staticmethod
    def create_prompt(
        role: str,
        task: str,
        context: str | None = None,
        methodology: str | None = None,
        input_spec: str | None = None,
        output_requirements: str | None = None,
        constraints: str | None = None,
        additional_sections: dict[str, str] | None = None,
    ) -> str:
        """
        Create a structured prompt with consistent XML-like formatting.

        Args:
            role: The role/expertise of the AI
            task: The main task description
            context: Optional context information
            methodology: Optional methodology/approach
            input_spec: Optional input specification
            output_requirements: Required output format and rules
            constraints: What NOT to do
            additional_sections: Any additional custom sections

        Returns:
            Formatted prompt string
        """
        sections = []
        sections.append(PromptTemplate.wrap_section("role", role))
        sections.append(PromptTemplate.wrap_section("task", task))

        if context:
            sections.append(PromptTemplate.wrap_section("context", context))

        if methodology:
            sections.append(PromptTemplate.wrap_section("methodology", methodology))

        if input_spec:
            sections.append(PromptTemplate.wrap_section("input", input_spec))

        if output_requirements:
            sections.append(
                PromptTemplate.wrap_section("output_requirements", output_requirements)
            )

        if constraints:
            sections.append(PromptTemplate.wrap_section("constraints", constraints))

        if additional_sections:
            for tag, content in additional_sections.items():
                sections.append(PromptTemplate.wrap_section(tag, content))

        return "\n\n".join(sections)

    @staticmethod
    def format_list(items: list[str], bullet: str = "-") -> str:
        """Format a list of items with consistent indentation."""
        return "\n".join(f"{bullet} {item}" for item in items)

    @staticmethod
    def format_numbered_list(items: list[str]) -> str:
        """Format a numbered list with consistent formatting."""
        return "\n".join(f"{i + 1}. {item}" for i, item in enumerate(items))


class CommonPromptFragments:
    """Common prompt fragments that can be reused across generators."""

    @staticmethod
    def penetration_testing_context() -> str:
        """Common context about ethical penetration testing."""
        return (
            "This is for authorized penetration testing and security assessment "
            "purposes. The generated wordlist will be used to identify security "
            "weaknesses in systems where testing is explicitly permitted."
        )

    @staticmethod
    def output_format_requirements(
        count: int, one_per_line: bool = True, no_explanations: bool = True
    ) -> list[str]:
        """Common output format requirements."""
        requirements = [f"Output exactly {count} items"]

        if one_per_line:
            requirements.append("One item per line, no other text")

        if no_explanations:
            requirements.append("No explanations, categories, or additional text")

        requirements.extend(["No duplicates", "Follow all specified validation rules"])

        return requirements

    @staticmethod
    def no_generic_items_constraint(item_type: str) -> str:
        """Constraint against generic items unrelated to context."""
        return f"Do NOT include generic {item_type} unrelated to the provided context"

    @staticmethod
    def adversarial_thinking_instructions() -> str:
        """Instructions for thinking like an attacker."""
        return dedent("""
        Think like a red team operator:
        - Consider what developers actually use, not what they should use
        - Remember human laziness and shortcuts
        - Think about emergency deployments and quick fixes
        - Remember that people reuse patterns across systems
        - Think about legacy systems and technical debt
        """).strip()

    @staticmethod
    def chain_of_thought_instructions() -> str:
        """Instructions for demonstrating reasoning process."""
        return dedent("""
        For each pattern type, follow this reasoning process:
        1. Analyze the seed words for context clues
        2. Identify the likely organization type/industry
        3. Determine if regional/cultural context is present in seeds
        4. Apply relevant pattern generation strategies
        5. Validate against real-world likelihood
        """).strip()

    @staticmethod
    def diversity_requirements() -> str:
        """Requirements for ensuring diverse output."""
        return dedent("""
        Ensure output diversity:
        - 30% common/obvious patterns
        - 40% mutations and variations
        - 20% creative/unusual patterns
        - 10% high-risk/edge cases
        Avoid clustering similar patterns together.
        """).strip()

    @staticmethod
    def cultural_variation_instructions() -> str:
        """Instructions for incorporating cultural variations."""
        return dedent("""
        ONLY if the seed words contain regional/cultural indicators (city names,
        country names, regional terms, non-English words), then consider:
        - Language variations (color/colour, center/centre)
        - Date formats (MM/DD/YYYY vs DD/MM/YYYY)
        - Regional terminology (elevator/lift, soccer/football)
        - Local references (sports teams, landmarks)
        - Transliterations and local language terms

        If no regional context is present in seeds, focus on universal patterns.
        """).strip()

    @staticmethod
    def create_few_shot_examples(
        good_examples: list[tuple[str, str]], bad_examples: list[tuple[str, str]]
    ) -> str:
        """Create few-shot examples section with reasoning."""
        examples = ["Examples with reasoning:\n"]

        examples.append("GOOD examples:")
        for example, reasoning in good_examples:
            examples.append(f"✓ {example} - {reasoning}")

        examples.append("\nBAD examples:")
        for example, reasoning in bad_examples:
            examples.append(f"✗ {example} - {reasoning}")

        return "\n".join(examples)


def create_simple_prompt(system_prompt: str, **kwargs) -> str:
    """
    Create a simple prompt by formatting a template string.

    This is for backwards compatibility and simple use cases.
    """
    return dedent(system_prompt).format(**kwargs)
