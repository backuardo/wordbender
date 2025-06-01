from unittest.mock import Mock, patch

import pytest

from cli.factories import GeneratorFactory, LlmServiceFactory
from config import Config
from wordlist_generators.password_wordlist_generator import PasswordWordlistGenerator
from wordlist_generators.subdomain_wordlist_generator import (
    SubdomainWordlistGenerator,
)


class TestGenerationFlow:
    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.get_api_key.return_value = "test-api-key"
        config.get_preferences.return_value = {
            "default_provider": "openrouter",
            "default_wordlist_type": "password",
            "default_wordlist_length": 50,
        }
        return config

    @pytest.fixture
    def generator_factory(self):
        return GeneratorFactory()

    @pytest.fixture
    def llm_factory(self, mock_config):
        return LlmServiceFactory(mock_config)

    @pytest.mark.integration
    def test_password_generation_flow(self, generator_factory, tmp_path):
        output_file = tmp_path / "passwords.txt"
        generator = generator_factory.create("password", output_file)
        assert isinstance(generator, PasswordWordlistGenerator)

        generator.add_seed_words("john", "smith", "chicago", "bears")
        generator.wordlist_length = 20
        generator.additional_instructions = "Focus on sports-related variations"

        mock_llm = Mock()
        mock_llm.generate_words.return_value = [
            "johnsmith123",
            "chicago2024",
            "bearswin",
            "smith@chicago",
            "invalid!@#",  # Should be filtered out
            "jsmith",
            "chicagobears",
            "bears1985",
            "smithjohn",
            "gobears",
        ]

        words = generator.generate(mock_llm)

        assert len(words) > 0
        assert "invalid!@#" not in words  # Special chars filtered
        assert all(generator._validate_word(w) for w in words)

        generator.save()
        assert output_file.exists()

        saved_words = output_file.read_text().strip().split("\n")
        assert saved_words == words

    @pytest.mark.integration
    def test_subdomain_generation_flow(self, generator_factory, tmp_path):
        output_file = tmp_path / "subdomains.txt"
        generator = generator_factory.create("subdomain", output_file)
        assert isinstance(generator, SubdomainWordlistGenerator)

        generator.add_seed_words("acme", "corp", "cloud", "newyork")
        generator.wordlist_length = 15

        mock_llm = Mock()
        mock_llm.generate_words.return_value = [
            "api",
            "dev-acme",
            "cloud-prod",
            "NYC-office",  # Should be lowercased
            "staging",
            "acme-api",
            "test@cloud",  # Should be filtered out
            "-invalid",  # Should be filtered out
            "valid-subdomain",
            "api-v2",
        ]

        words = generator.generate(mock_llm)

        assert len(words) > 0
        assert "test@cloud" not in words  # Invalid chars filtered
        assert "-invalid" not in words  # Can't start with hyphen
        assert "nyc-office" in words  # Lowercased
        assert all(generator._validate_word(w) for w in words)

        generator.save()
        assert output_file.exists()

    @pytest.mark.integration
    @patch("requests.post")
    def test_full_flow_with_real_services(self, mock_post, mock_config, tmp_path):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            "testword1\ntestword2\ntestword3\ntestword4\ntestword5"
                        )
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        gen_factory = GeneratorFactory()
        llm_factory = LlmServiceFactory(mock_config)

        output_file = tmp_path / "wordlist.txt"
        generator = gen_factory.create("password", output_file)
        llm_service = llm_factory.create("openrouter", "claude-opus")

        assert generator is not None
        generator.add_seed_words("test", "seed", "words")
        generator.wordlist_length = 5

        if llm_service:  # Service might not be available in test env
            words = generator.generate(llm_service)
            assert len(words) == 5
            generator.save()
            assert output_file.exists()

    @pytest.mark.integration
    def test_error_handling_flow(self, generator_factory):
        generator = generator_factory.create("password")

        mock_llm = Mock()
        with pytest.raises(ValueError, match="No seed words provided"):
            generator.generate(mock_llm)

        generator.add_seed_words("test")
        mock_llm.generate_words.side_effect = Exception("API error")

        with pytest.raises(
            RuntimeError, match="Failed to generate words from LLM: API error"
        ):
            generator.generate(mock_llm)

        mock_llm.generate_words.side_effect = None
        mock_llm.generate_words.return_value = []
        with pytest.raises(ValueError, match="LLM returned empty response"):
            generator.generate(mock_llm)

    @pytest.mark.integration
    def test_append_mode_flow(self, generator_factory, tmp_path):
        output_file = tmp_path / "wordlist.txt"

        generator1 = generator_factory.create("password", output_file)
        generator1.add_seed_words("first", "batch")
        generator1._generated_words = ["word1", "word2"]
        generator1.save()

        generator2 = generator_factory.create("password", output_file)
        generator2.add_seed_words("second", "batch")
        generator2._generated_words = ["word3", "word4"]
        generator2.save(append=True)

        content = output_file.read_text()
        assert content == "word1\nword2\nword3\nword4\n"

    @pytest.mark.integration
    def test_duplicate_removal_flow(self, generator_factory):
        generator = generator_factory.create("password")
        generator.add_seed_words("test")

        mock_llm = Mock()
        mock_llm.generate_words.return_value = [
            "word1",
            "word2",
            "word1",  # Duplicate
            "word3",
            "word2",  # Duplicate
            "word4",
        ]

        words = generator.generate(mock_llm)
        assert words == ["word1", "word2", "word3", "word4"]
        assert len(words) == 4

    @pytest.mark.integration
    def test_validation_filtering_flow(self, generator_factory):
        generator = generator_factory.create("password")
        generator.add_seed_words("test")

        mock_llm = Mock()
        mock_llm.generate_words.return_value = [
            "validword",
            "ab",  # Too short
            "a" * 31,  # Too long
            "special@char",  # Invalid chars
            "another-valid",  # Hyphens not allowed in passwords
            "UPPERCASE",  # Valid
            "123numeric",  # Valid
        ]

        with patch("builtins.print"):
            words = generator.generate(mock_llm)

        assert "validword" in words
        assert "ab" not in words
        assert "a" * 31 not in words
        assert "special@char" not in words
        assert "another-valid" not in words
        assert "UPPERCASE" in words
        assert "123numeric" in words
