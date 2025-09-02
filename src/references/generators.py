"""Reference generation system for comic book creation."""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import asyncio
from PIL import Image
from io import BytesIO

from .models import (
    BaseReference,
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
)
from .storage import ReferenceStorage
from src.api import GeminiClient

logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for reference generation."""
    
    image_width: int = 1024
    image_height: int = 1024
    quality: str = "high"  # high, medium, low
    style_consistency: float = 0.8  # 0.0 to 1.0
    batch_size: int = 3  # Number of images to generate in parallel
    retry_attempts: int = 3
    timeout_seconds: int = 60
    
    def get_quality_settings(self) -> Dict[str, Any]:
        """Get quality-specific generation settings."""
        quality_map = {
            "high": {"steps": 50, "cfg_scale": 7.5},
            "medium": {"steps": 30, "cfg_scale": 7.0},
            "low": {"steps": 20, "cfg_scale": 6.5},
        }
        return quality_map.get(self.quality, quality_map["medium"])


class BaseReferenceGenerator(ABC):
    """Base class for reference generation."""
    
    def __init__(
        self,
        gemini_client: GeminiClient,
        storage: Optional[ReferenceStorage] = None,
        config: Optional[GenerationConfig] = None
    ):
        """Initialize reference generator.
        
        Args:
            gemini_client: Gemini API client for image generation
            storage: Optional storage system for saving references
            config: Generation configuration
        """
        self.client = gemini_client
        self.storage = storage or ReferenceStorage()
        self.config = config or GenerationConfig()
    
    @abstractmethod
    async def generate_reference(
        self,
        name: str,
        description: str,
        **kwargs
    ) -> BaseReference:
        """Generate a complete reference with images.
        
        Args:
            name: Name of the reference
            description: Base description
            **kwargs: Type-specific parameters
            
        Returns:
            Generated reference with images
        """
        pass
    
    @abstractmethod
    def _build_generation_prompt(
        self,
        description: str,
        specific_details: Dict[str, Any]
    ) -> str:
        """Build prompt for image generation.
        
        Args:
            description: Base description
            specific_details: Type-specific details for generation
            
        Returns:
            Complete prompt for Gemini
        """
        pass
    
    async def _generate_single_image(
        self,
        prompt: str,
        context_images: Optional[List[Image.Image]] = None
    ) -> bytes:
        """Generate a single image using Gemini.
        
        Args:
            prompt: Generation prompt
            context_images: Optional context images for consistency
            
        Returns:
            Generated image data as bytes
            
        Raises:
            Exception: If generation fails after retries
        """
        for attempt in range(self.config.retry_attempts):
            try:
                logger.info(f"Generating image (attempt {attempt + 1}/{self.config.retry_attempts})")
                logger.debug(f"Prompt: {prompt[:200]}...")
                
                # Call Gemini API
                image_bytes = await self.client.generate_image(
                    prompt=prompt,
                    context_images=context_images,
                    width=self.config.image_width,
                    height=self.config.image_height,
                    quality=self.config.quality
                )
                
                logger.info("Successfully generated image")
                return image_bytes
                
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                if attempt == self.config.retry_attempts - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def _generate_batch_images(
        self,
        prompts: List[str],
        context_images: Optional[List[Image.Image]] = None
    ) -> List[bytes]:
        """Generate multiple images in parallel.
        
        Args:
            prompts: List of generation prompts
            context_images: Optional context images for consistency
            
        Returns:
            List of generated image data
        """
        results = []
        
        # Process in batches to avoid overwhelming the API
        for i in range(0, len(prompts), self.config.batch_size):
            batch = prompts[i:i + self.config.batch_size]
            
            # Generate batch in parallel
            tasks = [
                self._generate_single_image(prompt, context_images)
                for prompt in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle results and errors
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to generate image {i+j}: {result}")
                    # Generate a placeholder or retry
                    results.append(None)
                else:
                    results.append(result)
        
        return results
    
    def _create_consistency_prompt(self, base_description: str) -> str:
        """Create a prompt that emphasizes consistency.
        
        Args:
            base_description: Base description of the reference
            
        Returns:
            Consistency-focused prompt addition
        """
        return f"""
CONSISTENCY REQUIREMENTS:
- Maintain EXACT same visual appearance across all variations
- Keep consistent colors, proportions, and style
- Ensure recognizable as the same {base_description}
- Professional comic book art style
- Clean lines and clear details
"""
    
    def _add_style_context(self, prompt: str, style_guide: Optional[StyleGuide]) -> str:
        """Add style guide context to prompt.
        
        Args:
            prompt: Base prompt
            style_guide: Optional style guide for consistency
            
        Returns:
            Prompt with style context
        """
        if not style_guide:
            return prompt
        
        style_context = f"""
