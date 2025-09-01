"""Mock Gemini client for testing without API calls."""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from PIL import Image, ImageDraw
import io

from src.models import Panel, CharacterReference

logger = logging.getLogger(__name__)


class MockGeminiClient:
    """Mock client that generates placeholder images for testing."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize mock client."""
        self.api_key = api_key or "mock-api-key"
        self.text_model = 'mock-text-model'
        self.image_model = 'mock-image-model'
        logger.info("Using MOCK Gemini client - no API calls will be made")
        
    async def generate_panel_image(
        self, 
        prompt: str, 
        reference_images: Optional[List[bytes]] = None,
        style_config: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate a placeholder comic panel image.
        
        Args:
            prompt: Text prompt describing the panel
            reference_images: Optional reference images for consistency
            style_config: Optional style configuration
            
        Returns:
            Generated placeholder image data as bytes
        """
        logger.info(f"Mock generating panel for prompt: {prompt[:50]}...")
        
        # Create a placeholder image
        width, height = 800, 600
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw border
        draw.rectangle([0, 0, width-1, height-1], outline='black', width=3)
        
        # Add text
        text_lines = [
            "MOCK PANEL",
            f"Prompt: {prompt[:40]}...",
        ]
        if style_config:
            text_lines.append(f"Style: {style_config.get('art_style', 'default')}")
        
        y = 20
        for line in text_lines:
            draw.text((10, y), line, fill='black')
            y += 30
        
        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    async def enhance_panel_description(
        self, 
        panel: Panel,
        character_refs: Optional[Dict[str, CharacterReference]] = None
    ) -> str:
        """Mock enhancement of panel descriptions.
        
        Args:
            panel: Panel object with description
            character_refs: Character reference information
            
        Returns:
            Enhanced description (just returns original with prefix)
        """
        logger.info(f"Mock enhancing panel {panel.number} description")
        enhanced = f"[ENHANCED] {panel.description}"
        
        if character_refs and panel.characters:
            enhanced += f" Characters: {', '.join(panel.characters)}"
            
        return enhanced
    
    async def generate_character_reference(
        self,
        character_name: str,
        description: str
    ) -> CharacterReference:
        """Generate a mock character reference.
        
        Args:
            character_name: Name of the character
            description: Text description of the character
            
        Returns:
            Mock CharacterReference object
        """
        logger.info(f"Mock generating reference for character: {character_name}")
        
        appearance = f"[MOCK APPEARANCE] {character_name}: {description}. "
        appearance += "Tall figure with distinctive features, wearing signature outfit."
        
        return CharacterReference(
            name=character_name,
            appearance_description=appearance
        )
    
    def _build_image_prompt(
        self,
        base_prompt: str,
        style_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build complete image generation prompt with style."""
        return f"[MOCK] {base_prompt}"
    
    def _build_enhancement_prompt(
        self,
        panel: Panel,
        character_refs: Optional[Dict[str, CharacterReference]] = None
    ) -> str:
        """Build prompt for enhancing panel description."""
        return f"[MOCK] Enhance panel {panel.number}: {panel.description}"