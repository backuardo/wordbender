# Wordbender

An LLM-powered targeted wordlist generator for penetration testing and security assessments. Wordbender uses AI language models to generate contextually relevant wordlists based on seed words you provide.

## Features

- **Multiple Wordlist Types**: Generate password base words or subdomain names
- **AI-Powered**: Uses Claude, GPT-4, and other models for intelligent word generation
- **Multiple Providers**: Supports Anthropic (direct), OpenRouter, and other LLM providers
- **Flexible Operation Modes**: Interactive CLI, direct generation, or batch processing
- **Smart Validation**: Ensures generated words meet specific criteria for each wordlist type
- **Extensible**: Easy to add new wordlist types or LLM providers

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wordbender.git
cd wordbender
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Create a `.env` file with your API keys:
```bash
# This will create a .env.example file
uv run python wordbender.py config --setup

# Copy the example file and add your keys
cp .env.example .env
```

4. Edit `.env` and add at least one API key:
```bash
# Wordbender API keys
#
# Add your API keys below:

# OpenAI
OPENAI_API_KEY=

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-key-here

# OpenRouter
OPENROUTER_API_KEY=your-openrouter-key-here

# Custom
CUSTOM_API_KEY=
```

## Usage

### Interactive Mode (Recommended for beginners)

The easiest way to use Wordbender is through interactive mode:

```bash
uv run python wordbender.py
```

This will:
1. Display available wordlist types
2. Prompt you to select a type
3. Ask for seed words
4. Let you choose generation options
5. Select an LLM provider and model
6. Generate and save your wordlist

### Direct Generation

Generate wordlists directly from the command line:

```bash
# Generate password wordlist with specific seeds
uv run python wordbender.py generate password -s john -s smith -s acme -l 200

# Generate subdomain wordlist
uv run python wordbender.py generate subdomain -s google -s tech -l 100

# Specify output file
uv run python wordbender.py generate password -s admin -o custom_passwords.txt

# Append to existing file
uv run python wordbender.py generate subdomain -s api -s dev -o subdomains.txt --append
```

### Batch Processing

Process multiple seed word sets from a file:

```bash
# Create a seed file
cat > seeds.txt << EOF
apple
microsoft
google
amazon
EOF

# Generate wordlists for each seed
uv run python wordbender.py batch seeds.txt subdomain

# With custom options
uv run python wordbender.py batch seeds.txt password -l 150 -o batch_output.txt
```

### Configuration Management

```bash
# Show current configuration
uv run python wordbender.py config --show

# Run setup wizard (interactive configuration)
uv run python wordbender.py config --setup

# Set a specific API key
uv run python wordbender.py config --set-key anthropic YOUR_API_KEY

# Set default preferences
uv run python wordbender.py config --set-preference default_provider anthropic
uv run python wordbender.py config --set-preference default_wordlist_length 150

# Reset all preferences to defaults
uv run python wordbender.py config --reset
```

## Wordlist Types

### Password Wordlists
- Generates base words for password mutation tools (like Hashcat)
- Focuses on alphanumeric words (3-30 characters)
- Includes semantically related words, variations, and compound words
- Output: `password_base_wordlist.txt`

### Subdomain Wordlists
- Generates potential subdomain names for enumeration
- Creates DNS-compliant labels (lowercase, alphanumeric with hyphens)
- Includes common patterns, department names, and service indicators
- Output: `subdomain_wordlist.txt`

## Supported LLM Providers and Models

### Anthropic (Direct API)
- Claude 3 Opus (`claude-3-opus-20240229`)
- Claude 3 Sonnet (`claude-3-sonnet-20240229`)
- Claude 3 Haiku (`claude-3-haiku-20240307`)
- Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- Claude 3.5 Haiku (`claude-3-5-haiku-20241022`)
- Claude Opus 4 (`claude-opus-4-20250514`)
- Claude Sonnet 4 (`claude-sonnet-4-20250514`)

### OpenRouter
- Claude 3 Opus (`anthropic/claude-3-opus`)
- GPT-4 Turbo (`openai/gpt-4-turbo-preview`)

## Command Reference

