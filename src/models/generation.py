"""Generation and output data models for Comic Book Creator."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass
class CharacterReference:
    """Reference information for a character."""
    name: str
    appearance_description: str
    reference_image: Optional[bytes] = None
    personality_traits: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate character reference."""
        if not self.name:
            raise ValueError("Character must have a name")
        if not self.appearance_description:
            raise ValueError("Character must have an appearance description")
    
    def get_consistency_prompt(self) -> str:
        """Generate consistency prompt for this character."""
        prompt = f"{self.name}: {self.appearance_description}"
        if self.personality_traits:
            traits = ", ".join(self.personality_traits)
            prompt += f" (Personality: {traits})"
        return prompt


@dataclass
class GeneratedPanel:
    """A generated comic panel with image data."""
    panel: Any  # Panel from script.py (avoiding circular import)
    image_data: bytes
    generation_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if not self.metadata:
            self.metadata = {
                "generated_at": datetime.now().isoformat(),
                "image_size": len(self.image_data) if self.image_data else 0,
                "generation_time_seconds": self.generation_time,
            }


@dataclass
class GeneratedPage:
    """A generated comic page."""
    page: Any  # Page from script.py
    panels: List[GeneratedPanel]  # Empty for single-pass generation
    image_data: Optional[bytes] = None  # Complete page image for single-pass
    composed_image: Optional[bytes] = None  # Legacy: for multi-panel composition
    composition_time: float = 0.0
    generation_time: float = 0.0  # Total time to generate page
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize page metadata."""
        if not self.metadata:
            self.metadata = {
                "page_number": self.page.number if self.page else 0,
                "panel_count": len(self.panels),
                "composed": self.composed_image is not None,
                "total_generation_time": sum(p.generation_time for p in self.panels),
                "composition_time": self.composition_time,
            }
    
    def is_complete(self) -> bool:
        """Check if page generation is complete."""
        # For single-pass generation, check if we have the image_data
        if self.image_data:
            return True
        # For legacy multi-panel generation
        return (
            len(self.panels) == len(self.page.panels) and
            all(p.image_data for p in self.panels) and
            self.composed_image is not None
        )


@dataclass
class ProcessingResult:
    """Result of processing a comic script."""
    success: bool = True
    script: Optional['ComicScript'] = None  # Forward reference
    generated_pages: Optional[List[GeneratedPage]] = None
    validation_result: Optional['ValidationResult'] = None  # Forward reference
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    export_paths: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate total processing time if not set."""
        if not self.processing_time and self.generated_pages:
            self.processing_time = sum(
                page.generation_time
                for page in self.generated_pages
            )
    
    def is_successful(self) -> bool:
        """Check if processing was successful."""
        return self.success and not self.errors
    
    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        return {
            "total_pages": len(self.generated_pages) if self.generated_pages else 0,
            "total_panels": sum(len(page.panels) for page in self.generated_pages) if self.generated_pages else 0,
            "total_time_seconds": self.processing_time,
            "successful": self.is_successful(),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "export_formats": list(self.export_paths.keys()),
        }


@dataclass
class ProcessingOptions:
    """Options for processing a comic script."""
    page_range: Optional[Tuple[int, int]] = None  # (start, end) inclusive
    style_preset: Optional[str] = None  # Name of style preset to use
    style_override: Optional[str] = None  # Custom style override
    quality: str = "high"
    export_formats: List[str] = field(default_factory=lambda: ["png"])
    parallel_generation: bool = False  # Generate panels in parallel
    # Text rendering removed - Gemini handles all text
    debug_mode: bool = False
    
    def __post_init__(self):
        """Validate processing options."""
        valid_qualities = ["draft", "standard", "high"]
        if self.quality not in valid_qualities:
            raise ValueError(f"Quality must be one of {valid_qualities}")
        
        valid_formats = ["png", "pdf", "cbz", "jpg"]
        for fmt in self.export_formats:
            if fmt not in valid_formats:
                raise ValueError(f"Export format '{fmt}' not supported. Must be one of {valid_formats}")
    
    def should_process_page(self, page_number: int) -> bool:
        """Check if a page should be processed based on page range."""
        if self.page_range is None:
            return True
        start, end = self.page_range
        return start <= page_number <= end


@dataclass
class StyleConfig:
    """Style configuration for consistent comic generation."""
    name: str
    art_style: str
    color_palette: str
    line_weight: str
    shading: str
    custom_prompts: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate style configuration."""
        if not self.name:
            raise ValueError("Style must have a name")
        if not self.art_style:
            raise ValueError("Style must have an art style")
    
    def get_style_prompt(self) -> str:
        """Generate style prompt for image generation."""
        parts = [
            f"Art style: {self.art_style}",
            f"Color palette: {self.color_palette}",
            f"Line weight: {self.line_weight}",
            f"Shading: {self.shading}",
        ]
        
        # Add custom prompts if any
        for key, value in self.custom_prompts.items():
            parts.append(f"{key}: {value}")
        
        return "\n".join(parts)


@dataclass
class ValidationResult:
    """Result of script validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Update validity based on errors."""
        if self.errors:
            self.is_valid = False
    
    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def get_message(self) -> str:
        """Get formatted validation message."""
        if self.is_valid:
            msg = "✓ Script is valid"
            if self.warnings:
                msg += f"\n\nWarnings ({len(self.warnings)}):\n"
                msg += "\n".join(f"  - {w}" for w in self.warnings)
            return msg
        else:
            msg = f"✗ Script validation failed with {len(self.errors)} error(s):\n"
            msg += "\n".join(f"  - {e}" for e in self.errors)
            if self.warnings:
                msg += f"\n\nWarnings ({len(self.warnings)}):\n"
                msg += "\n".join(f"  - {w}" for w in self.warnings)
            return msg