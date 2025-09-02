"""Reference data models for comic book generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


@dataclass
class BaseReference(ABC):
    """Base class for all reference types."""
    
    name: str
    description: str
    style_notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the reference after initialization."""
        self.validate()
    
    @abstractmethod
    def validate(self) -> None:
        """Validate the reference data.
        
        Raises:
            ValueError: If the reference data is invalid
        """
        if not self.name or not self.name.strip():
            raise ValueError("Reference name cannot be empty")
        
        if not self.description or not self.description.strip():
            raise ValueError("Reference description cannot be empty")
        
        # Sanitize name for filesystem compatibility
        invalid_chars = '<>:"/\\|?*'
        if any(char in self.name for char in invalid_chars):
            raise ValueError(f"Reference name contains invalid characters: {invalid_chars}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert reference to dictionary for JSON serialization."""
        data = {
            "name": self.name,
            "description": self.description,
            "style_notes": self.style_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "type": self.__class__.__name__.lower().replace("reference", ""),
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseReference':
        """Create reference from dictionary."""
        # Convert datetime strings back to datetime objects
        if "created_at" in data:
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        # Remove type field as it's not part of the constructor
        data.pop("type", None)
        
        return cls(**data)
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now()


@dataclass
class CharacterReference(BaseReference):
    """Reference for character consistency across panels."""
    
    poses: List[str] = field(default_factory=list)
    expressions: List[str] = field(default_factory=list)
    outfits: List[str] = field(default_factory=list)
    images: Dict[str, str] = field(default_factory=dict)  # combination -> filename
    age_range: str = ""
    physical_traits: List[str] = field(default_factory=list)
    personality_traits: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate character reference data."""
        super().validate()
        
        # Validate poses
        valid_poses = [
            "standing", "sitting", "running", "walking", "fighting", "pointing",
            "climbing", "jumping", "lying", "kneeling", "crouching", "flying"
        ]
        for pose in self.poses:
            if pose not in valid_poses:
                # Allow custom poses but warn
                pass
        
        # Validate expressions
        valid_expressions = [
            "neutral", "happy", "sad", "angry", "surprised", "worried",
            "determined", "confused", "excited", "focused", "scared", "confident"
        ]
        for expression in self.expressions:
            if expression not in valid_expressions:
                # Allow custom expressions but warn
                pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with character-specific fields."""
        data = super().to_dict()
        data.update({
            "poses": self.poses,
            "expressions": self.expressions,
            "outfits": self.outfits,
            "images": self.images,
            "age_range": self.age_range,
            "physical_traits": self.physical_traits,
            "personality_traits": self.personality_traits,
        })
        return data
    
    def get_image_key(self, pose: str, expression: str = "neutral", outfit: str = "default") -> str:
        """Generate image key for pose/expression/outfit combination."""
        return f"{pose}_{expression}_{outfit}".lower()
    
    def has_image(self, pose: str, expression: str = "neutral", outfit: str = "default") -> bool:
        """Check if image exists for given combination."""
        key = self.get_image_key(pose, expression, outfit)
        return key in self.images
    
    def add_image(self, pose: str, filename: str, expression: str = "neutral", outfit: str = "default"):
        """Add image filename for pose/expression/outfit combination."""
        key = self.get_image_key(pose, expression, outfit)
        self.images[key] = filename
        self.update_timestamp()


@dataclass
class LocationReference(BaseReference):
    """Reference for location consistency across panels."""
    
    location_type: str = ""  # interior, exterior, mixed
    angles: List[str] = field(default_factory=list)
    lighting_conditions: List[str] = field(default_factory=list)
    time_of_day: List[str] = field(default_factory=list)
    weather_conditions: List[str] = field(default_factory=list)
    images: Dict[str, str] = field(default_factory=dict)  # angle_lighting_time -> filename
    architectural_style: str = ""
    key_features: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate location reference data."""
        super().validate()
        
        # Validate location type
        valid_types = ["interior", "exterior", "mixed"]
        if self.location_type and self.location_type not in valid_types:
            raise ValueError(f"Invalid location type: {self.location_type}")
        
        # Validate angles
        valid_angles = [
            "wide-shot", "medium-shot", "close-up", "aerial", "ground-level",
            "bird's-eye", "worm's-eye", "establishing", "detail"
        ]
        for angle in self.angles:
            if angle not in valid_angles:
                # Allow custom angles but warn
                pass
        
        # Validate lighting
        valid_lighting = [
            "dawn", "morning", "midday", "afternoon", "dusk", "night",
            "bright", "dim", "dramatic", "soft", "harsh", "natural", "artificial"
        ]
        for lighting in self.lighting_conditions:
            if lighting not in valid_lighting:
                # Allow custom lighting but warn
                pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with location-specific fields."""
        data = super().to_dict()
        data.update({
            "location_type": self.location_type,
            "angles": self.angles,
            "lighting_conditions": self.lighting_conditions,
            "time_of_day": self.time_of_day,
            "weather_conditions": self.weather_conditions,
            "images": self.images,
            "architectural_style": self.architectural_style,
            "key_features": self.key_features,
        })
        return data
    
    def get_image_key(self, angle: str, lighting: str = "natural", time: str = "day") -> str:
        """Generate image key for angle/lighting/time combination."""
        return f"{angle}_{lighting}_{time}".lower()
    
    def has_image(self, angle: str, lighting: str = "natural", time: str = "day") -> bool:
        """Check if image exists for given combination."""
        key = self.get_image_key(angle, lighting, time)
        return key in self.images
    
    def add_image(self, angle: str, filename: str, lighting: str = "natural", time: str = "day"):
        """Add image filename for angle/lighting/time combination."""
        key = self.get_image_key(angle, lighting, time)
        self.images[key] = filename
        self.update_timestamp()


@dataclass
class ObjectReference(BaseReference):
    """Reference for object consistency across panels."""
    
    object_type: str = ""  # weapon, tool, vehicle, artifact, etc.
    views: List[str] = field(default_factory=list)
    states: List[str] = field(default_factory=list)  # new, aged, broken, magical, etc.
    size_category: str = ""  # tiny, small, medium, large, huge
    images: Dict[str, str] = field(default_factory=dict)  # view_state -> filename
    materials: List[str] = field(default_factory=list)
    colors: List[str] = field(default_factory=list)
    special_properties: List[str] = field(default_factory=list)
    
    def validate(self) -> None:
        """Validate object reference data."""
        super().validate()
        
        # Validate size category
        valid_sizes = ["tiny", "small", "medium", "large", "huge"]
        if self.size_category and self.size_category not in valid_sizes:
            raise ValueError(f"Invalid size category: {self.size_category}")
        
        # Validate views
        valid_views = [
            "front", "back", "left", "right", "top", "bottom",
            "three-quarter", "profile", "detail", "action", "closed", "open"
        ]
        for view in self.views:
            if view not in valid_views:
                # Allow custom views but warn
                pass
        
        # Validate states
        valid_states = [
            "new", "worn", "aged", "broken", "damaged", "repaired",
            "magical", "glowing", "active", "inactive", "pristine"
        ]
        for state in self.states:
            if state not in valid_states:
                # Allow custom states but warn
                pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with object-specific fields."""
        data = super().to_dict()
        data.update({
            "object_type": self.object_type,
            "views": self.views,
            "states": self.states,
            "size_category": self.size_category,
            "images": self.images,
            "materials": self.materials,
            "colors": self.colors,
            "special_properties": self.special_properties,
        })
        return data
    
    def get_image_key(self, view: str, state: str = "new") -> str:
        """Generate image key for view/state combination."""
        return f"{view}_{state}".lower()
    
    def has_image(self, view: str, state: str = "new") -> bool:
        """Check if image exists for given combination."""
        key = self.get_image_key(view, state)
        return key in self.images
    
    def add_image(self, view: str, filename: str, state: str = "new"):
        """Add image filename for view/state combination."""
        key = self.get_image_key(view, state)
        self.images[key] = filename
        self.update_timestamp()


@dataclass
class StyleGuide(BaseReference):
    """Style guide for consistent visual design."""
    
    art_style: str = ""  # realistic, cartoon, anime, noir, etc.
    color_palette: List[str] = field(default_factory=list)  # hex color codes
    color_mood: str = ""  # warm, cool, vibrant, muted, etc.
    line_style: str = ""  # clean, sketchy, bold, thin, etc.
    lighting_style: str = ""  # dramatic, soft, high-contrast, etc.
    typography: str = ""  # font style preferences
    reference_image: str = ""  # filename of style reference image
    texture_style: str = ""  # smooth, textured, painterly, etc.
    composition_style: str = ""  # dynamic, static, cinematic, etc.
    
    def validate(self) -> None:
        """Validate style guide data."""
        super().validate()
        
        # Validate color palette (hex codes)
        for color in self.color_palette:
            if not color.startswith('#') or len(color) != 7:
                try:
                    # Try to parse as hex
                    int(color.lstrip('#'), 16)
                except ValueError:
                    raise ValueError(f"Invalid color code: {color}")
        
        # Validate art style
        valid_styles = [
            "realistic", "cartoon", "anime", "manga", "comic-book",
            "noir", "watercolor", "oil-painting", "sketch", "digital-art"
        ]
        if self.art_style and self.art_style not in valid_styles:
            # Allow custom styles but warn
            pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with style guide fields."""
        data = super().to_dict()
        data.update({
            "art_style": self.art_style,
            "color_palette": self.color_palette,
            "color_mood": self.color_mood,
            "line_style": self.line_style,
            "lighting_style": self.lighting_style,
            "typography": self.typography,
            "reference_image": self.reference_image,
            "texture_style": self.texture_style,
            "composition_style": self.composition_style,
        })
        return data
    
    def add_color(self, color: str):
        """Add color to palette after validation."""
        if not color.startswith('#'):
            color = '#' + color
        
        # Validate hex color
        try:
            int(color.lstrip('#'), 16)
            if color not in self.color_palette:
                self.color_palette.append(color)
                self.update_timestamp()
        except ValueError:
            raise ValueError(f"Invalid color code: {color}")
    
    def remove_color(self, color: str):
        """Remove color from palette."""
        if color in self.color_palette:
            self.color_palette.remove(color)
            self.update_timestamp()


def create_reference_from_dict(data: Dict[str, Any]) -> BaseReference:
    """Factory function to create reference from dictionary based on type."""
    ref_type = data.get("type", "").lower()
    
    type_mapping = {
        "character": CharacterReference,
        "location": LocationReference,
        "object": ObjectReference,
        "styleguide": StyleGuide,
    }
    
    reference_class = type_mapping.get(ref_type)
    if not reference_class:
        raise ValueError(f"Unknown reference type: {ref_type}")
    
    return reference_class.from_dict(data)