"""Validators for reference data and images."""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from PIL import Image
import io
from datetime import datetime

from .models import (
    BaseReference,
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
)

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ValidationWarning:
    """Warning issued during validation."""
    
    def __init__(self, field: str, message: str, severity: str = "warning"):
        """Initialize warning.
        
        Args:
            field: Field that triggered the warning
            message: Warning message
            severity: warning, minor, major, critical
        """
        self.field = field
        self.message = message
        self.severity = severity
        self.timestamp = datetime.now()
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


class ReferenceValidator:
    """Validator for reference data."""
    
    # Validation rules
    MIN_NAME_LENGTH = 2
    MAX_NAME_LENGTH = 50
    MIN_DESCRIPTION_LENGTH = 10
    MAX_DESCRIPTION_LENGTH = 500
    
    # Pattern for valid names
    NAME_PATTERN = re.compile(r'^[A-Za-z][A-Za-z0-9_\s-]*$')
    
    # Reserved names
    RESERVED_NAMES = {'default', 'none', 'null', 'undefined', 'test'}
    
    def validate_reference(
        self,
        reference: BaseReference,
        strict: bool = False
    ) -> Tuple[bool, List[ValidationWarning]]:
        """Validate a reference.
        
        Args:
            reference: Reference to validate
            strict: If True, warnings become errors
            
        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings = []
        
        try:
            # Basic validation
            reference.validate()
            
            # Name validation
            name_warnings = self._validate_name(reference.name)
            warnings.extend(name_warnings)
            
            # Description validation
            desc_warnings = self._validate_description(reference.description)
            warnings.extend(desc_warnings)
            
            # Type-specific validation
            if isinstance(reference, CharacterReference):
                char_warnings = self._validate_character(reference)
                warnings.extend(char_warnings)
            elif isinstance(reference, LocationReference):
                loc_warnings = self._validate_location(reference)
                warnings.extend(loc_warnings)
            elif isinstance(reference, ObjectReference):
                obj_warnings = self._validate_object(reference)
                warnings.extend(obj_warnings)
            elif isinstance(reference, StyleGuide):
                style_warnings = self._validate_style_guide(reference)
                warnings.extend(style_warnings)
            
            # Check severity
            if strict and warnings:
                critical = [w for w in warnings if w.severity == "critical"]
                if critical:
                    return False, warnings
            
            return True, warnings
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            warnings.append(ValidationWarning(
                "general",
                str(e),
                "critical"
            ))
            return False, warnings
    
    def _validate_name(self, name: str) -> List[ValidationWarning]:
        """Validate reference name."""
        warnings = []
        
        # Length check
        if len(name) < self.MIN_NAME_LENGTH:
            warnings.append(ValidationWarning(
                "name",
                f"Name too short (min {self.MIN_NAME_LENGTH} chars)",
                "major"
            ))
        elif len(name) > self.MAX_NAME_LENGTH:
            warnings.append(ValidationWarning(
                "name",
                f"Name too long (max {self.MAX_NAME_LENGTH} chars)",
                "minor"
            ))
        
        # Pattern check
        if not self.NAME_PATTERN.match(name):
            warnings.append(ValidationWarning(
                "name",
                "Name contains invalid characters",
                "major"
            ))
        
        # Reserved name check
        if name.lower() in self.RESERVED_NAMES:
            warnings.append(ValidationWarning(
                "name",
                f"'{name}' is a reserved name",
                "critical"
            ))
        
        return warnings
    
    def _validate_description(self, description: str) -> List[ValidationWarning]:
        """Validate reference description."""
        warnings = []
        
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            warnings.append(ValidationWarning(
                "description",
                f"Description too short (min {self.MIN_DESCRIPTION_LENGTH} chars)",
                "minor"
            ))
        elif len(description) > self.MAX_DESCRIPTION_LENGTH:
            warnings.append(ValidationWarning(
                "description",
                f"Description too long (max {self.MAX_DESCRIPTION_LENGTH} chars)",
                "minor"
            ))
        
        return warnings
    
    def _validate_character(self, character: CharacterReference) -> List[ValidationWarning]:
        """Validate character-specific fields."""
        warnings = []
        
        # Check poses
        if not character.poses:
            warnings.append(ValidationWarning(
                "poses",
                "No poses defined for character",
                "warning"
            ))
        
        # Check expressions
        if not character.expressions:
            warnings.append(ValidationWarning(
                "expressions",
                "No expressions defined for character",
                "warning"
            ))
        
        # Check for duplicate poses/expressions
        if len(set(character.poses)) != len(character.poses):
            warnings.append(ValidationWarning(
                "poses",
                "Duplicate poses detected",
                "minor"
            ))
        
        if len(set(character.expressions)) != len(character.expressions):
            warnings.append(ValidationWarning(
                "expressions",
                "Duplicate expressions detected",
                "minor"
            ))
        
        return warnings
    
    def _validate_location(self, location: LocationReference) -> List[ValidationWarning]:
        """Validate location-specific fields."""
        warnings = []
        
        # Check angles
        if not location.angles:
            warnings.append(ValidationWarning(
                "angles",
                "No camera angles defined for location",
                "warning"
            ))
        
        # Check lighting
        if not location.lighting_conditions:
            warnings.append(ValidationWarning(
                "lighting_conditions",
                "No lighting conditions defined",
                "warning"
            ))
        
        return warnings
    
    def _validate_object(self, obj: ObjectReference) -> List[ValidationWarning]:
        """Validate object-specific fields."""
        warnings = []
        
        # Check views
        if not obj.views:
            warnings.append(ValidationWarning(
                "views",
                "No views defined for object",
                "warning"
            ))
        
        # Check states
        if not obj.states:
            warnings.append(ValidationWarning(
                "states",
                "No states defined for object",
                "warning"
            ))
        
        return warnings
    
    def _validate_style_guide(self, style: StyleGuide) -> List[ValidationWarning]:
        """Validate style guide fields."""
        warnings = []
        
        # Check color palette
        if style.color_palette:
            for color in style.color_palette:
                if not self._is_valid_color(color):
                    warnings.append(ValidationWarning(
                        "color_palette",
                        f"Invalid color format: {color}",
                        "minor"
                    ))
        
        return warnings
    
    def _is_valid_color(self, color: str) -> bool:
        """Check if color is valid hex format."""
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')
        return bool(hex_pattern.match(color))


class ImageValidator:
    """Validator for reference images."""
    
    # Image constraints
    MIN_WIDTH = 256
    MIN_HEIGHT = 256
    MAX_WIDTH = 4096
    MAX_HEIGHT = 4096
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Supported formats
    SUPPORTED_FORMATS = {'PNG', 'JPEG', 'JPG', 'WEBP'}
    
    def validate_image(
        self,
        image_data: bytes,
        context: Optional[str] = None
    ) -> Tuple[bool, List[ValidationWarning]]:
        """Validate image data.
        
        Args:
            image_data: Binary image data
            context: Optional context for the image
            
        Returns:
            Tuple of (is_valid, warnings)
        """
        warnings = []
        
        try:
            # Check file size
            if len(image_data) > self.MAX_FILE_SIZE:
                warnings.append(ValidationWarning(
                    "file_size",
                    f"Image exceeds maximum size ({len(image_data)/1024/1024:.1f}MB > {self.MAX_FILE_SIZE/1024/1024}MB)",
                    "major"
                ))
                return False, warnings
            
            # Load image
            img = Image.open(io.BytesIO(image_data))
            
            # Check format
            if img.format not in self.SUPPORTED_FORMATS:
                warnings.append(ValidationWarning(
                    "format",
                    f"Unsupported format: {img.format}",
                    "critical"
                ))
                return False, warnings
            
            # Check dimensions
            width, height = img.size
            
            if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
                warnings.append(ValidationWarning(
                    "dimensions",
                    f"Image too small ({width}x{height} < {self.MIN_WIDTH}x{self.MIN_HEIGHT})",
                    "major"
                ))
            
            if width > self.MAX_WIDTH or height > self.MAX_HEIGHT:
                warnings.append(ValidationWarning(
                    "dimensions",
                    f"Image too large ({width}x{height} > {self.MAX_WIDTH}x{self.MAX_HEIGHT})",
                    "major"
                ))
            
            # Check aspect ratio
            aspect_ratio = width / height
            if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                warnings.append(ValidationWarning(
                    "aspect_ratio",
                    f"Unusual aspect ratio: {aspect_ratio:.2f}",
                    "minor"
                ))
            
            # Check image mode
            if img.mode not in ['RGB', 'RGBA']:
                warnings.append(ValidationWarning(
                    "mode",
                    f"Unusual image mode: {img.mode}",
                    "minor"
                ))
            
            # Check for transparency in non-RGBA
            if img.mode == 'RGBA':
                # Check if alpha channel is actually used
                alpha = img.split()[-1]
                if alpha.getextrema() == (255, 255):
                    warnings.append(ValidationWarning(
                        "transparency",
                        "RGBA image without transparency",
                        "minor"
                    ))
            
            return True, warnings
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            warnings.append(ValidationWarning(
                "image",
                f"Failed to validate image: {str(e)}",
                "critical"
            ))
            return False, warnings
    
    def check_quality(
        self,
        image_data: bytes,
        min_quality_score: float = 0.7
    ) -> Tuple[float, List[ValidationWarning]]:
        """Check image quality.
        
        Args:
            image_data: Binary image data
            min_quality_score: Minimum acceptable quality score (0-1)
            
        Returns:
            Tuple of (quality_score, warnings)
        """
        warnings = []
        
        try:
            img = Image.open(io.BytesIO(image_data))
            
            # Simple quality heuristics
            quality_score = 1.0
            
            # Check compression artifacts (for JPEG)
            if img.format == 'JPEG':
                # Estimate JPEG quality (simplified)
                quality_score *= 0.9
                warnings.append(ValidationWarning(
                    "compression",
                    "JPEG compression may reduce quality",
                    "minor"
                ))
            
            # Check resolution
            width, height = img.size
            pixels = width * height
            if pixels < 512 * 512:
                quality_score *= 0.8
                warnings.append(ValidationWarning(
                    "resolution",
                    "Low resolution image",
                    "minor"
                ))
            elif pixels < 1024 * 1024:
                quality_score *= 0.95
            
            # Check for upscaling artifacts (simplified check)
            # In real implementation, would use more sophisticated methods
            
            if quality_score < min_quality_score:
                warnings.append(ValidationWarning(
                    "quality",
                    f"Quality score {quality_score:.2f} below threshold {min_quality_score}",
                    "major"
                ))
            
            return quality_score, warnings
            
        except Exception as e:
            logger.error(f"Quality check error: {e}")
            warnings.append(ValidationWarning(
                "quality",
                f"Failed to check quality: {str(e)}",
                "critical"
            ))
            return 0.0, warnings


class ConsistencyValidator:
    """Validator for reference consistency."""
    
    def check_consistency(
        self,
        references: List[BaseReference],
        check_images: bool = False
    ) -> List[ValidationWarning]:
        """Check consistency across references.
        
        Args:
            references: List of references to check
            check_images: Whether to check image consistency
            
        Returns:
            List of warnings
        """
        warnings = []
        
        # Check for naming conflicts
        names = {}
        for ref in references:
            key = (ref.__class__.__name__, ref.name.lower())
            if key in names:
                warnings.append(ValidationWarning(
                    "naming",
                    f"Duplicate name '{ref.name}' in {ref.__class__.__name__}",
                    "major"
                ))
            names[key] = ref
        
        # Check for similar names that might be confusing
        all_names = [ref.name for ref in references]
        for i, name1 in enumerate(all_names):
            for name2 in all_names[i+1:]:
                similarity = self._name_similarity(name1, name2)
                if similarity > 0.8 and name1.lower() != name2.lower():
                    warnings.append(ValidationWarning(
                        "naming",
                        f"Similar names might be confusing: '{name1}' and '{name2}'",
                        "minor"
                    ))
        
        # Check style guide consistency
        style_guides = [r for r in references if isinstance(r, StyleGuide)]
        if len(style_guides) > 1:
            # Check for conflicting styles
            art_styles = set(s.art_style for s in style_guides if s.art_style)
            if len(art_styles) > 1:
                warnings.append(ValidationWarning(
                    "style",
                    f"Multiple art styles defined: {art_styles}",
                    "warning"
                ))
        
        return warnings
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names (0-1)."""
        # Simple character-based similarity
        # In real implementation, would use Levenshtein distance or similar
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        if name1_lower == name2_lower:
            return 1.0
        
        # Check if one is substring of the other
        if name1_lower in name2_lower or name2_lower in name1_lower:
            return 0.85
        
        # Check common prefix
        common_prefix_len = 0
        for c1, c2 in zip(name1_lower, name2_lower):
            if c1 == c2:
                common_prefix_len += 1
            else:
                break
        
        max_len = max(len(name1), len(name2))
        if common_prefix_len > 0:
            return common_prefix_len / max_len
        
        return 0.0


