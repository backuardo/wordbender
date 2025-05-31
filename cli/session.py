from typing import Dict, List, Optional, Tuple

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from rich.console import Console
from rich.table import Table

from cli.factories import GeneratorFactory, LlmServiceFactory
from config import Config
from llm_services.llm_service import LlmProvider

console = Console()


class InteractiveSession:
    """Handles interactive user sessions."""

    def __init__(
        self,
        config: Config,
        generator_factory: GeneratorFactory,
        llm_factory: LlmServiceFactory,
    ):
        self.config = config
        self.generator_factory = generator_factory
        self.llm_factory = llm_factory

    def select_wordlist_type(self) -> Optional[str]:
        """Interactive menu to select wordlist type."""
        console.print("\n[bold]Select wordlist type:[/bold]")

        available_types = self.generator_factory.available_types
        if not available_types:
            console.print("[red]No wordlist generators found![/red]")
            return None

        table = Table(show_header=False, box=None)
        for idx, gen_type in enumerate(available_types, 1):
            description = self.generator_factory.get_description(gen_type)
            table.add_row(f"[cyan]{idx})[/cyan]", description)

        console.print(table)

        valid_choices = [str(i) for i in range(1, len(available_types) + 1)]
        choice = prompt("\nChoice: ", completer=WordCompleter(valid_choices))

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available_types):
                return available_types[idx]
            else:
                console.print(
                    f"[red]Invalid choice: Please select 1-{len(available_types)}[/red]"
                )
                return None
        except ValueError:
            console.print(f"[red]Invalid choice: '{choice}' is not a number[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            return None

    def get_seed_words(self, generator=None) -> List[str]:
        """Get seed words from user interactively."""
        console.print("\n[bold]Enter seed words:[/bold]")

        # Show hints if generator is provided
        if generator and hasattr(generator, "get_seed_hints"):
            console.print(f"\n[dim]{generator.get_seed_hints()}[/dim]\n")

        console.print(
            "[dim]Enter all your seed words separated by spaces or commas:[/dim]\n"
        )

        while True:
            input_text = prompt("Seed words: ").strip()
            if not input_text:
                console.print("[yellow]Please enter at least one seed word[/yellow]")
                continue

            # Split by both spaces and commas, filter empty strings
            seed_words = []
            for word in input_text.replace(",", " ").split():
                word = word.strip()
                if word:
                    seed_words.append(word)

            if seed_words:
                console.print(f"\n[green]✓[/green] Added {len(seed_words)} seed words:")
                for word in seed_words[:5]:  # Show first 5
                    console.print(f"  • {word}")
                if len(seed_words) > 5:
                    console.print(f"  • ... and {len(seed_words) - 5} more")
                return seed_words
            else:
                console.print("[yellow]No valid seed words found[/yellow]")

    def get_generation_options(self) -> Dict:
        """Get additional generation options from user."""
        options = {}

        console.print(
            "\n[bold]Additional options:[/bold] [dim](press Enter for defaults)[/dim]"
        )

        while True:
            length_input = prompt("Wordlist length [100]: ").strip()
            if not length_input:
                options["length"] = 100
                break
            elif length_input.isdigit():
                length = int(length_input)
                if 1 <= length <= 10000:
                    options["length"] = length
                    break
                else:
                    console.print(
                        "[yellow]Please enter a value between 1 and 10000[/yellow]"
                    )
            else:
                console.print("[yellow]Please enter a valid number[/yellow]")

        instructions = prompt("Additional instructions (optional): ").strip()
        if instructions:
            options["instructions"] = instructions

        output_file = prompt("Output file [auto]: ").strip()
        if output_file:
            from pathlib import Path

            try:
                path = Path(output_file)
                # Validate path is not a directory
                if path.exists() and path.is_dir():
                    console.print(
                        f"[yellow]'{output_file}' is a directory, not a file[/yellow]"
                    )
                else:
                    options["output_file"] = path
            except (OSError, ValueError) as e:
                console.print(f"[yellow]Invalid output path: {e}[/yellow]")

        append_input = prompt("Append to file? [y/N]: ").strip().lower()
        options["append"] = append_input in ["y", "yes"]

        return options

    def select_llm_service(self) -> Optional[Tuple[str, Optional[str]]]:
        """Select LLM provider and model."""
        available_providers = []

        for provider_name in self.llm_factory.available_providers:
            provider_enum = LlmProvider.get_by_name(provider_name)
            if not provider_enum:
                continue

            if provider_enum.requires_api_key:
                if self.config.get_api_key(provider_name):
                    available_providers.append(provider_name)
            else:
                available_providers.append(provider_name)

        if not available_providers:
            console.print("[red]No configured LLM providers found![/red]")
            return None

        provider = self._select_provider(available_providers)
        if not provider:
            return None

        models = self.llm_factory.get_available_models(provider)
        if len(models) > 1:
            model = self._select_model(provider, models)
            return (provider, model) if model else None
        elif models:
            return (provider, models[0])

        return (provider, None)

    def _select_provider(self, available_providers: List[str]) -> Optional[str]:
        """Select a provider from available ones."""
        prefs = self.config.get_preferences()
        default_provider = prefs.get("default_provider")

        if default_provider in available_providers and len(available_providers) == 1:
            return default_provider
        elif len(available_providers) == 1:
            return available_providers[0]

        console.print("\n[bold]Select LLM provider:[/bold]")
        table = Table(show_header=False, box=None)

        for idx, provider_name in enumerate(available_providers, 1):
            provider_enum = LlmProvider.get_by_name(provider_name)
            display_name = (
                provider_enum.display_name if provider_enum else provider_name
            )
            table.add_row(f"[cyan]{idx})[/cyan]", display_name)

        console.print(table)

        choice = prompt("\nChoice: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available_providers):
                return available_providers[idx]
            else:
                max_choice = len(available_providers)
                console.print(
                    f"[red]Invalid choice: Please select 1-{max_choice}[/red]"
                )
        except ValueError:
            console.print(f"[red]Invalid choice: '{choice}' is not a number[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        return None

    def _select_model(self, provider: str, models: List[str]) -> Optional[str]:
        """Select a model for the given provider."""
        console.print(f"\n[bold]Select model for {provider}:[/bold]")
        table = Table(show_header=False, box=None)

        for idx, model in enumerate(models, 1):
            table.add_row(f"[cyan]{idx})[/cyan]", model)

        console.print(table)

        choice = prompt("\nChoice: ")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return models[idx]
            else:
                console.print(
                    f"[red]Invalid choice: Please select 1-{len(models)}[/red]"
                )
        except ValueError:
            console.print(f"[red]Invalid choice: '{choice}' is not a number[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        return None

    def confirm_generation(self) -> bool:
        """Confirm generation with user."""
        response = prompt("\nProceed? [Y/n]: ").strip().lower()
        return response not in ["n", "no"]