STYLE GUIDE:
- Art Style: {style_guide.art_style}
- Color Palette: {', '.join(style_guide.color_palette) if style_guide.color_palette else 'standard'}
- Line Style: {style_guide.line_style}
- Lighting: {style_guide.lighting_style}
- Mood: {style_guide.color_mood}
"""
        return prompt + style_context
    
    async def save_reference_with_images(
        self,
        reference: BaseReference,
        images: Dict[str, bytes]
    ) -> None:
        """Save reference and its images to storage.
        
        Args:
            reference: Reference to save
            images: Dictionary mapping image keys to image data
        """
        # Determine reference type
        ref_type = reference.__class__.__name__.lower().replace("reference", "")
        if ref_type == "styleguide":
            ref_type = "styleguide"
        
        # Save reference metadata
        self.storage.save_reference(reference)
        
        # Save each image
        for image_key, image_data in images.items():
            if image_data:  # Skip None values (failed generations)
                filename = self.storage.save_reference_image(
                    ref_type,
                    reference.name,
                    image_key,
                    image_data,
                    "png"
                )
                
                # Update reference with filename
                if hasattr(reference, 'images'):
                    reference.images[image_key] = filename
                elif hasattr(reference, 'reference_image'):
                    reference.reference_image = filename
        
        # Re-save reference with updated image filenames
        self.storage.save_reference(reference)
        logger.info(f"Saved {ref_type} reference with {len(images)} images")


class CharacterReferenceGenerator(BaseReferenceGenerator):
    """Generator for character references."""
    
    async def generate_reference(
        self,
        name: str,
        description: str,
        poses: Optional[List[str]] = None,
        expressions: Optional[List[str]] = None,
        outfits: Optional[List[str]] = None,
        style_guide: Optional[StyleGuide] = None,
        **kwargs
    ) -> CharacterReference:
        """Generate character reference with multiple poses and expressions.
        
        Args:
            name: Character name
            description: Character description
            poses: List of poses to generate
            expressions: List of expressions to generate
            outfits: List of outfits to generate
            style_guide: Optional style guide for consistency
            **kwargs: Additional character attributes
            
        Returns:
            Generated character reference with images
        """
        # Default poses and expressions if not provided
        poses = poses or ["standing", "profile", "action"]
        expressions = expressions or ["neutral", "happy", "determined"]
        outfits = outfits or ["default"]
        
        # Create character reference
        character = CharacterReference(
            name=name,
            description=description,
            poses=poses,
            expressions=expressions,
            outfits=outfits,
            **kwargs
        )
        
        # Generate base reference image first for consistency
        base_prompt = self._build_generation_prompt(
            description,
            {
                "pose": "standing",
                "expression": "neutral",
                "type": "character sheet",
                "full_body": True
            }
        )
        
        if style_guide:
            base_prompt = self._add_style_context(base_prompt, style_guide)
        
        base_image_bytes = await self._generate_single_image(base_prompt)
        base_image = Image.open(BytesIO(base_image_bytes))
        
        # Generate variations with base image as context
        prompts = []
        keys = []
        
        for pose in poses:
            for expression in expressions:
                if pose == "standing" and expression == "neutral":
                    continue  # Already generated as base
                
                prompt = self._build_generation_prompt(
                    description,
                    {
                        "pose": pose,
                        "expression": expression,
                        "maintain_exact_appearance": True
                    }
                )
                
                if style_guide:
                    prompt = self._add_style_context(prompt, style_guide)
                
                prompts.append(prompt)
                keys.append(character.get_image_key(pose, expression))
        
        # Generate all variations
        variation_images = await self._generate_batch_images(prompts, [base_image])
        
        # Compile all images
        all_images = {"standing_neutral_default": base_image_bytes}
        for key, image_data in zip(keys, variation_images):
            if image_data:
                all_images[key] = image_data
        
        # Save character with images
        await self.save_reference_with_images(character, all_images)
        
        return character
    
    def _build_generation_prompt(
        self,
        description: str,
        specific_details: Dict[str, Any]
    ) -> str:
        """Build character generation prompt."""
        pose = specific_details.get("pose", "standing")
        expression = specific_details.get("expression", "neutral")
        is_sheet = specific_details.get("type") == "character sheet"
        
        if is_sheet:
            prompt = f"""Generate a character reference sheet for a comic book character.

CHARACTER DESCRIPTION:
{description}

REQUIREMENTS:
- Full body view in a neutral standing pose
- Clear, detailed character design
- Professional comic book art style
- Clean white or simple background
- Front-facing view with all details visible
- Consistent proportions and anatomy
- Include key visual features and costume details

{self._create_consistency_prompt(description)}

OUTPUT: Single character reference sheet image showing the complete character design."""
        else:
            prompt = f"""Generate a comic book character image.

CHARACTER DESCRIPTION:
{description}

