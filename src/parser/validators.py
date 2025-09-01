"""Script validation utilities."""

from typing import List, Optional
from pathlib import Path

from src.models import ComicScript, ValidationResult


class ScriptValidator:
    """Validator for comic book scripts."""
    
    @staticmethod
    def validate_format(script_content: str) -> ValidationResult:
        """Validate script format without full parsing.
        
        Args:
            script_content: Raw script content
            
        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(is_valid=True)
        
        if not script_content or not script_content.strip():
            result.add_error("Script is empty")
            return result
            
        lines = script_content.strip().split('\n')
        
        # Check for basic structure
        has_page = False
        has_panel = False
        page_count = 0
        panel_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for page markers
            if line.upper().startswith('PAGE'):
                has_page = True
                page_count += 1
                
            # Check for panel markers  
            if line.lower().startswith('panel'):
                has_panel = True
                panel_count += 1
        
        # Validate structure
        if not has_page:
            result.add_error("No PAGE markers found in script")
            
        if not has_panel:
            result.add_error("No Panel markers found in script")
            
        if page_count > 0 and panel_count == 0:
            result.add_error("Pages found but no panels defined")
            
        # Add warnings for potential issues
        if page_count > 50:
            result.add_warning(f"Script has {page_count} pages - consider splitting into chapters")
            
        if panel_count > 0 and page_count > 0:
            avg_panels = panel_count / page_count
            if avg_panels > 9:
                result.add_warning(f"Average of {avg_panels:.1f} panels per page may be too dense")
            elif avg_panels < 3:
                result.add_warning(f"Average of {avg_panels:.1f} panels per page may be too sparse")
        
        return result
    
    @staticmethod
    def validate_script(script: ComicScript) -> ValidationResult:
        """Validate a parsed comic script.
        
        Args:
            script: Parsed ComicScript object
            
        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(is_valid=True)
        
        # Use built-in validation
        errors = script.validate()
        for error in errors:
            result.add_error(error)
        
        # Additional validation
        if script.pages:
            # Check for consistent panel numbering
            for page in script.pages:
                if not page.panels:
                    result.add_warning(f"Page {page.number} has no panels")
                    continue
                    
                # Check panel descriptions
                for panel in page.panels:
                    if not panel.description or len(panel.description) < 10:
                        result.add_warning(
                            f"Page {page.number}, Panel {panel.number}: "
                            "Description is too short or missing"
                        )
                    
                    # Check for excessive dialogue
                    if len(panel.dialogue) > 5:
                        result.add_warning(
                            f"Page {page.number}, Panel {panel.number}: "
                            f"Has {len(panel.dialogue)} dialogue entries - may be too crowded"
                        )
                    
                    # Check for missing characters in dialogue
                    for dialogue in panel.dialogue:
                        if dialogue.character not in panel.characters:
                            panel.characters.append(dialogue.character)
            
            # Check page balance
            panel_counts = [len(page.panels) for page in script.pages]
            if panel_counts:
                min_panels = min(panel_counts)
                max_panels = max(panel_counts)
                if max_panels - min_panels > 4:
                    result.add_warning(
                        f"Uneven panel distribution: {min_panels} to {max_panels} panels per page"
                    )
        
        return result
    
    @staticmethod
    def validate_file(file_path: str) -> ValidationResult:
        """Validate a script file.
        
        Args:
            file_path: Path to script file
            
        Returns:
            ValidationResult with any errors or warnings
        """
        result = ValidationResult(is_valid=True)
        
        path = Path(file_path)
        
        # Check file exists
        if not path.exists():
            result.add_error(f"File not found: {file_path}")
            return result
        
        # Check file extension
        valid_extensions = ['.txt', '.fdx', '.fountain', '.json']
        if path.suffix.lower() not in valid_extensions:
            result.add_warning(
                f"Unusual file extension '{path.suffix}'. "
                f"Expected one of: {', '.join(valid_extensions)}"
            )
        
        # Check file size
        file_size = path.stat().st_size
        if file_size == 0:
            result.add_error("File is empty")
            return result
        elif file_size > 10 * 1024 * 1024:  # 10MB
            result.add_warning("File is very large (>10MB) - processing may be slow")
        
        # Try to read file
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Validate content format
            format_result = ScriptValidator.validate_format(content)
            result.errors.extend(format_result.errors)
            result.warnings.extend(format_result.warnings)
            if format_result.errors:
                result.is_valid = False
                
        except UnicodeDecodeError:
            result.add_error("File encoding is not UTF-8")
        except Exception as e:
            result.add_error(f"Error reading file: {str(e)}")
        
        return result