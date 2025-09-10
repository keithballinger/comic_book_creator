"""Data models for reference experiments."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


class RefExpParseError(Exception):
    """Raised when YAML file parsing fails."""
    pass


class RefExpValidationError(Exception):
    """Raised when template validation fails."""
    pass


class RefExpSchemaError(Exception):
    """Raised when YAML schema is invalid."""
    pass


@dataclass
class RefExperiment:
    """Represents a reference experiment configuration."""
    
    name: str
    prompt_template: str
    variables: Dict[str, List[str]]
    source_file: str
    description: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    image_settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the experiment after initialization."""
        if not self.name:
            raise RefExpValidationError("Experiment name is required")
        if not self.prompt_template:
            raise RefExpValidationError("Prompt template is required")
        if not self.variables:
            raise RefExpValidationError("At least one variable is required")
            
    def get_total_combinations(self) -> int:
        """Calculate total number of possible combinations."""
        total = 1
        for values in self.variables.values():
            total *= len(values)
        return total
    
    def validate_template(self) -> List[str]:
        """Validate that all template variables are defined.
        
        Returns:
            List of undefined variables (empty if all defined)
        """
        import re
        # Find all {variable} patterns in template
        template_vars = set(re.findall(r'\{(\w+)\}', self.prompt_template))
        defined_vars = set(self.variables.keys())
        undefined = template_vars - defined_vars
        return list(undefined)


@dataclass
class Combination:
    """Represents a single combination of variable values."""
    
    id: int
    prompt: str
    variables: Dict[str, str]
    hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Generate hash if not provided."""
        if not self.hash:
            import hashlib
            # Create stable hash from prompt
            self.hash = hashlib.md5(self.prompt.encode()).hexdigest()[:8]
    
    def get_filename_suffix(self) -> str:
        """Generate filename suffix from variable values."""
        parts = []
        for key, value in sorted(self.variables.items()):
            # Sanitize value for filename
            safe_value = "".join(c if c.isalnum() or c in "-_" else "_" 
                                for c in str(value))
            # Truncate if too long
            if len(safe_value) > 20:
                safe_value = safe_value[:20]
            parts.append(safe_value)
        return "_".join(parts)


@dataclass
class GeneratedImage:
    """Represents a generated image from an experiment."""
    
    combination: Combination
    image_data: bytes
    filepath: str
    timestamp: datetime
    generation_metadata: Dict[str, Any] = field(default_factory=dict)
    experiment_name: str = ""
    model_used: str = "gemini-2.5-flash-image-preview"
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    def get_relative_path(self, base_dir: str = "") -> str:
        """Get path relative to base directory."""
        if base_dir:
            try:
                return str(Path(self.filepath).relative_to(base_dir))
            except ValueError:
                # If not relative to base_dir, return full path
                return self.filepath
        return self.filepath


@dataclass
class ExperimentSession:
    """Represents a complete experiment session."""
    
    experiment: RefExperiment
    generated_images: List[GeneratedImage]
    start_time: datetime
    end_time: Optional[datetime] = None
    total_combinations: int = 0
    generated_count: int = 0
    failed_count: int = 0
    session_id: str = ""
    errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize session details."""
        if not self.start_time:
            self.start_time = datetime.now()
        if not self.session_id:
            # Generate session ID from timestamp
            self.session_id = self.start_time.strftime("%Y%m%d_%H%M%S")
        if not self.total_combinations:
            self.total_combinations = self.experiment.get_total_combinations()
    
    def mark_complete(self):
        """Mark the session as complete."""
        self.end_time = datetime.now()
        self.generated_count = len(self.generated_images)
    
    def add_error(self, error: str):
        """Add an error to the session."""
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")
        self.failed_count += 1
    
    def get_duration(self) -> float:
        """Get session duration in seconds."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_success_rate(self) -> float:
        """Calculate success rate as percentage."""
        total_attempted = self.generated_count + self.failed_count
        if total_attempted == 0:
            return 0.0
        return (self.generated_count / total_attempted) * 100