class ValidationReport:
    """Complete validation report."""
    
    def __init__(self):
        """Initialize report."""
        self.timestamp = datetime.now()
        self.reference_results: Dict[str, Tuple[bool, List[ValidationWarning]]] = {}
        self.image_results: Dict[str, Tuple[bool, List[ValidationWarning]]] = {}
        self.consistency_warnings: List[ValidationWarning] = []
    
    def add_reference_result(
        self,
        ref_id: str,
        is_valid: bool,
        warnings: List[ValidationWarning]
    ):
        """Add reference validation result."""
        self.reference_results[ref_id] = (is_valid, warnings)
    
    def add_image_result(
        self,
        image_id: str,
        is_valid: bool,
        warnings: List[ValidationWarning]
    ):
        """Add image validation result."""
        self.image_results[image_id] = (is_valid, warnings)
    
    def set_consistency_warnings(self, warnings: List[ValidationWarning]):
        """Set consistency warnings."""
        self.consistency_warnings = warnings
    
    def is_valid(self) -> bool:
        """Check if all validations passed."""
        # Check references
        for is_valid, _ in self.reference_results.values():
            if not is_valid:
                return False
        
        # Check images
        for is_valid, _ in self.image_results.values():
            if not is_valid:
                return False
        
        # Check critical consistency warnings
        critical = [w for w in self.consistency_warnings if w.severity == "critical"]
        if critical:
            return False
        
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        total_refs = len(self.reference_results)
        valid_refs = sum(1 for v, _ in self.reference_results.values() if v)
        
        total_images = len(self.image_results)
        valid_images = sum(1 for v, _ in self.image_results.values() if v)
        
        all_warnings = []
        for _, warnings in self.reference_results.values():
            all_warnings.extend(warnings)
        for _, warnings in self.image_results.values():
            all_warnings.extend(warnings)
        all_warnings.extend(self.consistency_warnings)
        
        severity_counts = {
            "critical": 0,
            "major": 0,
            "minor": 0,
            "warning": 0
        }
        
        for warning in all_warnings:
            severity_counts[warning.severity] += 1
        
        return {
            "timestamp": self.timestamp.isoformat(),
            "is_valid": self.is_valid(),
            "references": {
                "total": total_refs,
                "valid": valid_refs,
                "invalid": total_refs - valid_refs
            },
            "images": {
                "total": total_images,
                "valid": valid_images,
                "invalid": total_images - valid_images
            },
            "warnings": {
                "total": len(all_warnings),
                "by_severity": severity_counts
            }
        }
    
    def format_report(self) -> str:
        """Format report as string."""
        lines = []
        lines.append("=" * 60)
        lines.append("VALIDATION REPORT")
        lines.append(f"Generated: {self.timestamp.isoformat()}")
        lines.append("=" * 60)
        
        summary = self.get_summary()
        lines.append(f"\nOverall Status: {'✅ VALID' if summary['is_valid'] else '❌ INVALID'}")
        
        lines.append(f"\nReferences: {summary['references']['valid']}/{summary['references']['total']} valid")
        lines.append(f"Images: {summary['images']['valid']}/{summary['images']['total']} valid")
        
        lines.append(f"\nWarnings: {summary['warnings']['total']}")
        for severity, count in summary['warnings']['by_severity'].items():
            if count > 0:
                lines.append(f"  - {severity.upper()}: {count}")
        
        # Detailed warnings
        if self.reference_results:
            lines.append("\n" + "-" * 40)
            lines.append("REFERENCE VALIDATION:")
            for ref_id, (is_valid, warnings) in self.reference_results.items():
                status = "✅" if is_valid else "❌"
                lines.append(f"\n{status} {ref_id}")
                for warning in warnings:
                    lines.append(f"  {warning}")
        
        if self.image_results:
            lines.append("\n" + "-" * 40)
            lines.append("IMAGE VALIDATION:")
            for img_id, (is_valid, warnings) in self.image_results.items():
                status = "✅" if is_valid else "❌"
                lines.append(f"\n{status} {img_id}")
                for warning in warnings:
                    lines.append(f"  {warning}")
        
        if self.consistency_warnings:
            lines.append("\n" + "-" * 40)
            lines.append("CONSISTENCY WARNINGS:")
            for warning in self.consistency_warnings:
                lines.append(f"  {warning}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)