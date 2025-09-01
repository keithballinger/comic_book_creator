"""Script data models for Comic Book Creator."""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class PanelType(Enum):
    """Types of comic panels."""
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    SPLASH = "splash"


class DialogueType(Enum):
    """Types of dialogue presentation."""
    BALLOON = "balloon"  # Standard speech balloon
    THOUGHT = "thought"  # Thought bubble
    WHISPER = "whisper"  # Whispered/quiet speech
    SHOUT = "shout"     # Shouting/yelling


@dataclass
class Dialogue:
    """Dialogue spoken by a character."""
    character: str
    text: str
    emotion: Optional[str] = None
    type: DialogueType = DialogueType.BALLOON
    
    def __post_init__(self):
        """Validate dialogue data."""
        if not self.character:
            raise ValueError("Dialogue must have a character")
        if not self.text:
            raise ValueError("Dialogue must have text")


@dataclass
class Caption:
    """Caption or narration text."""
    text: str
    position: str = "top"
    style: str = "narration"
    
    def __post_init__(self):
        """Validate caption data."""
        if not self.text:
            raise ValueError("Caption must have text")
        valid_positions = ["top", "bottom", "left", "right", "center", "middle"]
        if self.position not in valid_positions:
            raise ValueError(f"Caption position must be one of {valid_positions}")


@dataclass
class SoundEffect:
    """Sound effect in a panel."""
    text: str
    style: str = "bold"
    size: str = "large"
    position: Optional[dict[str, float]] = None
    
    def __post_init__(self):
        """Validate sound effect data."""
        if not self.text:
            raise ValueError("Sound effect must have text")
        valid_sizes = ["small", "medium", "large", "extra-large", "huge"]
        if self.size not in valid_sizes:
            raise ValueError(f"Sound effect size must be one of {valid_sizes}")


@dataclass
class Panel:
    """A single comic panel."""
    number: int
    description: str
    panel_type: PanelType = PanelType.MEDIUM
    dialogue: List[Dialogue] = field(default_factory=list)
    captions: List[Caption] = field(default_factory=list)
    sound_effects: List[SoundEffect] = field(default_factory=list)
    characters: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate panel data."""
        if self.number <= 0:
            raise ValueError("Panel number must be positive")
        if not self.description:
            raise ValueError("Panel must have a description")
        
        # Ensure panel_type is PanelType enum
        if isinstance(self.panel_type, str):
            try:
                self.panel_type = PanelType(self.panel_type)
            except ValueError:
                # Try to match by name
                for pt in PanelType:
                    if pt.name.lower() == self.panel_type.lower():
                        self.panel_type = pt
                        break
                else:
                    self.panel_type = PanelType.MEDIUM
    
    def add_dialogue(self, character: str, text: str, emotion: Optional[str] = None):
        """Add dialogue to the panel."""
        self.dialogue.append(Dialogue(character, text, emotion))
        if character not in self.characters:
            self.characters.append(character)
    
    def add_caption(self, text: str, position: str = "top", style: str = "narration"):
        """Add a caption to the panel."""
        self.captions.append(Caption(text, position, style))
    
    def add_sound_effect(self, text: str, style: str = "bold", size: str = "large"):
        """Add a sound effect to the panel."""
        self.sound_effects.append(SoundEffect(text, style, size))


@dataclass
class Page:
    """A comic book page containing panels."""
    number: int
    panels: List[Panel] = field(default_factory=list)
    layout: str = "standard"  # standard, splash, double-spread
    
    def __post_init__(self):
        """Validate page data."""
        if self.number <= 0:
            raise ValueError("Page number must be positive")
        valid_layouts = ["standard", "splash", "double-spread"]
        if self.layout not in valid_layouts:
            raise ValueError(f"Page layout must be one of {valid_layouts}")
    
    def add_panel(self, panel: Panel):
        """Add a panel to the page."""
        self.panels.append(panel)
    
    def get_panel(self, panel_number: int) -> Optional[Panel]:
        """Get a panel by number."""
        for panel in self.panels:
            if panel.number == panel_number:
                return panel
        return None


@dataclass
class ComicScript:
    """Complete comic book script."""
    title: str = ""
    pages: List[Page] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize script metadata."""
        if not self.metadata:
            self.metadata = {
                "total_pages": 0,
                "total_panels": 0,
                "characters": [],
            }
        self.update_metadata()
    
    def add_page(self, page: Page):
        """Add a page to the script."""
        self.pages.append(page)
        self.update_metadata()
    
    def get_page(self, page_number: int) -> Optional[Page]:
        """Get a page by number."""
        for page in self.pages:
            if page.number == page_number:
                return page
        return None
    
    def update_metadata(self):
        """Update script metadata."""
        self.metadata["total_pages"] = len(self.pages)
        self.metadata["total_panels"] = sum(len(page.panels) for page in self.pages)
        
        # Collect all unique characters
        characters = set()
        for page in self.pages:
            for panel in page.panels:
                characters.update(panel.characters)
        self.metadata["characters"] = sorted(list(characters))
    
    def validate(self) -> List[str]:
        """Validate the script structure.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for missing title
        if not self.title:
            errors.append("Script must have a title")
        
        # Check for pages
        if not self.pages:
            errors.append("Script must have at least one page")
        
        # Check page numbering
        page_numbers = [page.number for page in self.pages]
        if page_numbers != sorted(page_numbers):
            errors.append("Pages are not in sequential order")
        
        # Check for duplicate page numbers
        if len(page_numbers) != len(set(page_numbers)):
            errors.append("Duplicate page numbers found")
        
        # Check panels in each page
        for page in self.pages:
            if not page.panels:
                errors.append(f"Page {page.number} has no panels")
            
            # Check panel numbering within page
            panel_numbers = [panel.number for panel in page.panels]
            if panel_numbers != sorted(panel_numbers):
                errors.append(f"Panels in page {page.number} are not in sequential order")
            
            # Check for duplicate panel numbers
            if len(panel_numbers) != len(set(panel_numbers)):
                errors.append(f"Duplicate panel numbers in page {page.number}")
        
        return errors