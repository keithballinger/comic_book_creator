"""Tests for configuration loader module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import yaml

from src.config import (
    Config,
    ConfigLoader,
    load_config,
    load_styles,
)


class TestConfigLoader:
    """Test cases for ConfigLoader class."""
    
    def test_default_config(self):
        """Test loading default configuration."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            config = load_config()
            
            assert config.api_key == 'test-key'
            assert config.style.art_style == "modern comic book"
            assert config.generation.panel_size == [1024, 1536]
            assert config.output.formats == ["png", "pdf", "cbz"]
            assert config.performance.cache_enabled is True
    
    def test_yaml_config_loading(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
style:
  art_style: "manga"
  color_palette: "black and white"
  line_weight: "thin"
  shading: "screen-tone"
  
generation:
  panel_size: [800, 1200]
  quality: "medium"
  consistency_weight: 0.8
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
            
        try:
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
                config = load_config(temp_path)
                
                assert config.style.art_style == "manga"
                assert config.style.color_palette == "black and white"
                assert config.generation.panel_size == [800, 1200]
                assert config.generation.consistency_weight == 0.8
        finally:
            os.unlink(temp_path)
    
    def test_env_overrides(self):
        """Test environment variable overrides."""
        env_vars = {
            'GEMINI_API_KEY': 'env-test-key',
            'MAX_CONCURRENT_REQUESTS': '8',
            'CACHE_ENABLED': 'false',
            'CACHE_DIR': '/tmp/cache',
            'DEFAULT_OUTPUT_DIR': '/tmp/output',
            'DEFAULT_IMAGE_FORMAT': 'jpg',
            'DEFAULT_DPI': '600',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_config()
            
            assert config.api_key == 'env-test-key'
            assert config.max_concurrent_requests == 8
            assert config.performance.cache_enabled is False
            assert config.cache_dir == '/tmp/cache'
            assert config.output_dir == '/tmp/output'
            assert 'jpg' in config.output.formats
            assert config.output.dpi == 600
            assert config.debug is True
            assert config.log_level == 'DEBUG'
    
    def test_missing_api_key(self):
        """Test validation error when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                load_config()
    
    def test_invalid_panel_size(self):
        """Test validation of panel size."""
        yaml_content = """
generation:
  panel_size: [0, -100]
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
            
        try:
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
                with pytest.raises(ValueError, match="Panel size dimensions must be positive"):
                    load_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_consistency_weight(self):
        """Test validation of consistency weight."""
        yaml_content = """
generation:
  consistency_weight: 1.5
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
            
        try:
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
                with pytest.raises(ValueError, match="Consistency weight must be between 0 and 1"):
                    load_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_dpi(self):
        """Test validation of DPI setting."""
        yaml_content = """
output:
  dpi: -300
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name
            
        try:
            with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
                with pytest.raises(ValueError, match="DPI must be positive"):
                    load_config(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_invalid_log_level(self):
        """Test validation of log level."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key', 'LOG_LEVEL': 'INVALID'}):
            with pytest.raises(ValueError, match="Log level must be one of"):
                load_config()
    
    def test_load_styles(self):
        """Test loading art styles."""
        styles = load_styles()
        
        # Should have styles if the config/styles.yaml exists
        if Path("config/styles.yaml").exists():
            assert 'modern' in styles
            assert 'manga' in styles
            assert 'indie' in styles
            assert styles['modern']['art_style'] == "modern comic book"
            assert styles['manga']['color_palette'] == "black and white"
    
    def test_nonexistent_config_file(self):
        """Test loading with non-existent config file."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            # Should use defaults when file doesn't exist
            config = load_config("nonexistent.yaml")
            assert config.style.art_style == "modern comic book"


class TestRedCometConfig:
    """Test configuration with red_comet.txt example."""
    
    def test_config_for_red_comet(self):
        """Test that configuration is suitable for red_comet.txt processing."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            config = load_config()
            
            # Check that we have appropriate settings for the example
            assert config.generation.panel_size[0] > 0
            assert config.generation.panel_size[1] > 0
            assert config.generation.quality in ["draft", "standard", "high"]
            assert config.performance.batch_size >= 6  # At least 6 panels per page
            assert config.output.formats  # At least one output format