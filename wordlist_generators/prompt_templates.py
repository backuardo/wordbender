from textwrap import dedent
from typing import Dict, List, Optional


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
        context: Optional[str] = None,
        methodology: Optional[str] = None,
        input_spec: Optional[str] = None,
        output_requirements: Optional[str] = None,
        constraints: Optional[str] = None,
        additional_sections: Optional[Dict[str, str]] = None,
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
    def format_list(items: List[str], bullet: str = "-") -> str:
        """Format a list of items with consistent indentation."""
        return "\n".join(f"{bullet} {item}" for item in items)

    @staticmethod
    def format_numbered_list(items: List[str]) -> str:
        """Format a numbered list with consistent formatting."""
        return "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))


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
    ) -> List[str]:
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


def create_simple_prompt(system_prompt: str, **kwargs) -> str:
    """
    Create a simple prompt by formatting a template string.

    This is for backwards compatibility and simple use cases.
    """
    return dedent(system_prompt).format(**kwargs)
