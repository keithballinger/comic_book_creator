"""Tests for YAML parser."""

import pytest
import tempfile
from pathlib import Path
import yaml

from src.refexp.parser import RefExpParser
from src.refexp.models import RefExpParseError, RefExpSchemaError, RefExpValidationError


class TestRefExpParser:
    """Test the YAML parser for reference experiments."""
    
    def test_parse_valid_yaml(self, tmp_path):
        """Test parsing a valid YAML file."""
        yaml_content = """
name: "Test Experiment"
description: "A test experiment"
prompt: "Create a {style} image of a {subject}"
variables:
  style: ["realistic", "cartoon"]
  subject: ["cat", "dog"]
settings:
  quality: high
  seed: 42
image_settings:
  width: 1024
  height: 1024
"""
        yaml_file = tmp_path / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        parser = RefExpParser()
        experiment = parser.parse_file(str(yaml_file))
        
        assert experiment.name == "Test Experiment"
        assert experiment.description == "A test experiment"
        assert "style" in experiment.variables
        assert len(experiment.variables["style"]) == 2
        assert experiment.settings["quality"] == "high"
        assert experiment.image_settings["width"] == 1024
    
    def test_parse_minimal_yaml(self, tmp_path):
        """Test parsing minimal YAML with only required fields."""
        yaml_content = """
prompt: "Create a {style} image"
variables:
  style: ["realistic"]
"""
        yaml_file = tmp_path / "minimal.yaml"
        yaml_file.write_text(yaml_content)
        
        parser = RefExpParser()
        experiment = parser.parse_file(str(yaml_file))
        
        assert experiment.name == "Unnamed Experiment"
        assert experiment.description is None
        assert experiment.settings == {}
        assert experiment.image_settings == {}
    
    def test_missing_required_fields(self, tmp_path):
        """Test error when required fields are missing."""
        yaml_content = """
name: "Test"
description: "Missing prompt and variables"
"""
        yaml_file = tmp_path / "invalid.yaml"
        yaml_file.write_text(yaml_content)
        
        parser = RefExpParser()
        with pytest.raises(RefExpSchemaError) as exc:
            parser.parse_file(str(yaml_file))
        assert "Missing required fields" in str(exc.value)
    
    def test_undefined_variables(self, tmp_path):
        """Test error when template uses undefined variables."""
        yaml_content = """
prompt: "Create a {style} image with {color}"
variables:
  style: ["realistic"]
"""
        yaml_file = tmp_path / "undefined.yaml"
        yaml_file.write_text(yaml_content)
        
        parser = RefExpParser()
        with pytest.raises(RefExpValidationError) as exc:
            parser.parse_file(str(yaml_file))
        assert "undefined variables" in str(exc.value)
        assert "color" in str(exc.value)
    
    def test_invalid_variable_format(self, tmp_path):
        """Test error with invalid variable format."""
        yaml_content = """
prompt: "Test {var}"
variables:
  var: "not a list"  # Should be a list
"""
        yaml_file = tmp_path / "bad_var.yaml"
        yaml_file.write_text(yaml_content)
        
        parser = RefExpParser()
        with pytest.raises(RefExpSchemaError) as exc:
            parser.parse_file(str(yaml_file))
        assert "must be a list" in str(exc.value)
    
    def test_empty_variable_list(self, tmp_path):
        """Test error with empty variable list."""
        yaml_content = """
prompt: "Test {var}"
variables:
  var: []  # Empty list
"""
        yaml_file = tmp_path / "empty_var.yaml"
        yaml_file.write_text(yaml_content)
        
        parser = RefExpParser()
        with pytest.raises(RefExpSchemaError) as exc:
            parser.parse_file(str(yaml_file))
        assert "at least one value" in str(exc.value)
    
    def test_invalid_yaml_syntax(self, tmp_path):
        """Test error with invalid YAML syntax."""
        yaml_content = """
name: "Test
prompt: unclosed quote
"""
        yaml_file = tmp_path / "invalid_syntax.yaml"
        yaml_file.write_text(yaml_content)
        
        parser = RefExpParser()
        with pytest.raises(RefExpParseError) as exc:
            parser.parse_file(str(yaml_file))
        assert "Failed to parse YAML" in str(exc.value)
    
    def test_file_not_found(self):
        """Test error when file doesn't exist."""
        parser = RefExpParser()
        with pytest.raises(RefExpParseError) as exc:
            parser.parse_file("/nonexistent/file.yaml")
        assert "File not found" in str(exc.value)
    
    def test_validate_file(self, tmp_path):
        """Test validate_file method."""
        valid_yaml = """
prompt: "Test {var}"
variables:
  var: ["a", "b"]
"""
        valid_file = tmp_path / "valid.yaml"
        valid_file.write_text(valid_yaml)
        
        invalid_yaml = """
prompt: "Test"
"""
        invalid_file = tmp_path / "invalid.yaml"
        invalid_file.write_text(invalid_yaml)
        
        parser = RefExpParser()
        assert parser.validate_file(str(valid_file)) is True
        assert parser.validate_file(str(invalid_file)) is False