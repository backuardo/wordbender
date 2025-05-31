import sys
from pathlib import Path
from typing import List, Optional

import click
from prompt_toolkit import prompt
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table

from cli.app import WordbenderApp
from cli.factories import GeneratorFactory, LlmServiceFactory
from config import Config
from llm_services.llm_service import LlmProvider

console = Console()


@click.command(name="config")
@click.option("--setup", is_flag=True, help="Setup wizard for API keys")
@click.option("--show", is_flag=True, help="Show current configuration")
@click.option("--provider", help="Configure specific provider")
@click.option("--key", help="API key for the provider")
def config_cmd(setup, show, provider, key):
    """Configure Wordbender settings and API keys."""
    config = Config()

    if setup:
        _run_setup_wizard(config)
    elif show:
        _show_configuration(config)
    elif provider and key:
        _set_provider_key(config, provider, key)
    else:
        console.print(
            "Use --setup for interactive setup or --show to view configuration"
        )


@click.command(name="generate")
@click.argument("wordlist_type")
@click.option("-s", "--seed", multiple=True, required=True, help="Seed words")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("-l", "--length", type=int, default=100, help="Target length")
@click.option("-p", "--provider", help="LLM provider to use")
@click.option("-m", "--model", help="Specific model to use")
@click.option("-a", "--append", is_flag=True, help="Append to existing file")
@click.option("--instructions", help="Additional instructions for the LLM")
def generate_cmd(
    wordlist_type, seed, output, length, provider, model, append, instructions
):
    """Generate a wordlist from seed words."""
    app = WordbenderApp()
    app.display_banner()

    if not app.check_configuration():
        sys.exit(1)

    generator_factory = GeneratorFactory()
    llm_factory = LlmServiceFactory(app.config)

    if wordlist_type not in generator_factory.available_types:
        console.print(f"[red]Unknown wordlist type: {wordlist_type}[/red]")
        console.print(
            f"Available types: {', '.join(generator_factory.available_types)}"
        )
        sys.exit(1)

    generator = generator_factory.create(
        wordlist_type, Path(output) if output else None
    )
    if not generator:
        sys.exit(1)

    provider_name = app.config.select_provider(provider)
    if not provider_name:
        sys.exit(1)

    llm_service = llm_factory.create(provider_name, model)
    if not llm_service:
        sys.exit(1)

    console.print(f"\n[bold]Generating {wordlist_type} wordlist...[/bold]")
    console.print(f"Seeds: {', '.join(seed)}")
    console.print(f"Provider: {provider_name}")
    if model:
        console.print(f"Model: {model}")
    console.print()

    options = {
        "length": length,
        "append": append,
    }
    if instructions:
        options["instructions"] = instructions

    success = app.generate_wordlist(generator, llm_service, list(seed), options)
    if not success:
        sys.exit(1)


@click.command(name="batch")
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("wordlist_type")
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("-l", "--length", type=int, default=100, help="Target length per batch")
@click.option("-p", "--provider", help="LLM provider to use")
@click.option("-b", "--batch-size", type=int, default=5, help="Seeds per batch")
def batch_cmd(input_file, wordlist_type, output, length, provider, batch_size):
    """Generate wordlists from a file of seed words."""
    processor = BatchProcessor()
    processor.process(
        input_file=Path(input_file),
        wordlist_type=wordlist_type,
        output=Path(output) if output else None,
        length=length,
        provider=provider,
        batch_size=batch_size,
    )