POSE: {pose}
EXPRESSION: {expression}

REQUIREMENTS:
- Character in {pose} pose
- Facial expression: {expression}
- Maintain EXACT appearance from reference
- Professional comic book art style
- Clean background
- Clear details and proportions

{self._create_consistency_prompt(description)}

OUTPUT: Single character image in the specified pose and expression."""
        
        return prompt


class LocationReferenceGenerator(BaseReferenceGenerator):
    """Generator for location references."""
    
    async def generate_reference(
        self,
        name: str,
        description: str,
        angles: Optional[List[str]] = None,
        lighting_conditions: Optional[List[str]] = None,
        time_of_day: Optional[List[str]] = None,
        style_guide: Optional[StyleGuide] = None,
        **kwargs
    ) -> LocationReference:
        """Generate location reference with multiple views.
        
        Args:
            name: Location name
            description: Location description
            angles: Camera angles to generate
            lighting_conditions: Lighting variations
            time_of_day: Time variations
            style_guide: Optional style guide
            **kwargs: Additional location attributes
            
        Returns:
            Generated location reference with images
        """
        # Defaults
        angles = angles or ["wide-shot", "medium-shot", "detail"]
        lighting_conditions = lighting_conditions or ["natural"]
        time_of_day = time_of_day or ["day"]
        
        # Create location reference
        location = LocationReference(
            name=name,
            description=description,
            angles=angles,
            lighting_conditions=lighting_conditions,
            time_of_day=time_of_day,
            **kwargs
        )
        
        # Generate establishing shot first
        base_prompt = self._build_generation_prompt(
            description,
            {
                "angle": "wide-shot",
                "type": "establishing",
                "lighting": "natural",
                "time": "day"
            }
        )
        
        if style_guide:
            base_prompt = self._add_style_context(base_prompt, style_guide)
        
        base_image_bytes = await self._generate_single_image(base_prompt)
        base_image = Image.open(BytesIO(base_image_bytes))
        
        # Generate variations
        prompts = []
        keys = []
        
        for angle in angles:
            for lighting in lighting_conditions:
                for time in time_of_day:
                    if angle == "wide-shot" and lighting == "natural" and time == "day":
                        continue  # Already generated
                    
                    prompt = self._build_generation_prompt(
                        description,
                        {
                            "angle": angle,
                            "lighting": lighting,
                            "time": time,
                            "maintain_consistency": True
                        }
                    )
                    
                    if style_guide:
                        prompt = self._add_style_context(prompt, style_guide)
                    
                    prompts.append(prompt)
                    keys.append(location.get_image_key(angle, lighting, time))
        
        # Generate all variations
        variation_images = await self._generate_batch_images(prompts, [base_image])
        
        # Compile all images
        all_images = {"wide-shot_natural_day": base_image_bytes}
        for key, image_data in zip(keys, variation_images):
            if image_data:
                all_images[key] = image_data
        
        # Save location with images
        await self.save_reference_with_images(location, all_images)
        
        return location
    
    def _build_generation_prompt(
        self,
        description: str,
        specific_details: Dict[str, Any]
    ) -> str:
        """Build location generation prompt."""
        angle = specific_details.get("angle", "wide-shot")
        lighting = specific_details.get("lighting", "natural")
        time = specific_details.get("time", "day")
        is_establishing = specific_details.get("type") == "establishing"
        
        if is_establishing:
            prompt = f"""Generate an establishing shot of a location for a comic book.

LOCATION DESCRIPTION:
{description}

REQUIREMENTS:
- Wide establishing shot showing the entire location
- Clear architectural or environmental details
- Professional comic book art style
- Atmospheric and mood-setting
- {time} time setting with {lighting} lighting
- Clear depth and perspective

{self._create_consistency_prompt(description)}

OUTPUT: Single establishing shot image of the location."""
        else:
            prompt = f"""Generate a comic book location image.

LOCATION DESCRIPTION:
{description}

CAMERA ANGLE: {angle}
LIGHTING: {lighting}
TIME OF DAY: {time}

REQUIREMENTS:
- {angle} camera angle
- {lighting} lighting conditions
- {time} time setting
- Maintain consistent location design
- Professional comic book art style
- Clear environmental details

{self._create_consistency_prompt(description)}

