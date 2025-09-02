"""Gemini API client for Comic Book Creator."""

import os
import asyncio
from typing import Any, Dict, List, Optional
import logging
from dotenv import load_dotenv
from google import genai

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
        self.image_model = 'imagen-3'  # Image generation model (when available)
        
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
            
            # Configure image generation
            from google.genai.types import GenerateImagesConfig
            config = GenerateImagesConfig(
                numberOfImages=1,
                aspectRatio='3:4',  # Comic panel aspect ratio
                imageSize='1024x1024'
            )
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.models.generate_images(
                    model=self.image_model,
                    prompt=full_prompt,
                    config=config
                )
            )
            
            # Extract image data from response
            if response and response.generated_images:
                # Convert base64 or get raw bytes
                import base64
                image_data = response.generated_images[0].image.data
                if isinstance(image_data, str):
                    # If it's base64 encoded string
                    return base64.b64decode(image_data)
                return image_data
            else:
                raise ValueError("No image generated from API")
                
        except Exception as e:
            logger.error(f"Error generating panel image: {e}")
            # For now, raise a clear error message about image generation not being available
            raise NotImplementedError(
                "Image generation is not yet available via the Gemini API. "
                "The imagen-3 model is expected to be released soon. "
                "Text generation and panel description enhancement are fully functional."
            )
    
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
        
        # Add base prompt
        prompt_parts.append("\nPanel description:")
        prompt_parts.append(base_prompt)
        
        # Add quality instructions
        prompt_parts.append("\nHigh quality comic book panel, professional artwork, detailed illustration")
        
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
        prompt = f"""
        Enhance this comic book panel description for image generation.
        Make it more visual, specific, and suitable for AI image generation.
        
        Original Panel {panel.number} description:
        {panel.description}
        """
        
        # Add character information if available
        if character_refs and panel.characters:
            prompt += "\n\nCharacters in this panel:"
            for char_name in panel.characters:
                if char_ref := character_refs.get(char_name):
                    prompt += f"\n- {char_name}: {char_ref.appearance_description}"
        
        # Add dialogue context if present
        if panel.dialogue:
            prompt += "\n\nDialogue context:"
            for dialogue in panel.dialogue:
                prompt += f"\n- {dialogue.character}: '{dialogue.text}'"
                if dialogue.emotion:
                    prompt += f" ({dialogue.emotion})"
        
        prompt += """
        
        Provide an enhanced visual description that includes:
        - Camera angle and framing
        - Character positions and expressions
        - Background details
        - Lighting and atmosphere
        - Important visual elements
        
        Keep it concise (2-3 sentences) and focus on visual elements.
        """
        
        return prompt