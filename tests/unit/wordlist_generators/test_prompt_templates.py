import pytest

from wordlist_generators.prompt_templates import (
    CommonPromptFragments,
    PromptTemplate,
    create_simple_prompt,
)


class TestPromptTemplate:
    def test_create_prompt_minimal(self):
        prompt = PromptTemplate.create_prompt(role="r", task="t")
        assert "<role>" in prompt and "</role>" in prompt
        assert "<task>" in prompt and "</task>" in prompt
        assert "<context>" not in prompt

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
        expected_tags = [
            "role",
            "task",
            "context",
            "methodology",
            "input",
            "output_requirements",
            "constraints",
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


class TestCreateSimplePrompt:
    def test_create_simple_prompt_basic(self):
        template = "Hello {name}!"
        result = create_simple_prompt(template, name="World")
        assert result == "Hello World!"

    def test_create_simple_prompt_missing_variable(self):
        template = "Hello {name}!"
        with pytest.raises(KeyError):
            create_simple_prompt(template)


class TestPromptTemplateIntegration:
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
        assert "25" in prompt
