import logging
from typing import Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from yaspin import yaspin

from cli.factories import GeneratorFactory, LlmServiceFactory
from cli.session import InteractiveSession
from config import Config
from llm_services.llm_service import LlmProvider, LlmService
from wordlist_generators.wordlist_generator import WordlistGenerator

console = Console()

__version__ = "0.1.0"
__author__ = "Ben Eisner (@backuardo)"

BANNER = f"""\
       ██╗    ██╗ ██████╗ ██████╗ ██████╗
       ██║    ██║██╔═══██╗██╔══██╗██╔══██╗
       ██║ █╗ ██║██║   ██║██████╔╝██║  ██║
       ██║███╗██║██║   ██║██╔══██╗██║  ██║
       ╚███╔███╔╝╚██████╔╝██║  ██║██████╔╝
        ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═════╝
██████╗ ███████╗███╗   ██╗██████╗ ███████╗██████╗
██╔══██╗██╔════╝████╗  ██║██╔══██╗██╔════╝██╔══██╗
██████╔╝█████╗  ██╔██╗ ██║██║  ██║█████╗  ██████╔╝
██╔══██╗██╔══╝  ██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
██████╔╝███████╗██║ ╚████║██████╔╝███████╗██║  ██║
╚═════╝ ╚══════╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
{__author__}
version {__version__}
"""


class WordbenderApp:
    """Main CLI application controller."""

    def __init__(self, log_level: Optional[str] = None):
        self.config = Config()
        self.generator_factory = GeneratorFactory()
        self.llm_factory = LlmServiceFactory(self.config)
        if log_level:
            logging.basicConfig(
                level=getattr(logging, log_level.upper()),
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def display_banner():
        """Display the application banner."""
        console.print(Panel(Text(BANNER, style="bold cyan"), border_style="cyan"))
        console.print(
            "An LLM-powered targeted wordlist generator for penetration testing and security assessments.", style="dim"
        )
        console.print()

    def check_configuration(self) -> bool:
        """Check if the application is properly configured."""
        if not self.config.check_api_keys():
            console.print("\n[red]No API keys configured![/red]")
            console.print("Run: [cyan]wordbender config --setup[/cyan]")
            return False
        return True

    def generate_wordlist(
        self,
        generator: WordlistGenerator,
        llm_service: LlmService,
        seed_words: List[str],
        options: Dict,
    ) -> bool:
        """Generate a wordlist with the given parameters."""
        for word in seed_words:
            if word and word.strip():
                generator.add_seed_words(word.strip())
            else:
                console.print("[yellow]Skipping empty seed word[/yellow]")

        generator.wordlist_length = options.get("length", 100)

        if "instructions" in options:
            generator.additional_instructions = options["instructions"]

        if "output_file" in options:
            output_file = options["output_file"]
            if output_file:
                generator.output_file = output_file

        with yaspin(text="Contacting LLM service...", color="cyan") as spinner:
            try:
                spinner.text = "Generating wordlist..."
                words = generator.generate(llm_service)
                spinner.ok("✓")
                if words is None:
                    console.print("[red]No words generated[/red]")
                    return False
                console.print(f"[green]Generated {len(words)} unique words[/green]")

                if len(words) <= 20:
                    console.print("\n[dim]Sample words:[/dim]")
                    for word in words[:5]:
                        console.print(f"  • {word}")
                    if len(words) > 5:
                        console.print("  ...")

            except Exception as e:
                spinner.fail("✗")
                console.print(f"[red]Generation failed: {e}[/red]")
                return False

        try:
            generator.save(append=options.get("append", False))
            console.print(f"[green]✓ Saved to: {generator.output_file}[/green]")

            # Show usage instructions
            if hasattr(generator, "get_usage_instructions"):
                console.print(
                    f"\n[bold cyan]{generator.get_usage_instructions()}[/bold cyan]"
                )

            return True
        except Exception as e:
            console.print(f"[red]Failed to save: {e}[/red]")
            return False

    def run_interactive_session(self):
        """Run the interactive mode."""
        self.display_banner()

        if not self.check_configuration():
            return

        session = InteractiveSession(
            self.config, self.generator_factory, self.llm_factory
        )

        wordlist_type = session.select_wordlist_type()
        if not wordlist_type:
            return

        # Create generator early so we can show hints
        generator = self.generator_factory.create(wordlist_type)
        if not generator:
            console.print(f"[red]Failed to create {wordlist_type} generator[/red]")
            console.print(
                f"[dim]Available types: "
                f"{', '.join(self.generator_factory.available_types)}[/dim]"
            )
            return

        seed_words = session.get_seed_words(generator)
        if not seed_words:
            return

        options = session.get_generation_options()

        service_selection = session.select_llm_service()
        if not service_selection:
            return

        provider, model = service_selection
        llm_service = self.llm_factory.create(provider, model)
        if not llm_service:
            console.print(f"[red]Failed to create LLM service for {provider}[/red]")
            if model:
                console.print(f"[dim]Model: {model}[/dim]")
            return

        self._display_generation_summary(
            wordlist_type, seed_words, options, provider, model
        )

        if session.confirm_generation():
            self.generate_wordlist(generator, llm_service, seed_words, options)

    def _display_generation_summary(
        self,
        wordlist_type: str,
        seed_words: List[str],
        options: Dict,
        provider: str,
        model: Optional[str],
    ):
        """Display a summary of the generation parameters."""
        console.print("\n[bold]Generation Summary:[/bold]")
        table = Table(show_header=False, box=None)
        table.add_row("Type:", wordlist_type)
        table.add_row("Seeds:", ", ".join(seed_words))
        table.add_row("Length:", str(options.get("length", 100)))

        provider_enum = LlmProvider.get_by_name(provider)
        provider_display = provider_enum.display_name if provider_enum else provider
        table.add_row("Provider:", provider_display)

        if model:
            table.add_row("Model:", model)

        console.print(table)