### Global Options
- `-h, --help`: Show help message

### Generate Command
```bash
uv run python wordbender.py generate [OPTIONS] WORDLIST_TYPE
```

Options:
- `-s, --seed TEXT`: Seed word(s) to base generation on (required, multiple allowed)
- `-l, --length INTEGER`: Number of words to generate (default: 100)
- `-o, --output PATH`: Output file path (default: auto-generated based on type)
- `--append`: Append to output file instead of overwriting
- `-p, --provider TEXT`: LLM provider to use
- `-m, --model TEXT`: Specific model to use
- `-i, --instructions TEXT`: Additional instructions for the LLM

### Batch Command
```bash
uv run python wordbender.py batch [OPTIONS] SEED_FILE WORDLIST_TYPE
```

Options:
- `-l, --length INTEGER`: Words to generate per seed (default: 100)
- `-o, --output PATH`: Output file path
- `-p, --provider TEXT`: LLM provider to use
- `-b, --batch-size INTEGER`: Seeds to process per batch (default: 5)

### Config Command
```bash
uv run python wordbender.py config [OPTIONS]
```

Options:
- `--setup`: Run interactive setup wizard
- `--show`: Display current configuration
- `--set-key TEXT TEXT`: Set API key for a provider
- `--set-preference TEXT TEXT`: Set a preference value
- `--reset`: Reset all preferences to defaults

## Examples

### Security Assessment Workflow

1. Generate password wordlist for a company:
```bash
uv run python wordbender.py generate password \
  -s acmecorp -s acme -s 2024 -s enterprise \
  -l 500 -o acme_passwords.txt
```

2. Generate subdomain wordlist:
```bash
uv run python wordbender.py generate subdomain \
  -s acme -s corp -s internal \
  -l 200 -o acme_subdomains.txt
```

3. Batch process multiple targets:
```bash
cat > targets.txt << EOF
facebook
twitter
linkedin
instagram
EOF

uv run python wordbender.py batch targets.txt subdomain \
  -l 100 -o social_media_subdomains.txt
```

4. Generate mutations with Hashcat (or similar)

### Using Different Providers

```bash
# Use Anthropic directly with Claude 3.5 Sonnet
uv run python wordbender.py generate password \
  -s admin -p anthropic -m claude-3-5-sonnet-20241022

# Use OpenRouter with GPT-4
uv run python wordbender.py generate subdomain \
  -s api -p openrouter -m openai/gpt-4-turbo-preview

# Interactive mode will show all available providers and models
uv run python wordbender.py
```

## Troubleshooting

### No API Keys Configured
If you see "No API keys configured!", ensure:
1. You have created a `.env` file (not just `.env.example`)
2. At least one API key is properly set in the `.env` file
3. The API key variable names match exactly (e.g., `ANTHROPIC_API_KEY`)

### Rate Limiting
If you encounter rate limiting:
- The tool automatically retries with exponential backoff
- Consider using batch processing with smaller batch sizes
- Switch to a different provider temporarily

### Invalid Words Generated
Each wordlist type has specific validation rules:
- **Passwords**: Only alphanumeric, 3-30 characters
- **Subdomains**: Lowercase, alphanumeric with hyphens (not at start/end)

Words that don't meet criteria are automatically filtered out.

## Development

### Running Development Tools

```bash
# Format code, sort imports, and lint
uv run isort . && uv run black . && uv run flake8 .

# Individual tools
uv run black .      # Format code
uv run isort .      # Sort imports
uv run flake8 .     # Run linter
```

### Adding New Wordlist Types

1. Create a new file in `wordlist_generators/`
2. Inherit from `WordlistGenerator` base class
3. Implement required methods:
   - `_get_default_output_path()`
   - `_get_system_prompt()`
   - `_validate_word()`
4. The new type will be automatically discovered

### Adding New LLM Providers

1. Create a new file in `llm_services/`
2. Inherit from `LlmService` base class
3. Implement required properties and methods:
   - `model_name` property
   - `provider` property
   - `_call_api()` method
4. Add the provider to `LlmProvider` enum if needed

## License

[TODO]

## Contributing

[TODO]
