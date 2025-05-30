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

        # Create completer with valid choices
        valid_choices = [str(i) for i in range(1, len(available_types) + 1)]
        choice = prompt("\nChoice: ", completer=WordCompleter(valid_choices))

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(available_types):
                return available_types[idx]
        except (ValueError, IndexError):
            pass

        console.print("[red]Invalid choice[/red]")
        return None

    def get_seed_words(self) -> List[str]:
        """Get seed words from user interactively."""
        console.print("\n[bold]Enter seed words:[/bold]")
        console.print(
            "[dim]Enter words one at a time, press Enter twice when done[/dim]\n"
        )

        seed_words = []
        while True:
            word = prompt(f"Word {len(seed_words) + 1}: ").strip()
            if not word:
                if seed_words:
                    break
                console.print("[yellow]Please enter at least one seed word[/yellow]")
            else:
                seed_words.append(word)
                console.print(f"[green]✓[/green] Added: {word}")

        return seed_words

    def get_generation_options(self) -> Dict:
        """Get additional generation options from user."""
        options = {}

        console.print(
            "\n[bold]Additional options:[/bold] [dim](press Enter for defaults)[/dim]"
        )

        # Wordlist length
        length_input = prompt("Wordlist length [100]: ").strip()
        options["length"] = int(length_input) if length_input.isdigit() else 100

        # Additional instructions
        instructions = prompt("Additional instructions (optional): ").strip()
        if instructions:
            options["instructions"] = instructions

        # Output file
        output_file = prompt("Output file [auto]: ").strip()
        if output_file:
            from pathlib import Path

            options["output_file"] = Path(output_file)

        # Append mode
        append_input = prompt("Append to file? [y/N]: ").strip().lower()
        options["append"] = append_input in ["y", "yes"]

        return options

    def select_llm_service(self) -> Optional[Tuple[str, Optional[str]]]:
        """Select LLM provider and model."""
        # Get providers that are configured
        available_providers = []

        for provider_name in self.llm_factory.available_providers:
            provider_enum = LlmProvider.get_by_name(provider_name)
            if not provider_enum:
                continue

            # Check if provider is configured (has API key if required)
            if provider_enum.requires_api_key:
                if self.config.get_api_key(provider_name):
                    available_providers.append(provider_name)
            else:
                available_providers.append(provider_name)

        if not available_providers:
            console.print("[red]No configured LLM providers found![/red]")
            return None

        # Select provider
        provider = self._select_provider(available_providers)
        if not provider:
            return None

        # Select model
        models = self.llm_factory.get_available_models(provider)
        if len(models) > 1:
            model = self._select_model(provider, models)
            return (provider, model) if model else None
        elif models:
            return (provider, models[0])

        return (provider, None)

    def _select_provider(self, available_providers: List[str]) -> Optional[str]:
        """Select a provider from available ones."""
        # Check for default preference
        prefs = self.config.get_preferences()
        default_provider = prefs.get("default_provider")

        if default_provider in available_providers and len(available_providers) == 1:
            return default_provider
        elif len(available_providers) == 1:
            return available_providers[0]

        # Let user choose
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
        except ValueError:
            pass

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
        except ValueError:
            pass

        return None

    def confirm_generation(self) -> bool:
        """Confirm generation with user."""
        response = prompt("\nProceed? [Y/n]: ").strip().lower()
        return response not in ["n", "no"]
