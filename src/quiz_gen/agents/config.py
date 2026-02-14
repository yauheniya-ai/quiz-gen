#!/usr/bin/env python3
"""
Configuration for multi-agent system
Manages API keys, model selection, and agent settings
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for all agents in the quiz generation system"""

    # ============================================================================
    # API Keys
    # ============================================================================
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None

    # ============================================================================
    # Optional API Base URLs (for custom endpoints or proxies)
    # ============================================================================
    openai_api_base: Optional[str] = None
    anthropic_api_base: Optional[str] = None
    mistral_api_base: Optional[str] = None
    gemini_api_base: Optional[str] = None

    # ============================================================================
    # Provider-Specific Settings
    # ============================================================================
    anthropic_max_tokens: int = 4096  # Required by Anthropic API

    # ============================================================================
    # Model Configurations
    # ============================================================================
    conceptual_provider: str = "openai"
    practical_provider: str = "anthropic"
    validator_provider: str = "openai"
    refiner_provider: str = "openai"
    judge_provider: str = "anthropic"
    conceptual_model: str = "gpt-4o"
    practical_model: str = "claude-sonnet-4-20250514"
    validator_model: str = "gpt-4o"
    refiner_model: str = "gpt-4o"
    judge_model: str = "claude-sonnet-4-20250514"

    # ==========================================================================
    # Generation Settings
    # ==========================================================================

    # ============================================================================
    # Workflow Settings
    # ============================================================================
    auto_accept_valid: bool = False  # Auto-accept if validation passes
    save_intermediate_results: bool = True
    output_directory: str = "data/quizzes"

    # ============================================================================
    # Validation Settings
    # ============================================================================
    min_validation_score: int = 6  # Minimum score out of 10 to pass
    strict_validation: bool = True

    # ============================================================================
    # Retry Settings
    # ============================================================================
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    # ============================================================================
    # Logging Settings
    # ============================================================================
    verbose: bool = True
    log_file: Optional[str] = None

    # ============================================================================
    # Additional Metadata
    # ============================================================================
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Load from environment variables if not provided"""
        # Load API keys from environment
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")

        if not self.anthropic_api_key:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if not self.mistral_api_key:
            self.mistral_api_key = os.getenv("MISTRAL_API_KEY")

        if not self.gemini_api_key:
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        if not self.cohere_api_key:
            self.cohere_api_key = os.getenv("COHERE_API_KEY")

        # Load optional base URLs from environment
        if not self.openai_api_base:
            self.openai_api_base = os.getenv("OPENAI_API_BASE")

        if not self.anthropic_api_base:
            self.anthropic_api_base = os.getenv("ANTHROPIC_BASE_URL")

        if not self.mistral_api_base:
            self.mistral_api_base = os.getenv("MISTRAL_API_BASE")

        if not self.gemini_api_base:
            self.gemini_api_base = os.getenv("GEMINI_API_BASE")

        # Create output directory if it doesn't exist
        if self.output_directory:
            Path(self.output_directory).mkdir(parents=True, exist_ok=True)


    def validate(self) -> None:
        """
        Validate configuration

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        errors = []

        # Check required API keys for selected providers
        provider_key_map = {
            "openai": (self.openai_api_key, "OPENAI_API_KEY"),
            "anthropic": (self.anthropic_api_key, "ANTHROPIC_API_KEY"),
            "cohere": (self.cohere_api_key, "COHERE_API_KEY"),
            "mistral": (self.mistral_api_key, "MISTRAL_API_KEY"),
            "gemini": (self.gemini_api_key, "GEMINI_API_KEY"),
            "google": (self.gemini_api_key, "GOOGLE_API_KEY"),
        }

        for provider in {
            self.conceptual_provider,
            self.practical_provider,
            self.judge_provider,
            self.validator_provider,
            self.refiner_provider,
        }:
            key_value, env_name = provider_key_map.get(provider, (None, None))
            if env_name and not key_value:
                errors.append(
                    f"{env_name} is required for provider '{provider}' (set via parameter or environment variable)"
                )

        # Validate model names
        if not self.conceptual_provider:
            errors.append("conceptual_provider must be set")
        if not self.practical_provider:
            errors.append("practical_provider must be set")
        if not self.judge_provider:
            errors.append("judge_provider must be set")
        if not self.validator_provider:
            errors.append("validator_provider must be set")
        if not self.refiner_provider:
            errors.append("refiner_provider must be set")

        if not self.conceptual_model:
            errors.append("conceptual_model must be set")
        if not self.practical_model:
            errors.append("practical_model must be set")
        if not self.judge_model:
            errors.append("judge_model must be set")
        if not self.validator_model:
            errors.append("validator_model must be set")
        if not self.refiner_model:
            errors.append("refiner_model must be set")

        # Model identifiers are provider-specific and change over time; avoid hardcoded lists.

        # Base URLs are optional and only used for custom endpoints or proxies

        # Validate validation score
        if not 0 <= self.min_validation_score <= 10:
            errors.append(
                f"min_validation_score must be between 0 and 10, got {self.min_validation_score}"
            )

        if errors:
            raise ValueError(
                "Configuration validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            "openai_api_key": "***" if self.openai_api_key else None,
            "anthropic_api_key": "***" if self.anthropic_api_key else None,
            "mistral_api_key": "***" if self.mistral_api_key else None,
            "gemini_api_key": "***" if self.gemini_api_key else None,
            "cohere_api_key": "***" if self.cohere_api_key else None,
            "openai_api_base": self.openai_api_base,
            "anthropic_api_base": self.anthropic_api_base,
            "mistral_api_base": self.mistral_api_base,
            "gemini_api_base": self.gemini_api_base,
            "anthropic_max_tokens": self.anthropic_max_tokens,
            "conceptual_provider": self.conceptual_provider,
            "practical_provider": self.practical_provider,
            "judge_provider": self.judge_provider,
            "validator_provider": self.validator_provider,
            "refiner_provider": self.refiner_provider,
            "conceptual_model": self.conceptual_model,
            "practical_model": self.practical_model,
            "judge_model": self.judge_model,
            "validator_model": self.validator_model,
            "refiner_model": self.refiner_model,
            "auto_accept_valid": self.auto_accept_valid,
            "save_intermediate_results": self.save_intermediate_results,
            "output_directory": self.output_directory,
            "min_validation_score": self.min_validation_score,
            "strict_validation": self.strict_validation,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "verbose": self.verbose,
            "log_file": self.log_file,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict) -> "AgentConfig":
        """Create configuration from dictionary"""
        return cls(**config_dict)

    @classmethod
    def from_env_file(cls, env_file: str = ".env") -> "AgentConfig":
        """
        Load configuration from .env file

        Args:
            env_file: Path to .env file

        Returns:
            AgentConfig instance
        """
        from dotenv import load_dotenv

        load_dotenv(env_file)
        return cls()

    def save(self, filepath: str) -> None:
        """
        Save configuration to JSON file (without API keys)

        Args:
            filepath: Path to save configuration
        """
        import json

        config_dict = self.to_dict()

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)

        if self.verbose:
            print(f"Configuration saved to: {filepath}")

    @classmethod
    def load(cls, filepath: str) -> "AgentConfig":
        """
        Load configuration from JSON file

        Args:
            filepath: Path to configuration file

        Returns:
            AgentConfig instance
        """
        import json

        with open(filepath, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        return cls.from_dict(config_dict)

    def print_summary(self) -> None:
        """Print configuration summary"""
        print("=" * 70)
        print("Agent Configuration Summary")
        print("=" * 70)
        print(f"OpenAI API Key: {'✓ Set' if self.openai_api_key else '✗ Missing'}")
        print(f"Anthropic API Key: {'✓ Set' if self.anthropic_api_key else '✗ Missing'}")
        if self.anthropic_api_base:
            print(f"  └─ Custom Base URL: {self.anthropic_api_base}")
        print(f"Mistral API Key: {'✓ Set' if self.mistral_api_key else '✗ Missing'}")
        print(f"Gemini API Key: {'✓ Set' if self.gemini_api_key else '✗ Missing'}")
        print(f"Cohere API Key: {'✓ Set' if self.cohere_api_key else '✗ Missing'}")
        print("\nModels:")
        print(
            f"  Conceptual Generator: {self.conceptual_provider} / {self.conceptual_model}"
        )
        print(
            f"  Practical Generator: {self.practical_provider} / {self.practical_model}"
        )
        print(f"  Validator: {self.validator_provider} / {self.validator_model}")
        print(f"  Refiner: {self.refiner_provider} / {self.refiner_model}")
        print(f"  Judge: {self.judge_provider} / {self.judge_model}")
        print("\nValidation Settings:")
        print(f"  Min Validation Score: {self.min_validation_score}/10")
        print(f"  Strict Validation: {self.strict_validation}")
        print("\nWorkflow Settings:")
        print(f"  Auto-accept Valid: {self.auto_accept_valid}")
        print(f"  Save Intermediate: {self.save_intermediate_results}")
        print(f"  Output Directory: {self.output_directory}")
        print("\nRetry Settings:")
        print(f"  Max Retries: {self.max_retries}")
        print(f"  Retry Delay: {self.retry_delay}s")
        print("=" * 70)


# Example usage and testing
if __name__ == "__main__":
    # Example 1: Load from environment variables
    print("Example 1: Load from environment variables")
    config = AgentConfig()

    try:
        config.validate()
        config.print_summary()
    except ValueError as e:
        print(f"Validation error: {e}")

    print("\n")

    # Example 2: Create with custom settings
    print("Example 2: Create with custom settings")
    custom_config = AgentConfig(
        openai_api_key="sk-test-key",
        anthropic_api_key="sk-ant-test-key",
        min_validation_score=7,
        auto_accept_valid=True,
        verbose=True,
    )
    custom_config.print_summary()

    print("\n")

    # Example 3: Save and load configuration
    print("Example 3: Save and load configuration")
    test_config_path = "test_config.json"
    custom_config.save(test_config_path)
    loaded_config = AgentConfig.load(test_config_path)
    print("✓ Configuration saved and loaded successfully")

    # Cleanup
    import os

    if os.path.exists(test_config_path):
        os.remove(test_config_path)
