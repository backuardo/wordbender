import importlib
import inspect
import re
from pathlib import Path

from rich.console import Console

from config import Config
from llm_services.llm_service import LlmConfig, LlmProvider, LlmService
from wordlist_generators.wordlist_generator import WordlistGenerator

console = Console()


class ServiceDiscovery:
    """Discovers available services from the filesystem."""

    @staticmethod
    def discover_wordlist_generators() -> dict[str, type[WordlistGenerator]]:
        """Dynamically discover all wordlist generator classes."""
        generators: dict[str, type[WordlistGenerator]] = {}
        generator_dir = Path("wordlist_generators")

        try:
            if not generator_dir.exists():
                return generators
        except (OSError, PermissionError) as e:
            console.print(
                f"[yellow]Warning: Cannot access generators directory: {e}[/yellow]"
            )
            return generators

        for file_path in generator_dir.glob("*_wordlist_generator.py"):
            module_name = file_path.stem

            try:
                module = importlib.import_module(f"wordlist_generators.{module_name}")

                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, WordlistGenerator)
                        and obj != WordlistGenerator
                    ):
                        generator_name = name.replace("WordlistGenerator", "")
                        generator_type = ""
                        for i, char in enumerate(generator_name):
                            if i > 0 and char.isupper():
                                generator_type += "-"
                            generator_type += char.lower()
                        generators[generator_type] = obj

            except ImportError as e:
                console.print(
                    f"[yellow]Warning: Could not import {module_name}: {e}[/yellow]"
                )

        return generators

    @staticmethod
    def discover_llm_services() -> dict[str, dict[str, type[LlmService]]]:
        """Dynamically discover all LLM service classes grouped by provider."""
        services: dict[str, dict[str, type[LlmService]]] = {}
        service_dir = Path("llm_services")

        try:
            if not service_dir.exists():
                return services
        except (OSError, PermissionError) as e:
            console.print(
                f"[yellow]Warning: Cannot access services directory: {e}[/yellow]"
            )
            return services

        for file_path in service_dir.glob("*_llm_service.py"):
            if file_path.stem == "llm_service":
                continue

            module_name = file_path.stem

            try:
                module = importlib.import_module(f"llm_services.{module_name}")

                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, LlmService)
                        and obj != LlmService
                    ):
                        provider_name = ServiceDiscovery._get_provider_name(obj)
                        if provider_name:
                            if provider_name not in services:
                                services[provider_name] = {}

                            model_name = ServiceDiscovery._extract_model_name(name)
                            services[provider_name][model_name] = obj

            except ImportError as e:
                console.print(
                    f"[yellow]Warning: Could not import {module_name}: {e}[/yellow]"
                )

        return services

    @staticmethod
    def _get_provider_name(service_class: type[LlmService]) -> str | None:
        """Get provider name from service class by instantiating it."""
        try:
            dummy_config = LlmConfig(api_key="dummy")
            instance = service_class(dummy_config)
            return instance.provider.internal_name
        except Exception:
            class_name = service_class.__name__.lower()
            for provider in LlmProvider:
                if provider.internal_name in class_name:
                    return provider.internal_name
            return None

    @staticmethod
    def _extract_model_name(class_name: str) -> str:
        """Extract model name from class name."""
        name = class_name.replace("LlmService", "")

        for prefix in [
            "OpenRouter",
            "Anthropic",
            "OpenAI",
            "Local",
            "Groq",
            "Cohere",
            "Google",
        ]:
            name = name.replace(prefix, "")

        name = name.replace("Gpt", "GPT-")
        name = name.replace("Claude", "claude-")
        name = re.sub("([a-z0-9])([A-Z])", r"\1-\2", name)
        name = re.sub("([A-Z]+)([A-Z][a-z])", r"\1-\2", name)

        return name.lower().strip("-")


class GeneratorFactory:
    """Factory for creating wordlist generators."""

    def __init__(self):
        self._generators = ServiceDiscovery.discover_wordlist_generators()

    @property
    def available_types(self) -> list[str]:
        """Get list of available generator types."""
        return sorted(self._generators.keys())

    def create(
        self, generator_type: str, output_file: Path | None = None
    ) -> WordlistGenerator | None:
        """Create a generator instance by type."""
        generator_class = self._generators.get(generator_type)
        if not generator_class:
            return None
        try:
            return generator_class(output_file)
        except Exception as e:
            console.print(
                f"[red]Failed to create {generator_type} generator: {e}[/red]"
            )
            return None

    def get_description(self, generator_type: str) -> str:
        """Get description for a generator type from its docstring."""
        generator_class = self._generators.get(generator_type)
        if generator_class and generator_class.__doc__:
            return generator_class.__doc__.strip().split("\n")[0]
        return f"{generator_type.title()} wordlist generator"


class LlmServiceFactory:
    """Factory for creating LLM services."""

    def __init__(self, config: Config):
        self._config = config
        self._services = ServiceDiscovery.discover_llm_services()

    @property
    def available_providers(self) -> list[str]:
        """Get list of available providers that have implementations."""
        return sorted(self._services.keys())

    def get_available_models(self, provider: str) -> list[str]:
        """Get available models for a provider."""
        return sorted(self._services.get(provider, {}).keys())

    def create(self, provider: str, model: str | None = None) -> LlmService | None:
        """Create an LLM service instance."""
        provider_services = self._services.get(provider, {})
        if not provider_services:
            return None

        model_to_use = self._determine_model(provider, model, provider_services)
        if not model_to_use:
            return None

        service_class = provider_services.get(model_to_use)
        if not service_class:
            return None

        provider_enum = LlmProvider.get_by_name(provider)
        if not provider_enum:
            return None

        api_key = None
        if provider_enum.requires_api_key:
            api_key = self._config.get_api_key(provider)
            if not api_key:
                console.print(
                    f"[red]No API key configured for {provider_enum.display_name}[/red]"
                )
                return None

        config = LlmConfig(api_key=api_key)

        try:
            return service_class(config)
        except ValueError as e:
            console.print(f"[red]Invalid configuration: {e}[/red]")
            return None
        except AttributeError as e:
            console.print(f"[red]Service implementation error: {e}[/red]")
            return None
        except Exception as e:
            console.print(
                f"[red]Failed to create LLM service: {type(e).__name__}: {e}[/red]"
            )
            return None

    def _determine_model(
        self,
        provider: str,
        requested_model: str | None,
        available_models: dict[str, type[LlmService]],
    ) -> str | None:
        """Determine which model to use based on request and preferences."""
        if requested_model and requested_model in available_models:
            return requested_model

        prefs = self._config.get_preferences()
        default_model = prefs.get(f"default_{provider}_model")
        if (
            default_model
            and isinstance(default_model, str)
            and default_model in available_models
        ):
            return str(default_model)

        if available_models:
            return next(iter(available_models.keys()))

        return None
