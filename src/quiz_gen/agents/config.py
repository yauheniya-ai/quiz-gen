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
    
    # ============================================================================
    # Optional API Base URLs (for custom endpoints or proxies)
    # ============================================================================
    openai_api_base: Optional[str] = None
    anthropic_api_base: Optional[str] = None
    mistral_api_base: Optional[str] = None
    gemini_api_base: Optional[str] = None
    
    # ============================================================================
    # Model Configurations
    # ============================================================================
    conceptual_model: str = "gpt-4o"
    practical_model: str = "claude-sonnet-4-20250514"
    validator_model: str = "gpt-4o"
    judge_model: str = "claude-sonnet-4-20250514"
    
    # ============================================================================
    # Generation Settings
    # ============================================================================
    temperature: float = 0.7
    max_tokens: int = 2000
    
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
        
        # Load optional base URLs from environment
        if not self.openai_api_base:
            self.openai_api_base = os.getenv("OPENAI_API_BASE")
        
        if not self.anthropic_api_base:
            self.anthropic_api_base = os.getenv("ANTHROPIC_API_BASE")

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
        
        # Check required API keys
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required (set via parameter or environment variable)")
        
        if not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required (set via parameter or environment variable)")
        
        # Validate model names
        valid_openai_models = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        if self.conceptual_model not in valid_openai_models:
            errors.append(f"Invalid conceptual_model: {self.conceptual_model}")
        
        if self.validator_model not in valid_openai_models:
            errors.append(f"Invalid validator_model: {self.validator_model}")

        # Base URLs are optional and only used for custom endpoints or proxies
        
        # Validate temperature
        if not 0 <= self.temperature <= 2:
            errors.append(f"Temperature must be between 0 and 2, got {self.temperature}")
        
        # Validate max_tokens
        if self.max_tokens < 100:
            errors.append(f"max_tokens must be at least 100, got {self.max_tokens}")
        
        # Validate validation score
        if not 0 <= self.min_validation_score <= 10:
            errors.append(f"min_validation_score must be between 0 and 10, got {self.min_validation_score}")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary"""
        return {
            "openai_api_key": "***" if self.openai_api_key else None,
            "anthropic_api_key": "***" if self.anthropic_api_key else None,
            "mistral_api_key": "***" if self.mistral_api_key else None,
            "gemini_api_key": "***" if self.gemini_api_key else None,
            "openai_api_base": self.openai_api_base,
            "anthropic_api_base": self.anthropic_api_base,
            "mistral_api_base": self.mistral_api_base,
            "gemini_api_base": self.gemini_api_base,
            "conceptual_model": self.conceptual_model,
            "practical_model": self.practical_model,
            "judge_model": self.judge_model,
            "validator_model": self.validator_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "auto_accept_valid": self.auto_accept_valid,
            "save_intermediate_results": self.save_intermediate_results,
            "output_directory": self.output_directory,
            "min_validation_score": self.min_validation_score,
            "strict_validation": self.strict_validation,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "verbose": self.verbose,
            "log_file": self.log_file,
            "metadata": self.metadata
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
        
        with open(filepath, 'w', encoding='utf-8') as f:
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
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return cls.from_dict(config_dict)
    
    def print_summary(self) -> None:
        """Print configuration summary"""
        print("="*70)
        print("Agent Configuration Summary")
        print("="*70)
        print(f"OpenAI API Key: {'✓ Set' if self.openai_api_key else '✗ Missing'}")
        print(f"Anthropic API Key: {'✓ Set' if self.anthropic_api_key else '✗ Missing'}")
        print(f"Mistral API Key: {'✓ Set' if self.mistral_api_key else '✗ Missing'}")
        print(f"Gemini API Key: {'✓ Set' if self.gemini_api_key else '✗ Missing'}")
        print(f"\nModels:")
        print(f"  Conceptual Generator: {self.conceptual_model}")
        print(f"  Practical Generator: {self.practical_model}")
        print(f"  Judge: {self.judge_model}")
        print(f"  Validator: {self.validator_model}")
        print(f"\nGeneration Settings:")
        print(f"  Temperature: {self.temperature}")
        print(f"  Max Tokens: {self.max_tokens}")
        print(f"\nValidation Settings:")
        print(f"  Min Validation Score: {self.min_validation_score}/10")
        print(f"  Strict Validation: {self.strict_validation}")
        print(f"\nWorkflow Settings:")
        print(f"  Auto-accept Valid: {self.auto_accept_valid}")
        print(f"  Save Intermediate: {self.save_intermediate_results}")
        print(f"  Output Directory: {self.output_directory}")
        print(f"\nRetry Settings:")
        print(f"  Max Retries: {self.max_retries}")
        print(f"  Retry Delay: {self.retry_delay}s")
        print("="*70)


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
        temperature=0.5,
        min_validation_score=7,
        auto_accept_valid=True,
        verbose=True
    )
    custom_config.print_summary()
    
    print("\n")
    
    # Example 3: Save and load configuration
    print("Example 3: Save and load configuration")
    test_config_path = "test_config.json"
    custom_config.save(test_config_path)
    loaded_config = AgentConfig.load(test_config_path)
    print(f"✓ Configuration saved and loaded successfully")
    
    # Cleanup
    import os
    if os.path.exists(test_config_path):
        os.remove(test_config_path)