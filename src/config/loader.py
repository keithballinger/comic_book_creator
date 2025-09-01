"""Configuration loader module for Comic Book Creator."""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv
from dataclasses import dataclass, field


@dataclass
class StyleConfig:
    """Style configuration for comic generation."""
    art_style: str = "modern comic book"
    color_palette: str = "vibrant"
    line_weight: str = "medium"
    shading: str = "cel-shaded"


@dataclass
class GenerationConfig:
    """Generation configuration settings."""
    panel_size: list[int] = field(default_factory=lambda: [1024, 1536])
    quality: str = "high"
    consistency_weight: float = 0.7


@dataclass
class TextConfig:
    """Text rendering configuration."""
    font_family: str = "Comic Sans MS"
    bubble_style: str = "classic"
    caption_style: str = "box"


@dataclass
class OutputConfig:
    """Output configuration settings."""
    formats: list[str] = field(default_factory=lambda: ["png", "pdf", "cbz"])
    page_size: list[int] = field(default_factory=lambda: [2400, 3600])
    dpi: int = 300


@dataclass
class PerformanceConfig:
    """Performance configuration settings."""
    cache_enabled: bool = True
    max_workers: int = 4
    batch_size: int = 10


@dataclass
class Config:
    """Main configuration class."""
    style: StyleConfig = field(default_factory=StyleConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    text: TextConfig = field(default_factory=TextConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Runtime configuration
    api_key: Optional[str] = None
    max_concurrent_requests: int = 4
    cache_dir: str = ".cache"
    output_dir: str = "./output"
    debug: bool = False
    log_level: str = "INFO"


class ConfigLoader:
    """Configuration loader with YAML and environment variable support."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration loader.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or "config/default.yaml"
        load_dotenv()  # Load environment variables
        
    def load(self) -> Config:
        """Load configuration from file and environment.
        
        Returns:
            Config object with all settings
        """
        config = Config()
        
        # Load from YAML file if it exists
        if Path(self.config_path).exists():
            with open(self.config_path, 'r') as f:
                yaml_config = yaml.safe_load(f)
                config = self._merge_yaml_config(config, yaml_config)
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        # Validate configuration
        self._validate_config(config)
        
        return config
    
    def _merge_yaml_config(self, config: Config, yaml_config: Dict[str, Any]) -> Config:
        """Merge YAML configuration into config object.
        
        Args:
            config: Base configuration object
            yaml_config: YAML configuration dictionary
            
        Returns:
            Updated configuration object
        """
        if 'style' in yaml_config:
            config.style = StyleConfig(**yaml_config['style'])
            
        if 'generation' in yaml_config:
            config.generation = GenerationConfig(**yaml_config['generation'])
            
        if 'text' in yaml_config:
            config.text = TextConfig(**yaml_config['text'])
            
        if 'output' in yaml_config:
            config.output = OutputConfig(**yaml_config['output'])
            
        if 'performance' in yaml_config:
            config.performance = PerformanceConfig(**yaml_config['performance'])
            
        return config
    
    def _apply_env_overrides(self, config: Config) -> Config:
        """Apply environment variable overrides to configuration.
        
        Args:
            config: Configuration object to update
            
        Returns:
            Updated configuration object
        """
        # API configuration
        config.api_key = os.getenv('GEMINI_API_KEY', config.api_key)
        
        # Performance settings
        if env_max_concurrent := os.getenv('MAX_CONCURRENT_REQUESTS'):
            config.max_concurrent_requests = int(env_max_concurrent)
            
        if env_cache_enabled := os.getenv('CACHE_ENABLED'):
            config.performance.cache_enabled = env_cache_enabled.lower() == 'true'
            
        config.cache_dir = os.getenv('CACHE_DIR', config.cache_dir)
        
        # Output settings
        config.output_dir = os.getenv('DEFAULT_OUTPUT_DIR', config.output_dir)
        
        if env_format := os.getenv('DEFAULT_IMAGE_FORMAT'):
            if env_format not in config.output.formats:
                config.output.formats.append(env_format)
                
        if env_dpi := os.getenv('DEFAULT_DPI'):
            config.output.dpi = int(env_dpi)
            
        # Development settings
        if env_debug := os.getenv('DEBUG'):
            config.debug = env_debug.lower() == 'true'
            
        config.log_level = os.getenv('LOG_LEVEL', config.log_level)
        
        return config
    
    def _validate_config(self, config: Config) -> None:
        """Validate configuration settings.
        
        Args:
            config: Configuration object to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        # Check required fields
        if not config.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        # Validate panel size
        if len(config.generation.panel_size) != 2:
            raise ValueError("Panel size must be [width, height]")
            
        if any(s <= 0 for s in config.generation.panel_size):
            raise ValueError("Panel size dimensions must be positive")
            
        # Validate page size
        if len(config.output.page_size) != 2:
            raise ValueError("Page size must be [width, height]")
            
        if any(s <= 0 for s in config.output.page_size):
            raise ValueError("Page size dimensions must be positive")
            
        # Validate DPI
        if config.output.dpi <= 0:
            raise ValueError("DPI must be positive")
            
        # Validate consistency weight
        if not 0 <= config.generation.consistency_weight <= 1:
            raise ValueError("Consistency weight must be between 0 and 1")
            
        # Validate max workers
        if config.performance.max_workers <= 0:
            raise ValueError("Max workers must be positive")
            
        # Validate batch size
        if config.performance.batch_size <= 0:
            raise ValueError("Batch size must be positive")
            
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.log_level not in valid_log_levels:
            raise ValueError(f"Log level must be one of {valid_log_levels}")


def load_config(config_path: Optional[str] = None) -> Config:
    """Convenience function to load configuration.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Loaded configuration object
    """
    loader = ConfigLoader(config_path)
    return loader.load()


def load_styles() -> Dict[str, Dict[str, Any]]:
    """Load available art styles from styles.yaml.
    
    Returns:
        Dictionary of available styles
    """
    styles_path = Path("config/styles.yaml")
    if not styles_path.exists():
        return {}
        
    with open(styles_path, 'r') as f:
        styles_config = yaml.safe_load(f)
        
    return styles_config.get('styles', {})