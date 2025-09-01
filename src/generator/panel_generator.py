"""Panel generator for creating comic book panels."""

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

from src.api import GeminiClient, RateLimiter
from src.generator.consistency import ConsistencyManager
from src.models import (
    GeneratedPanel,
    Panel,
    Page,
    CharacterReference,
    StyleConfig,
)
from src.processor.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class PanelGenerator:
    """Orchestrates panel image generation with consistency and caching."""
    
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        consistency_manager: Optional[ConsistencyManager] = None,
        cache_manager: Optional[CacheManager] = None,
        rate_limiter: Optional[RateLimiter] = None
    ):
        """Initialize panel generator.
        
        Args:
            gemini_client: Gemini API client
            consistency_manager: Consistency manager
            cache_manager: Cache manager for storing results
            rate_limiter: Rate limiter for API calls
        """
        self.client = gemini_client or GeminiClient()
        self.consistency_manager = consistency_manager or ConsistencyManager()
        self.cache = cache_manager or CacheManager()
        self.rate_limiter = rate_limiter or RateLimiter(calls_per_minute=30)
        
        # Track generation statistics
        self.stats = {
            'panels_generated': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'total_time': 0.0,
            'errors': 0,
        }
        
    async def generate_panel(
        self,
        panel: Panel,
        page_context: Optional[Page] = None,
        previous_panels: Optional[List[GeneratedPanel]] = None,
        skip_cache: bool = False
    ) -> GeneratedPanel:
        """Generate a single panel with consistency.
        
        Args:
            panel: Panel to generate
            page_context: Page containing the panel
            previous_panels: Previously generated panels
            skip_cache: Skip cache lookup
            
        Returns:
            Generated panel with image data
        """
        import time
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(panel)
            
            # Check cache first unless skipped
            if not skip_cache:
                cached = await self.cache.get(cache_key)
                if cached:
                    logger.info(f"Cache hit for panel {panel.number}")
                    self.stats['cache_hits'] += 1
                    
                    # Deserialize cached panel
                    return self._deserialize_panel(cached)
            
            # Enhance description with context
            enhanced_desc = await self._enhance_description(panel)
            
            # Build consistent prompt
            prompt = self.consistency_manager.build_consistent_prompt(
                enhanced_desc,
                previous_panels
            )
            
            # Get reference images for consistency
            ref_images = self.consistency_manager.get_reference_images(
                previous_panels,
                panel.characters
            )
            
            # Get style configuration
            style_config = self._get_style_config()
            
            # Generate image with rate limiting
            logger.info(f"Generating panel {panel.number}")
            image_data = await self.rate_limiter.execute_with_retry(
                self.client.generate_panel_image,
                prompt,
                ref_images,
                style_config
            )
            
            self.stats['api_calls'] += 1
            
            # Create generated panel
            generation_time = time.time() - start_time
            generated_panel = GeneratedPanel(
                panel=panel,
                image_data=image_data,
                generation_time=generation_time,
                metadata={
                    'prompt': prompt,
                    'enhanced_description': enhanced_desc,
                    'style_hash': self.consistency_manager.get_style_hash(),
                    'cache_key': cache_key,
                }
            )
            
            # Register with consistency manager
            self.consistency_manager.register_panel(generated_panel)
            
            # Cache the result
            await self.cache.set(cache_key, self._serialize_panel(generated_panel))
            
            # Update statistics
            self.stats['panels_generated'] += 1
            self.stats['total_time'] += generation_time
            
            logger.info(f"Panel {panel.number} generated in {generation_time:.2f}s")
            
            return generated_panel
            
        except Exception as e:
            logger.error(f"Error generating panel {panel.number}: {e}")
            self.stats['errors'] += 1
            
            # Return a placeholder panel on error
            return GeneratedPanel(
                panel=panel,
                image_data=b"",  # Empty image data
                generation_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    async def generate_page_panels(
        self,
        page: Page,
        previous_pages: Optional[List[GeneratedPanel]] = None,
        parallel: bool = False
    ) -> List[GeneratedPanel]:
        """Generate all panels for a page.
        
        Args:
            page: Page containing panels
            previous_pages: Previously generated panels from other pages
            parallel: Generate panels in parallel (may affect consistency)
            
        Returns:
            List of generated panels
        """
        generated_panels = []
        previous_panels = list(previous_pages) if previous_pages else []
        
        if parallel:
            # Generate panels in parallel (faster but may affect consistency)
            tasks = []
            for panel in page.panels:
                task = self.generate_panel(
                    panel,
                    page,
                    previous_panels.copy()
                )
                tasks.append(task)
            
            generated_panels = await asyncio.gather(*tasks)
            
        else:
            # Generate panels sequentially (better consistency)
            for panel in page.panels:
                generated = await self.generate_panel(
                    panel,
                    page,
                    previous_panels
                )
                generated_panels.append(generated)
                
                # Add to previous panels for next iteration
                previous_panels.append(generated)
        
        return generated_panels
    
    async def initialize_characters(
        self,
        character_names: List[str],
        descriptions: Optional[Dict[str, str]] = None
    ):
        """Initialize character references for consistency.
        
        Args:
            character_names: List of character names
            descriptions: Optional descriptions for characters
        """
        for char_name in character_names:
            # Use provided description or generate one
            description = descriptions.get(char_name, f"Character named {char_name}") if descriptions else f"Character named {char_name}"
            
            # Generate character reference
            char_ref = await self.client.generate_character_reference(
                char_name,
                description
            )
            
            # Register with consistency manager
            self.consistency_manager.register_character(char_ref)
            
            logger.info(f"Initialized character: {char_name}")
    
    def set_style(self, style_config: StyleConfig):
        """Set the style configuration.
        
        Args:
            style_config: Style configuration to use
        """
        self.consistency_manager.load_style(style_config)
        logger.info(f"Style set to: {style_config.name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get generation statistics.
        
        Returns:
            Dictionary of statistics
        """
        stats = self.stats.copy()
        
        # Calculate averages
        if stats['panels_generated'] > 0:
            stats['avg_generation_time'] = stats['total_time'] / stats['panels_generated']
            stats['cache_hit_rate'] = stats['cache_hits'] / (stats['panels_generated'] + stats['cache_hits'])
        else:
            stats['avg_generation_time'] = 0
            stats['cache_hit_rate'] = 0
        
        return stats
    
    def reset_statistics(self):
        """Reset generation statistics."""
        self.stats = {
            'panels_generated': 0,
            'cache_hits': 0,
            'api_calls': 0,
            'total_time': 0.0,
            'errors': 0,
        }
    
    async def _enhance_description(self, panel: Panel) -> str:
        """Enhance panel description using AI.
        
        Args:
            panel: Panel to enhance
            
        Returns:
            Enhanced description
        """
        try:
            # Get character references for context
            char_refs = {}
            for char_name in panel.characters:
                if char_ref := self.consistency_manager.character_refs.get(char_name):
                    char_refs[char_name] = char_ref
            
            # Enhance description
            enhanced = await self.client.enhance_panel_description(panel, char_refs)
            return enhanced
            
        except Exception as e:
            logger.warning(f"Failed to enhance description: {e}")
            return panel.description
    
    def _generate_cache_key(self, panel: Panel) -> str:
        """Generate cache key for panel.
        
        Args:
            panel: Panel to generate key for
            
        Returns:
            Cache key string
        """
        # Include panel details and style in cache key
        key_data = {
            'panel_number': panel.number,
            'description': panel.description,
            'dialogue': [d.text for d in panel.dialogue],
            'captions': [c.text for c in panel.captions],
            'style_hash': self.consistency_manager.get_style_hash(),
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    def _get_style_config(self) -> Optional[Dict[str, Any]]:
        """Get style configuration dictionary.
        
        Returns:
            Style configuration or None
        """
        if style := self.consistency_manager.style_config:
            return {
                'art_style': style.art_style,
                'color_palette': style.color_palette,
                'line_weight': style.line_weight,
                'shading': style.shading,
                **style.custom_prompts
            }
        return None
    
    def _serialize_panel(self, panel: GeneratedPanel) -> Dict[str, Any]:
        """Serialize panel for caching.
        
        Args:
            panel: Panel to serialize
            
        Returns:
            Serialized panel data
        """
        return {
            'panel_number': panel.panel.number if panel.panel else 0,
            'image_data': panel.image_data.hex() if panel.image_data else "",
            'generation_time': panel.generation_time,
            'metadata': panel.metadata,
        }
    
    def _deserialize_panel(self, data: Dict[str, Any]) -> GeneratedPanel:
        """Deserialize panel from cache.
        
        Args:
            data: Serialized panel data
            
        Returns:
            Deserialized panel
        """
        # Note: We lose the original Panel object in serialization
        # This is acceptable for cache hits as we mainly need the image
        return GeneratedPanel(
            panel=None,  # Panel reference lost in serialization
            image_data=bytes.fromhex(data['image_data']) if data.get('image_data') else b"",
            generation_time=data.get('generation_time', 0),
            metadata=data.get('metadata', {})
        )