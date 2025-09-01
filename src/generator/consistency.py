"""Consistency manager for maintaining visual coherence across panels."""

import hashlib
import json
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
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize consistency manager.
        
        Args:
            cache_dir: Directory for caching consistency data
        """
        self.character_refs: Dict[str, CharacterReference] = {}
        self.style_config: Optional[StyleConfig] = None
        self.panel_history: List[GeneratedPanel] = []
        self.style_embeddings: Dict[str, Any] = {}
        
        # Cache directory for persistence
        self.cache_dir = Path(cache_dir) if cache_dir else Path(".cache/consistency")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Track visual elements for consistency
        self.visual_elements = {
            'backgrounds': {},
            'props': {},
            'lighting': None,
            'weather': None,
            'time_of_day': None,
        }
        
    def load_style(self, style_config: StyleConfig):
        """Load a style configuration.
        
        Args:
            style_config: Style configuration to use
        """
        self.style_config = style_config
        logger.info(f"Loaded style: {style_config.name}")
        
        # Save style config to cache
        style_cache_path = self.cache_dir / "style_config.json"
        with open(style_cache_path, 'w') as f:
            json.dump({
                'name': style_config.name,
                'art_style': style_config.art_style,
                'color_palette': style_config.color_palette,
                'line_weight': style_config.line_weight,
                'shading': style_config.shading,
                'custom_prompts': style_config.custom_prompts,
            }, f, indent=2)
    
    def register_character(self, character_ref: CharacterReference):
        """Register a character reference for consistency.
        
        Args:
            character_ref: Character reference to register
        """
        self.character_refs[character_ref.name] = character_ref
        logger.info(f"Registered character: {character_ref.name}")
        
        # Save character ref to cache
        char_cache_path = self.cache_dir / f"character_{character_ref.name}.json"
        with open(char_cache_path, 'w') as f:
            json.dump({
                'name': character_ref.name,
                'appearance_description': character_ref.appearance_description,
                'personality_traits': character_ref.personality_traits,
            }, f, indent=2)
    
    def build_consistent_prompt(
        self,
        base_description: str,
        previous_panels: Optional[List[GeneratedPanel]] = None
    ) -> str:
        """Build a prompt with consistency instructions.
        
        Args:
            base_description: Base panel description
            previous_panels: Previous panels for context
            
        Returns:
            Enhanced prompt with consistency instructions
        """
        prompt_parts = []
        
        # Add style configuration
        if self.style_config:
            prompt_parts.append(f"Create a comic book panel in {self.style_config.art_style} style.")
            prompt_parts.append(f"Color palette: {self.style_config.color_palette}")
            prompt_parts.append(f"Line weight: {self.style_config.line_weight}")
            prompt_parts.append(f"Shading style: {self.style_config.shading}")
            
            # Add custom style prompts
            for key, value in self.style_config.custom_prompts.items():
                prompt_parts.append(f"{key}: {value}")
        
        prompt_parts.append("")
        
        # Add visual consistency elements
        if self.visual_elements['lighting']:
            prompt_parts.append(f"Lighting: {self.visual_elements['lighting']}")
        if self.visual_elements['weather']:
            prompt_parts.append(f"Weather: {self.visual_elements['weather']}")
        if self.visual_elements['time_of_day']:
            prompt_parts.append(f"Time of day: {self.visual_elements['time_of_day']}")
        
        # Add panel description
        prompt_parts.append("\nPanel description:")
        prompt_parts.append(base_description)
        
        # Add character consistency instructions
        characters_in_desc = self._extract_characters(base_description)
        if characters_in_desc:
            prompt_parts.append("\nCharacter appearances:")
            for char_name in characters_in_desc:
                if char_ref := self.character_refs.get(char_name):
                    prompt_parts.append(f"- {char_ref.get_consistency_prompt()}")
        
        # Add continuity from previous panels
        if previous_panels:
            # Get most recent panels with same characters
            relevant_panels = self._get_relevant_panels(previous_panels, characters_in_desc)
            if relevant_panels:
                prompt_parts.append("\nMaintain visual consistency with previous panels:")
                prompt_parts.append("- Keep character appearances, proportions, and costumes consistent")
                prompt_parts.append("- Maintain the established art style and color scheme")
                prompt_parts.append("- Use consistent line weights and shading techniques")
        
        return "\n".join(prompt_parts)
    
    def get_reference_images(
        self,
        previous_panels: Optional[List[GeneratedPanel]] = None,
        characters: Optional[List[str]] = None
    ) -> List[bytes]:
        """Get reference images for consistency.
        
        Args:
            previous_panels: Previous generated panels
            characters: List of character names in current panel
            
        Returns:
            List of reference images as bytes
        """
        ref_images = []
        
        # Add character reference sheets if available
        if characters:
            for char_name in characters:
                if char_ref := self.character_refs.get(char_name):
                    if char_ref.reference_image:
                        ref_images.append(char_ref.reference_image)
        
        # Add recent panels with same characters for consistency
        if previous_panels and characters:
            # Get last 3 panels with overlapping characters
            relevant_count = 0
            for panel in reversed(previous_panels):
                if relevant_count >= 3:
                    break
                    
                panel_chars = panel.panel.characters if panel.panel else []
                if any(c in panel_chars for c in characters):
                    if panel.image_data:
                        ref_images.append(panel.image_data)
                        relevant_count += 1
        
        return ref_images
    
    def register_panel(self, generated_panel: GeneratedPanel):
        """Register a generated panel for future consistency.
        
        Args:
            generated_panel: The generated panel to register
        """
        self.panel_history.append(generated_panel)
        
        # Extract and store visual elements from the panel
        self._extract_visual_elements(generated_panel)
        
        # Save panel metadata to cache
        panel_cache_path = self.cache_dir / f"panel_{len(self.panel_history)}.json"
        with open(panel_cache_path, 'w') as f:
            json.dump({
                'panel_number': generated_panel.panel.number if generated_panel.panel else 0,
                'characters': generated_panel.panel.characters if generated_panel.panel else [],
                'generation_time': generated_panel.generation_time,
                'metadata': generated_panel.metadata,
            }, f, indent=2)
        
        logger.info(f"Registered panel {generated_panel.panel.number if generated_panel.panel else 'N/A'}")
    
    def update_visual_element(self, element_type: str, value: Any):
        """Update a visual element for consistency.
        
        Args:
            element_type: Type of visual element (lighting, weather, etc.)
            value: Value for the element
        """
        if element_type in self.visual_elements:
            self.visual_elements[element_type] = value
            logger.debug(f"Updated {element_type}: {value}")
    
    def get_style_hash(self) -> str:
        """Get a hash of the current style configuration.
        
        Returns:
            Hash string for caching purposes
        """
        if not self.style_config:
            return "default"
            
        style_data = f"{self.style_config.art_style}_{self.style_config.color_palette}_{self.style_config.line_weight}"
        return hashlib.md5(style_data.encode()).hexdigest()
    
    def save_session(self, session_name: str):
        """Save the current consistency session.
        
        Args:
            session_name: Name for the session
        """
        session_path = self.cache_dir / f"session_{session_name}.json"
        
        session_data = {
            'character_refs': {
                name: {
                    'name': ref.name,
                    'appearance_description': ref.appearance_description,
                    'personality_traits': ref.personality_traits,
                }
                for name, ref in self.character_refs.items()
            },
            'visual_elements': self.visual_elements,
            'panel_count': len(self.panel_history),
        }
        
        with open(session_path, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        logger.info(f"Saved consistency session: {session_name}")
    
    def load_session(self, session_name: str) -> bool:
        """Load a saved consistency session.
        
        Args:
            session_name: Name of the session to load
            
        Returns:
            True if session loaded successfully
        """
        session_path = self.cache_dir / f"session_{session_name}.json"
        
        if not session_path.exists():
            logger.warning(f"Session not found: {session_name}")
            return False
        
        try:
            with open(session_path, 'r') as f:
                session_data = json.load(f)
            
            # Restore character references
            self.character_refs = {}
            for name, ref_data in session_data['character_refs'].items():
                self.character_refs[name] = CharacterReference(
                    name=ref_data['name'],
                    appearance_description=ref_data['appearance_description'],
                    personality_traits=ref_data.get('personality_traits', [])
                )
            
            # Restore visual elements
            self.visual_elements = session_data['visual_elements']
            
            logger.info(f"Loaded consistency session: {session_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False
    
    def _extract_characters(self, description: str) -> List[str]:
        """Extract character names from description.
        
        Args:
            description: Panel description text
            
        Returns:
            List of character names found
        """
        found_characters = []
        
        # Check for registered characters in the description
        for char_name in self.character_refs.keys():
            if char_name.lower() in description.lower():
                found_characters.append(char_name)
        
        return found_characters
    
    def _get_relevant_panels(
        self,
        previous_panels: List[GeneratedPanel],
        characters: List[str]
    ) -> List[GeneratedPanel]:
        """Get panels relevant to current characters.
        
        Args:
            previous_panels: List of previous panels
            characters: Characters in current panel
            
        Returns:
            List of relevant panels
        """
        if not characters:
            return []
        
        relevant = []
        for panel in previous_panels:
            if panel.panel and panel.panel.characters:
                if any(c in panel.panel.characters for c in characters):
                    relevant.append(panel)
        
        return relevant[-3:]  # Return last 3 relevant panels
    
    def _extract_visual_elements(self, generated_panel: GeneratedPanel):
        """Extract visual elements from a generated panel.
        
        Args:
            generated_panel: Panel to extract elements from
        """
        # This would ideally use image analysis or metadata
        # For now, we extract from the description
        if generated_panel.panel and generated_panel.panel.description:
            desc_lower = generated_panel.panel.description.lower()
            
            # Extract time of day hints
            if any(word in desc_lower for word in ['morning', 'dawn', 'sunrise']):
                self.visual_elements['time_of_day'] = 'morning'
            elif any(word in desc_lower for word in ['night', 'evening', 'dusk']):
                self.visual_elements['time_of_day'] = 'night'
            elif any(word in desc_lower for word in ['noon', 'midday']):
                self.visual_elements['time_of_day'] = 'noon'
            
            # Extract weather hints
            if any(word in desc_lower for word in ['rain', 'rainy', 'storm']):
                self.visual_elements['weather'] = 'rainy'
            elif any(word in desc_lower for word in ['snow', 'snowy', 'blizzard']):
                self.visual_elements['weather'] = 'snowy'
            elif any(word in desc_lower for word in ['sunny', 'clear']):
                self.visual_elements['weather'] = 'clear'