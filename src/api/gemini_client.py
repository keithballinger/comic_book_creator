"""Gemini API client for Comic Book Creator."""

import os
import asyncio
from typing import Any, Dict, List, Optional
import logging
from dotenv import load_dotenv
from google import genai
from PIL import Image

from src.models import Panel, CharacterReference

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for interacting with Gemini Flash 2.5 APIs."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini API client.
        
        Args:
            api_key: Optional API key (will use env variable if not provided)
        """
        load_dotenv()
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment or provided")
            
        self.client = genai.Client(api_key=self.api_key)
        self.text_model = 'gemini-2.0-flash-exp'  # Using latest available model
        self.image_model = 'gemini-2.5-flash-image-preview'  # Image generation model
        
    async def generate_panel_image(
        self, 
        prompt: str, 
        reference_images: Optional[List[bytes]] = None,
        style_config: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate comic panel image using Gemini image generation.
        
        Args:
            prompt: Text prompt describing the panel
            reference_images: Optional reference images for consistency
            style_config: Optional style configuration
            
        Returns:
            Generated image data as bytes
        """
        try:
            # Build the full prompt with style information
            full_prompt = self._build_image_prompt(prompt, style_config)
            
            # Run synchronous API call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            # Configure for image generation
            config = {
                'response_modalities': ['IMAGE', 'TEXT'],
                'temperature': 0.7,
                'top_p': 0.95,
            }
            
            # Build contents for the request
            # If we have reference images, include them in the request
            if reference_images:
                import base64
                # Build multimodal content with images and text
                parts = []
                # Add reference images first
                for ref_image in reference_images:
                    parts.append({
                        'inline_data': {
                            'data': base64.b64encode(ref_image).decode('utf-8'),
                            'mime_type': 'image/png'
                        }
                    })
                # Add the text prompt
                parts.append({
                    'text': f"Generate a comic book panel image based on this description:\n{full_prompt}"
                })
                contents = [{'parts': parts}]
            else:
                # Just text prompt if no references
                contents = f"Generate a comic book panel image based on this description:\n{full_prompt}"
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.image_model,
                    config=config,
                    contents=contents
                )
            )
            
            # Extract image data from response
            if response and response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            # Check if this part contains image data
                            if hasattr(part, 'inline_data') and part.inline_data:
                                # The data is already in bytes format
                                if hasattr(part.inline_data, 'data'):
                                    return part.inline_data.data
                            
            # If no image was generated, raise an error
            raise ValueError("No image generated from API")
                
        except Exception as e:
            logger.error(f"Error generating panel image: {e}")
            raise
    
    async def enhance_panel_description(
        self, 
        panel: Panel,
        character_refs: Optional[Dict[str, CharacterReference]] = None
    ) -> str:
        """Use text model to enhance panel descriptions for better image generation.
        
        Args:
            panel: Panel object with description
            character_refs: Character reference information
            
        Returns:
            Enhanced description suitable for image generation
        """
        try:
            # Build the enhancement prompt
            prompt = self._build_enhancement_prompt(panel, character_refs)
            
            # Configure the request
            config = {
                'temperature': 0.7,
                'max_output_tokens': 500,
                'top_k': 40,
                'top_p': 0.95,
            }
            
            # Generate enhanced description
            contents = prompt
            
            # Run synchronous API call in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.text_model,
                    config=config,
                    contents=contents
                )
            )
            
            # Extract text from response
            if response and response.text:
                return response.text.strip()
            else:
                return panel.description
            
        except Exception as e:
            logger.error(f"Error enhancing panel description: {e}")
            # Return original description if enhancement fails
            return panel.description
    
    async def generate_character_reference(
        self,
        character_name: str,
        description: str
    ) -> CharacterReference:
        """Generate a character reference for consistency.
        
        Args:
            character_name: Name of the character
            description: Text description of the character
            
        Returns:
            CharacterReference object with detailed appearance
        """
        try:
            prompt = f"""
            Create a detailed character design sheet description for a comic book character:
            
            Character Name: {character_name}
            Basic Description: {description}
            
            Provide a detailed description including:
            - Physical appearance (height, build, hair, eyes, distinguishing features)
            - Costume/clothing details
            - Color scheme
            - Personality traits that affect appearance
            - Any props or accessories
            
            Format as a concise paragraph suitable for image generation.
            """
            
            config = {
                'temperature': 0.7,
                'max_output_tokens': 300,
            }
            
            # Run synchronous API call in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.text_model,
                    config=config,
                    contents=prompt
                )
            )
            
            # Extract text from response
            appearance_description = ''
            if response and response.text:
                appearance_description = response.text.strip()
            else:
                appearance_description = description
                    
            return CharacterReference(
                name=character_name,
                appearance_description=appearance_description
            )
            
        except Exception as e:
            logger.error(f"Error generating character reference: {e}")
            # Return basic reference if generation fails
            return CharacterReference(
                name=character_name,
                appearance_description=description
            )
    
    def _build_image_prompt(
        self,
        base_prompt: str,
        style_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build complete image generation prompt with style.
        
        Args:
            base_prompt: Base description of the panel
            style_config: Style configuration dictionary
            
        Returns:
            Complete prompt for image generation
        """
        prompt_parts = []
        
        # Add style configuration if provided
        if style_config:
            if 'art_style' in style_config:
                prompt_parts.append(f"Art style: {style_config['art_style']}")
            if 'color_palette' in style_config:
                prompt_parts.append(f"Color palette: {style_config['color_palette']}")
            if 'line_weight' in style_config:
                prompt_parts.append(f"Line weight: {style_config['line_weight']}")
            if 'shading' in style_config:
                prompt_parts.append(f"Shading: {style_config['shading']}")
        
        # Add strict single panel instruction
        prompt_parts.append("\n⚠️ CRITICAL: Generate EXACTLY ONE SINGLE PANEL - not multiple panels, not a grid, just ONE rectangular image.")
        
        # Add base prompt
        prompt_parts.append("\nCreate a single comic book panel with the following:")
        prompt_parts.append(base_prompt)
        
        # Add instructions for text rendering
        prompt_parts.append("\nIMPORTANT TEXT PLACEMENT RULES:")
        prompt_parts.append("- ALL text elements MUST be INSIDE the panel boundaries")
        prompt_parts.append("- Captions: Yellow/white rectangular boxes at top or bottom INSIDE the panel")
        prompt_parts.append("- Speech bubbles: White ovals with tails pointing to speakers, INSIDE the panel")
        prompt_parts.append("- Thought bubbles: Cloud-shaped bubbles INSIDE the panel")
        prompt_parts.append("- Sound effects: Stylized text integrated into the artwork")
        prompt_parts.append("- NO text should extend beyond the panel edges")
        
        # Add quality instructions
        prompt_parts.append("\nOutput: ONE high-quality comic book panel with exact dimensions, professional artwork, single rectangular illustration with ALL text contained within panel boundaries.")
        
        return "\n".join(prompt_parts)
    
    def _build_enhancement_prompt(
        self,
        panel: Panel,
        character_refs: Optional[Dict[str, CharacterReference]] = None
    ) -> str:
        """Build prompt for enhancing panel description.
        
        Args:
            panel: Panel object
            character_refs: Character reference information
            
        Returns:
            Prompt for description enhancement
        """
        # Simply pass the raw panel text to Gemini for interpretation
        prompt = f"""
        Convert this comic book panel script into a detailed visual description for image generation.
        
        Panel {panel.number}:
        {panel.raw_text if hasattr(panel, 'raw_text') else panel.description}
        
        Create a visual description that includes:
        - The scene setting and background
        - Character positions and expressions
        - Any dialogue in speech bubbles (regular bubbles for speech, cloud-shaped for thoughts)
        - Any captions in rectangular boxes
        - Any sound effects as stylized text
        - Camera angle and composition
        
        Make the description detailed and visual, suitable for AI image generation.
        Include ALL text elements (dialogue, captions, sound effects) that should appear in the panel.
        """
        
        # Add character references if available
        if character_refs and panel.characters:
            prompt += "\n\nCharacter references:"
            for char_name in panel.characters:
                if char_ref := character_refs.get(char_name):
                    prompt += f"\n- {char_name}: {char_ref.appearance_description}"
        
        return prompt
    
    async def generate_image(
        self,
        prompt: str,
        context_images: Optional[List[Image.Image]] = None,
        width: int = 1024,
        height: int = 1024,
        quality: str = "high"
    ) -> bytes:
        """Generate a single image using Gemini Flash 2.5 Image Preview.
        
        Args:
            prompt: Text prompt for image generation
            context_images: Optional PIL images for context/consistency
            width: Image width in pixels
            height: Image height in pixels
            quality: Quality setting (high/medium/low)
            
        Returns:
            Generated image as bytes
        """
        logger.info("Calling Gemini API for image generation")
        
        try:
            # Prepare contents for multimodal API call
            contents = []
            
            # Add context images if provided
            if context_images:
                for img in context_images:
                    contents.append(img)
            
            # Add the text prompt
            contents.append(prompt)
            
            # Configure generation
            config = {
                'response_modalities': ['IMAGE'],
            }
            
            # Run API call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_content(
                    model=self.image_model,
                    contents=contents,
                    config=genai.types.GenerateContentConfig(**config)
                )
            )
            
            # Extract image from response
            if response and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        for part in candidate.content.parts:
                            # Debug: log part attributes
                            logger.debug(f"Part type: {type(part)}, attrs: {dir(part)}")
                            
                            # Check for inline_data (base64 encoded image)
                            if hasattr(part, 'inline_data') and part.inline_data:
                                logger.info("Found inline_data in response")
                                if hasattr(part.inline_data, 'data'):
                                    import base64
                                    image_data = base64.b64decode(part.inline_data.data)
                                    logger.info("Successfully extracted image from inline_data")
                                    return image_data
                            
                            # Check for direct data attribute
                            if hasattr(part, 'data'):
                                if hasattr(part, 'mime_type') and part.mime_type.startswith('image'):
                                    logger.info("Successfully generated image (direct data)")
                                    return part.data
                            
                            # Check for text response (might be an error or different format)
                            if hasattr(part, 'text'):
                                logger.warning(f"Got text response instead of image: {part.text[:200]}")
            
            logger.error(f"No image found. Response candidates: {len(response.candidates) if response else 0}")
            raise ValueError("No image data in response")
            
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            raise