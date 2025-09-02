"""Consistency manager for maintaining visual coherence across panels."""

from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from src.models import (
    CharacterReference,
    GeneratedPanel,
    Panel,
    StyleConfig,
)

logger = logging.getLogger(__name__)


class ConsistencyManager:
    """Manages visual and stylistic consistency across comic panels."""
    
    def __init__(self):
        """Initialize consistency manager."""
        self.character_refs: Dict[str, CharacterReference] = {}
        self.style_config: Optional[StyleConfig] = None
        self.panel_history: List[GeneratedPanel] = []
        self.style_embeddings: Dict[str, Any] = {}
        
        # Track visual elements for consistency
        self.visual_elements = {
            'backgrounds': {},
            'props': {},
            'locations': {},
        }
    
    def set_style(self, style_config: StyleConfig):
        """Set the global style configuration.
        
        Args:
            style_config: Style configuration for the comic
        """
        self.style_config = style_config
        logger.info(f"Style set: {style_config.art_style}")
    
    def register_character(self, character_ref: CharacterReference):
        """Register a character reference for consistency.
        
        Args:
            character_ref: Character reference with appearance details
        """
        self.character_refs[character_ref.name] = character_ref
        logger.info(f"Character registered: {character_ref.name}")
    
    def build_consistent_prompt(
        self,
        base_prompt: str,
        previous_panels: Optional[List[GeneratedPanel]] = None
    ) -> str:
        """Build a prompt that maintains consistency with previous panels.
        
        Args:
            base_prompt: Base panel description
            previous_panels: Previously generated panels for context
            
        Returns:
            Enhanced prompt with consistency instructions
        """
        prompt_parts = [base_prompt]
        
        # Add style consistency instructions
        if self.style_config:
            style_prompt = f"""
            Maintain consistent art style:
            - Art style: {self.style_config.art_style}
            - Color palette: {self.style_config.color_palette}
            - Line weight: {self.style_config.line_weight}
            - Shading: {self.style_config.shading}
            """
            prompt_parts.append(style_prompt)
        
        # Add consistency context from previous panels
        if previous_panels and len(previous_panels) > 0:
            recent_panel = previous_panels[-1]
            if recent_panel.metadata and 'prompt' in recent_panel.metadata:
                prompt_parts.append(
                    f"Previous panel context: {recent_panel.metadata['prompt'][:200]}..."
                )
        
        return "\n".join(prompt_parts)
    
    def get_reference_images(
        self,
        previous_panels: Optional[List[GeneratedPanel]] = None,
        character_names: Optional[List[str]] = None
    ) -> List[bytes]:
        """Get reference images for consistency.
        
        Args:
            previous_panels: Previous panels to use as references
            character_names: Characters appearing in current panel
            
        Returns:
            List of reference image bytes
        """
        reference_images = []
        
        # Add recent panels as references (up to 3)
        if previous_panels:
            for panel in previous_panels[-3:]:
                if panel.image_data:
                    reference_images.append(panel.image_data)
        
        return reference_images
    
    def register_panel(self, generated_panel: GeneratedPanel):
        """Register a generated panel for consistency tracking.
        
        Args:
            generated_panel: Generated panel to track
        """
        self.panel_history.append(generated_panel)
        
        # Extract and track visual elements
        if generated_panel.panel:
            panel = generated_panel.panel
            
            # Track characters
            for character in panel.characters:
                if character not in self.visual_elements.get('characters', {}):
                    self.visual_elements.setdefault('characters', {})[character] = []
                self.visual_elements['characters'][character].append(generated_panel)
        
        logger.debug(f"Panel registered: {len(self.panel_history)} total panels")
    
    def get_character_context(self, character_name: str) -> Optional[str]:
        """Get context about a character's appearance.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Character appearance context or None
        """
        if character_ref := self.character_refs.get(character_name):
            return character_ref.appearance_description
        return None
    
    def reset(self):
        """Reset consistency manager for a new comic."""
        self.character_refs.clear()
        self.style_config = None
        self.panel_history.clear()
        self.style_embeddings.clear()
        self.visual_elements = {
            'backgrounds': {},
            'props': {},
            'locations': {},
        }
        logger.info("Consistency manager reset")