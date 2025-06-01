import pytest

from wordlist_generators.prompt_templates import (
    CommonPromptFragments,
    PromptTemplate,
    create_simple_prompt,
)


class TestPromptTemplate:
    def test_wrap_section(self):
        result = PromptTemplate.wrap_section("tag_name", "content")
        assert result.startswith("<tag_name>\n")
        assert result.endswith("\n</tag_name>")
        assert "content" in result

    def test_format_list_default_bullet(self):
        items = ["item1", "item2", "item3"]
        result = PromptTemplate.format_list(items)
        lines = result.split("\n")
        assert len(lines) == 3
        assert all(line.startswith("- ") for line in lines)
        assert lines[0].endswith("item1")
        assert lines[1].endswith("item2")
        assert lines[2].endswith("item3")

    def test_format_list_custom_bullet(self):
        items = ["a", "b"]
        result = PromptTemplate.format_list(items, bullet="*")
        lines = result.split("\n")
        assert len(lines) == 2
        assert all(line.startswith("* ") for line in lines)

    def test_format_list_empty(self):
        result = PromptTemplate.format_list([])
        assert result == ""

    def test_format_numbered_list(self):
        items = ["a", "b", "c"]
        result = PromptTemplate.format_numbered_list(items)
        lines = result.split("\n")
        assert len(lines) == 3
        assert lines[0].startswith("1. ")
        assert lines[1].startswith("2. ")
        assert lines[2].startswith("3. ")

    def test_format_numbered_list_empty(self):
        result = PromptTemplate.format_numbered_list([])
        assert result == ""

    def test_create_prompt_minimal(self):
        prompt = PromptTemplate.create_prompt(role="r", task="t")
        sections = prompt.split("\n\n")
        assert len(sections) == 2  # Only role and task
        assert "<role>" in prompt and "</role>" in prompt
        assert "<task>" in prompt and "</task>" in prompt
        assert "<context>" not in prompt
        assert "<methodology>" not in prompt
        assert "<input>" not in prompt
        assert "<output_requirements>" not in prompt
        assert "<constraints>" not in prompt

    def test_create_prompt_all_sections(self):
        prompt = PromptTemplate.create_prompt(
            role="r",
            task="t",
            context="c",
            methodology="m",
            input_spec="i",
            output_requirements="o",
            constraints="con",
        )
        sections = prompt.split("\n\n")
        assert len(sections) == 7
        expected_tags = [
            "role", "task", "context", "methodology",
            "input", "output_requirements", "constraints"
        ]
        for tag in expected_tags:
            assert f"<{tag}>" in prompt
            assert f"</{tag}>" in prompt

    def test_create_prompt_with_additional_sections(self):
        prompt = PromptTemplate.create_prompt(
            role="r",
            task="t",
            additional_sections={
                "custom1": "c1",
                "custom2": "c2",
            },
        )
        assert "<custom1>" in prompt and "</custom1>" in prompt
        assert "<custom2>" in prompt and "</custom2>" in prompt
        sections = prompt.split("\n\n")
        assert len(sections) == 4

    def test_create_prompt_section_order(self):
        prompt = PromptTemplate.create_prompt(
            role="Role",
            task="Task",
            context="Context",
            methodology="Methodology",
            input_spec="Input",
            output_requirements="Output",
            constraints="Constraints",
        )

        role_pos = prompt.find("<role>")
        task_pos = prompt.find("<task>")
        context_pos = prompt.find("<context>")
        methodology_pos = prompt.find("<methodology>")
        input_pos = prompt.find("<input>")
        output_pos = prompt.find("<output_requirements>")
        constraints_pos = prompt.find("<constraints>")

        assert role_pos < task_pos < context_pos < methodology_pos
        assert methodology_pos < input_pos < output_pos < constraints_pos

    def test_create_prompt_with_formatted_content(self):
        items = ["a", "b"]
        formatted = PromptTemplate.format_list(items)
        prompt = PromptTemplate.create_prompt(
            role="r",
            task="t",
            output_requirements=formatted,
        )
        assert "<output_requirements>" in prompt
        assert formatted in prompt


class TestCommonPromptFragments:
    def test_penetration_testing_context(self):
        context = CommonPromptFragments.penetration_testing_context()
        assert isinstance(context, str)
        assert len(context) > 0

    def test_output_format_requirements_default(self):
        requirements = CommonPromptFragments.output_format_requirements(100)
        assert isinstance(requirements, list)
        assert len(requirements) == 5
        assert "100" in requirements[0]

    def test_output_format_requirements_custom(self):
        requirements = CommonPromptFragments.output_format_requirements(
            50, one_per_line=False, no_explanations=False
        )
        assert isinstance(requirements, list)
        assert len(requirements) == 3
        assert "50" in requirements[0]

    def test_no_generic_items_constraint(self):
        constraint = CommonPromptFragments.no_generic_items_constraint("items")
        assert isinstance(constraint, str)
        assert "items" in constraint
        assert constraint.startswith("Do NOT")


class TestCreateSimplePrompt:
    def test_create_simple_prompt_basic(self):
        template = "Hello {name}!"
        result = create_simple_prompt(template, name="World")
        assert result == "Hello World!"

    def test_create_simple_prompt_with_dedent(self):
        template = """
            Line1
            Line2
        """
        result = create_simple_prompt(template)
        lines = result.strip().split("\n")

        assert not any(line.startswith(" ") for line in lines)
        assert len(lines) == 2

    def test_create_simple_prompt_missing_variable(self):
        template = "Hello {name}!"
        with pytest.raises(KeyError):
            create_simple_prompt(template)

    def test_create_simple_prompt_ignores_extra_kwargs(self):
        template = "{x}"
        result = create_simple_prompt(template, x="used", y="ignored", z="ignored")
        assert result == "used"


class TestPromptTemplateIntegration:
    def test_prompt_structure_with_mixed_formatting(self):
        methodology_items = ["step1", "step2", "step3"]
        output_items = ["req1", "req2", "req3"]

        prompt = PromptTemplate.create_prompt(
            role="role",
            task="task",
            methodology=PromptTemplate.format_numbered_list(methodology_items),
            output_requirements=PromptTemplate.format_list(output_items, bullet="•"),
            constraints=CommonPromptFragments.no_generic_items_constraint("items"),
        )

        assert prompt.count("<") == prompt.count(">")
        assert "<role>" in prompt and "</role>" in prompt
        assert "<methodology>" in prompt and "</methodology>" in prompt
        assert "1. " in prompt
        assert "• " in prompt

    def test_integration_with_common_fragments(self):
        requirements = CommonPromptFragments.output_format_requirements(25)
        prompt = PromptTemplate.create_prompt(
            role="r",
            task="t",
            context=CommonPromptFragments.penetration_testing_context(),
            output_requirements=PromptTemplate.format_list(requirements),
            constraints=CommonPromptFragments.no_generic_items_constraint("x"),
        )

        assert "<context>" in prompt
        assert "<output_requirements>" in prompt
        assert "<constraints>" in prompt
        assert prompt.count("<") == prompt.count(">")