OUTPUT: Single location image with specified angle and lighting."""
        
        return prompt


class ObjectReferenceGenerator(BaseReferenceGenerator):
    """Generator for object references."""
    
    async def generate_reference(
        self,
        name: str,
        description: str,
        views: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
        style_guide: Optional[StyleGuide] = None,
        **kwargs
    ) -> ObjectReference:
        """Generate object reference with multiple views and states.
        
        Args:
            name: Object name
            description: Object description
            views: Views to generate
            states: States to generate
            style_guide: Optional style guide
            **kwargs: Additional object attributes
            
        Returns:
            Generated object reference with images
        """
        # Defaults
        views = views or ["front", "three-quarter", "profile"]
        states = states or ["new"]
        
        # Create object reference
        obj = ObjectReference(
            name=name,
            description=description,
            views=views,
            states=states,
            **kwargs
        )
        
        # Generate main reference first
        base_prompt = self._build_generation_prompt(
            description,
            {
                "view": "three-quarter",
                "state": "new",
                "type": "reference"
            }
        )
        
        if style_guide:
            base_prompt = self._add_style_context(base_prompt, style_guide)
        
        base_image_bytes = await self._generate_single_image(base_prompt)
        base_image = Image.open(BytesIO(base_image_bytes))
        
        # Generate variations
        prompts = []
        keys = []
        
        for view in views:
            for state in states:
                if view == "three-quarter" and state == "new":
                    continue  # Already generated
                
                prompt = self._build_generation_prompt(
                    description,
                    {
                        "view": view,
                        "state": state,
                        "maintain_design": True
                    }
                )
                
                if style_guide:
                    prompt = self._add_style_context(prompt, style_guide)
                
                prompts.append(prompt)
                keys.append(obj.get_image_key(view, state))
        
        # Generate all variations
        variation_images = await self._generate_batch_images(prompts, [base_image])
        
        # Compile all images
        all_images = {"three-quarter_new": base_image_bytes}
        for key, image_data in zip(keys, variation_images):
            if image_data:
                all_images[key] = image_data
        
        # Save object with images
        await self.save_reference_with_images(obj, all_images)
        
        return obj
    
    def _build_generation_prompt(
        self,
        description: str,
        specific_details: Dict[str, Any]
    ) -> str:
        """Build object generation prompt."""
        view = specific_details.get("view", "front")
        state = specific_details.get("state", "new")
        is_reference = specific_details.get("type") == "reference"
        
        if is_reference:
            prompt = f"""Generate a reference image of an object for a comic book.

OBJECT DESCRIPTION:
{description}

REQUIREMENTS:
- Clear three-quarter view showing object details
- Professional comic book art style
- Clean, simple background
- Clear details and textures
- Proper proportions and scale
- {state} condition

{self._create_consistency_prompt(description)}

OUTPUT: Single object reference image."""
        else:
            prompt = f"""Generate a comic book object image.

OBJECT DESCRIPTION:
{description}

VIEW: {view}
CONDITION: {state}

REQUIREMENTS:
- {view} view of the object
- Object in {state} condition
- Maintain exact design from reference
- Professional comic book art style
- Clean background
- Clear details and proportions

{self._create_consistency_prompt(description)}

OUTPUT: Single object image in specified view and condition."""
        
        return prompt


class StyleGuideGenerator(BaseReferenceGenerator):
    """Generator for style guides."""
    
    async def generate_reference(
        self,
        name: str,
        description: str,
        art_style: str,
        color_palette: Optional[List[str]] = None,
        sample_content: Optional[str] = None,
        **kwargs
    ) -> StyleGuide:
        """Generate style guide reference image.
        
        Args:
            name: Style guide name
            description: Style description
            art_style: Art style name
            color_palette: Color codes
            sample_content: What to show in the style sample
            **kwargs: Additional style attributes
            
        Returns:
            Generated style guide with reference image
        """
        # Create style guide
        style = StyleGuide(
            name=name,
            description=description,
            art_style=art_style,
            color_palette=color_palette or [],
            **kwargs
        )
        
        # Generate style reference image
        prompt = self._build_generation_prompt(
            description,
            {
                "art_style": art_style,
                "colors": color_palette,
                "sample": sample_content or "character and environment samples"
            }
        )
        
        image_bytes = await self._generate_single_image(prompt)
        
        # Save style guide with image
        await self.save_reference_with_images(
            style,
            {"style_reference": image_bytes}
        )
        
        return style
    
    def _build_generation_prompt(
        self,
        description: str,
        specific_details: Dict[str, Any]
    ) -> str:
        """Build style guide generation prompt."""
        art_style = specific_details.get("art_style", "comic book")
        colors = specific_details.get("colors", [])
        sample = specific_details.get("sample", "style samples")
        
        color_desc = ""
        if colors:
            color_desc = f"- Color palette: {', '.join(colors)}"
        
        prompt = f"""Generate a style guide reference image for comic book art.

STYLE DESCRIPTION:
{description}

ART STYLE: {art_style}
{color_desc}

REQUIREMENTS:
- Show {sample} in the specified art style
- Demonstrate key visual characteristics
- Include example of line work and coloring
- Show lighting and shading approach
- Professional presentation
- Clear style elements

OUTPUT: Single style guide reference image demonstrating the visual style."""
        
        return prompt