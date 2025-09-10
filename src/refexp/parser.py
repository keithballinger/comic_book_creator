"""YAML parser for reference experiment files."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from .models import RefExperiment, RefExpParseError, RefExpSchemaError, RefExpValidationError

logger = logging.getLogger(__name__)


class RefExpParser:
    """Parser for reference experiment YAML files."""
    
    # Required fields in YAML
    REQUIRED_FIELDS = {'prompt', 'variables'}
    
    # Optional fields with defaults
    OPTIONAL_FIELDS = {
        'name': 'Unnamed Experiment',
        'description': None,
        'settings': {},
        'image_settings': {}
    }
    
    def parse_file(self, filepath: str) -> RefExperiment:
        """Parse a YAML file and return RefExperiment object.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            RefExperiment object
            
        Raises:
            RefExpParseError: If file cannot be parsed
            RefExpSchemaError: If YAML schema is invalid
            RefExpValidationError: If validation fails
        """
        filepath = Path(filepath)
        
        # Check file exists
        if not filepath.exists():
            raise RefExpParseError(f"File not found: {filepath}")
        
        # Check file extension
        if filepath.suffix.lower() not in ['.yaml', '.yml']:
            logger.warning(f"File {filepath} does not have .yaml extension")
        
        try:
            # Load YAML content
            with open(filepath, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise RefExpParseError(f"Failed to parse YAML: {e}")
        except Exception as e:
            raise RefExpParseError(f"Failed to read file: {e}")
        
        # Validate schema
        if not isinstance(data, dict):
            raise RefExpSchemaError("YAML file must contain a dictionary at root level")
        
        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(data.keys())
        if missing_fields:
            raise RefExpSchemaError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Extract fields with defaults
        name = data.get('name', self.OPTIONAL_FIELDS['name'])
        description = data.get('description', self.OPTIONAL_FIELDS['description'])
        prompt_template = data['prompt']
        variables = data['variables']
        settings = data.get('settings', self.OPTIONAL_FIELDS['settings'])
        image_settings = data.get('image_settings', self.OPTIONAL_FIELDS['image_settings'])
        
        # Validate prompt template
        if not isinstance(prompt_template, str):
            raise RefExpSchemaError("Prompt must be a string")
        
        # Validate variables
        validated_variables = self._validate_variables(variables)
        
        # Validate settings
        if not isinstance(settings, dict):
            raise RefExpSchemaError("Settings must be a dictionary")
        
        if not isinstance(image_settings, dict):
            raise RefExpSchemaError("Image settings must be a dictionary")
        
        # Create RefExperiment object
        experiment = RefExperiment(
            name=name,
            description=description,
            prompt_template=prompt_template.strip(),
            variables=validated_variables,
            settings=settings,
            image_settings=image_settings,
            source_file=str(filepath),
            metadata={'original_data': data}
        )
        
        # Validate template variables
        undefined_vars = experiment.validate_template()
        if undefined_vars:
            raise RefExpValidationError(
                f"Template contains undefined variables: {', '.join(undefined_vars)}"
            )
        
        logger.info(f"Successfully parsed experiment '{name}' with {len(validated_variables)} variables")
        return experiment
    
    def _validate_variables(self, variables: Any) -> Dict[str, List[str]]:
        """Validate and normalize variables section.
        
        Args:
            variables: Variables from YAML
            
        Returns:
            Validated dictionary of variables
            
        Raises:
            RefExpSchemaError: If variables format is invalid
        """
        if not isinstance(variables, dict):
            raise RefExpSchemaError("Variables must be a dictionary")
        
        validated = {}
        
        for key, values in variables.items():
            # Validate key
            if not isinstance(key, str):
                raise RefExpSchemaError(f"Variable name must be string, got {type(key)}")
            
            if not key.replace('_', '').isalnum():
                raise RefExpSchemaError(
                    f"Variable name '{key}' must contain only letters, numbers, and underscores"
                )
            
            # Validate values
            if not isinstance(values, list):
                raise RefExpSchemaError(f"Variable '{key}' values must be a list")
            
            if not values:
                raise RefExpSchemaError(f"Variable '{key}' must have at least one value")
            
            # Convert all values to strings
            str_values = []
            for value in values:
                if value is None:
                    raise RefExpSchemaError(f"Variable '{key}' cannot have None values")
                str_values.append(str(value))
            
            validated[key] = str_values
            
            # Check for limits
            if len(str_values) > 100:
                logger.warning(f"Variable '{key}' has {len(str_values)} values (max recommended: 100)")
        
        # Check total combinations
        total_combinations = 1
        for values in validated.values():
            total_combinations *= len(values)
        
        if total_combinations > 10000:
            logger.warning(
                f"Total possible combinations: {total_combinations} (max recommended: 10000)"
            )
        
        return validated
    
    def validate_file(self, filepath: str) -> bool:
        """Validate a YAML file without fully parsing it.
        
        Args:
            filepath: Path to YAML file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            self.parse_file(filepath)
            return True
        except (RefExpParseError, RefExpSchemaError, RefExpValidationError) as e:
            logger.error(f"Validation failed: {e}")
            return False