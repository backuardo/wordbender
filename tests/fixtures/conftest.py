import tempfile
from pathlib import Path

import pytest

from ..test_constants import (
    MOCK_ANTHROPIC_RESPONSE,
    MOCK_LLM_RESPONSE,
    MOCK_OPENROUTER_RESPONSE,
    SAMPLE_SEED_WORDS,
    SAMPLE_WORDLIST,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env(monkeypatch):
    def _mock_env(**kwargs):
        for key, value in kwargs.items():
            monkeypatch.setenv(key, value)

    return _mock_env


@pytest.fixture
def mock_home_dir(temp_dir, monkeypatch):
    home_dir = temp_dir / "home"
    home_dir.mkdir()
    monkeypatch.setenv("HOME", str(home_dir))
    return home_dir


@pytest.fixture
def sample_seed_words():
    return SAMPLE_SEED_WORDS


@pytest.fixture
def sample_wordlist():
    return SAMPLE_WORDLIST


@pytest.fixture
def mock_llm_response():
    return MOCK_LLM_RESPONSE


@pytest.fixture
def mock_openrouter_response():
    return MOCK_OPENROUTER_RESPONSE


@pytest.fixture
def mock_anthropic_response():
    return MOCK_ANTHROPIC_RESPONSE


@pytest.fixture
def mock_config_file(temp_dir):
    config_dir = temp_dir / ".wordbender"
    config_dir.mkdir()
    config_file = config_dir / "config.json"

    config_data = {
        "default_wordlist_type": "password",
        "default_length": 50,
        "llm_provider": "openrouter",
        "model": "claude-3-haiku",
    }

    import json

    config_file.write_text(json.dumps(config_data, indent=2))
    return config_file


@pytest.fixture
def mock_env_file(temp_dir):
    env_file = temp_dir / ".env"
    env_content = """OPENROUTER_API_KEY=test-openrouter-key
ANTHROPIC_API_KEY=test-anthropic-key
"""
    env_file.write_text(env_content)
    return env_file