class BatchProcessor:
    """Handles batch processing of seed words."""

    def __init__(self):
        self.config = Config()
        self.generator_factory = GeneratorFactory()
        self.llm_factory = LlmServiceFactory(self.config)

    def process(
        self,
        input_file: Path,
        wordlist_type: str,
        output: Optional[Path],
        length: int,
        provider: Optional[str],
        batch_size: int,
    ):
        """Process a batch of seed words."""
        seed_words = self._load_seed_words(input_file)
        if not seed_words:
            return

        if not self._validate_wordlist_type(wordlist_type):
            return

        provider_name = self._select_provider(provider)
        if not provider_name:
            return

        console.print(f"[bold]Found {len(seed_words)} seed words[/bold]")

        all_words = self._process_all_batches(
            seed_words, wordlist_type, length, provider_name, batch_size
        )

        if all_words:
            output_path = output or Path(f"{wordlist_type}_batch_wordlist.txt")
            self._save_results(all_words, output_path)

    def _load_seed_words(self, input_file: Path) -> List[str]:
        """Load seed words from file."""
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                seed_words = [line.strip() for line in f if line.strip()]
            if not seed_words:
                console.print("[red]No seed words found in file[/red]")
            return seed_words
        except FileNotFoundError:
            console.print(f"[red]File not found: {input_file}[/red]")
            return []
        except PermissionError:
            console.print(f"[red]Permission denied reading file: {input_file}[/red]")
            return []
        except UnicodeDecodeError:
            console.print(f"[red]File contains invalid characters: {input_file}[/red]")
            return []
        except Exception as e:
            console.print(f"[red]Error reading file: {e}[/red]")
            return []

    def _validate_wordlist_type(self, wordlist_type: str) -> bool:
        """Validate the wordlist type."""
        if wordlist_type not in self.generator_factory.available_types:
            console.print(f"[red]Unknown wordlist type: {wordlist_type}[/red]")
            console.print(
                f"Available types: {', '.join(self.generator_factory.available_types)}"
            )
            return False
        return True

    def _select_provider(self, provider: Optional[str]) -> Optional[str]:
        """Select and validate provider."""
        provider_name = self.config.select_provider(provider)
        if not provider_name:
            console.print("[red]No valid provider selected[/red]")
        return provider_name

    def _process_all_batches(
        self,
        seed_words: List[str],
        wordlist_type: str,
        length: int,
        provider_name: str,
        batch_size: int,
    ) -> List[str]:
        """Process all batches of seed words."""
        all_words = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:

            task_id = progress.add_task("Processing batches...", total=len(seed_words))

            for i in range(0, len(seed_words), batch_size):
                batch = seed_words[i : i + batch_size]
                try:
                    words = self._process_single_batch(
                        batch, wordlist_type, length, provider_name
                    )
                except Exception as e:
                    batch_num = i // batch_size + 1
                    console.print(
                        f"[yellow]Warning: Batch {batch_num} failed: {e}[/yellow]"
                    )
                    words = []
                all_words.extend(words)
                progress.update(task_id, advance=len(batch))

        return all_words

    def _process_single_batch(
        self, batch: List[str], wordlist_type: str, length: int, provider_name: str
    ) -> List[str]:
        """Process a single batch of seed words."""
        try:
            generator = self.generator_factory.create(wordlist_type)
            if not generator:
                return []

            generator.wordlist_length = length

            llm_service = self.llm_factory.create(provider_name)
            if not llm_service:
                return []

            for word in batch:
                generator.add_seed_words(word)

            return generator.generate(llm_service)

        except ValueError as e:
            console.print(f"[yellow]Warning: Invalid input in batch: {e}[/yellow]")
            return []
        except RuntimeError as e:
            console.print(f"[yellow]Warning: LLM service error: {e}[/yellow]")
            return []
        except Exception as e:
            console.print(
                f"[yellow]Warning: Unexpected error: {type(e).__name__}: {e}[/yellow]"
            )
            return []

    def _save_results(self, words: List[str], output_path: Path):
        """Save the combined results."""
        unique_words = list(dict.fromkeys(words))

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            console.print(
                f"[red]Permission denied creating directory: {output_path.parent}[/red]"
            )
            return
        except Exception as e:
            console.print(f"[red]Failed to create directory: {e}[/red]")
            return

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                for word in unique_words:
                    f.write(f"{word}\n")

            console.print(
                f"\n[green]✓ Generated {len(unique_words)} unique words[/green]"
            )
            console.print(f"[green]✓ Saved to: {output_path}[/green]")

        except Exception as e:
            console.print(f"[red]Failed to save results: {e}[/red]")


def _run_setup_wizard(config: Config):
    """Run the interactive setup wizard."""
    console.print("[bold]Wordbender Setup Wizard[/bold]\n")

    if not Path(".env").exists():
        config.create_example_env()
        console.print("[green]✓[/green] Created .env.example file")
        console.print("Copy it to .env and add your API keys\n")

    for provider_enum in LlmProvider.requiring_api_keys():
        current_key = config.get_api_key(provider_enum.internal_name)

        if current_key:
            console.print(
                f"[green]✓[/green] {provider_enum.display_name} already configured"
            )
        else:
            console.print(f"\n[yellow]Configure {provider_enum.display_name}[/yellow]")
            key_input = prompt(
                f"Enter {provider_enum.env_var} (or press Enter to skip): ",
                is_password=True,
            )

            if key_input.strip():
                try:
                    config.set_api_key(provider_enum.internal_name, key_input.strip())
                    console.print(
                        f"[green]✓[/green] {provider_enum.display_name} configured"
                    )
                except ValueError as e:
                    console.print(f"[red]Invalid API key: {e}[/red]")


def _show_configuration(config: Config):
    """Display current configuration."""
    console.print("[bold]Current Configuration:[/bold]\n")

    table = Table("Provider", "Status", "Environment Variable")
    for provider_enum in LlmProvider:
        if provider_enum.requires_api_key:
            configured = config.get_api_key(provider_enum.internal_name) is not None
            status = (
                "[green]Configured[/green]"
                if configured
                else "[red]Not configured[/red]"
            )
            env_var = provider_enum.env_var or "N/A"
        else:
            status = "[blue]No key needed[/blue]"
            env_var = "N/A"

        table.add_row(provider_enum.display_name, status, env_var)

    console.print(table)

    console.print("\n[bold]Preferences:[/bold]")
    prefs = config.get_preferences()
    pref_table = Table(show_header=False)
    for key, value in prefs.items():
        display_key = key.replace("_", " ").title() + ":"
        pref_table.add_row(display_key, str(value))
    console.print(pref_table)


def _set_provider_key(config: Config, provider: str, key: str):
    """Set API key for a specific provider."""
    try:
        config.set_api_key(provider, key)
        console.print(f"[green]✓[/green] Configured {provider}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
