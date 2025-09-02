"""Panel generator for creating comic book panels."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.api import GeminiClient, RateLimiter
from src.generator.consistency import ConsistencyManager
from src.generator.reference_builder import ReferenceSheetBuilder
from src.references.manager import ReferenceManager
from PIL import Image
import io
from src.models import (
    GeneratedPanel,
    Panel,
    Page,
    CharacterReference,
    StyleConfig,
)

logger = logging.getLogger(__name__)


class PanelGenerator:
    """Orchestrates panel image generation with consistency and caching."""
    
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        consistency_manager: Optional[ConsistencyManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        reference_manager: Optional[ReferenceManager] = None
    ):
        """Initialize panel generator.
        
        Args:
            gemini_client: Gemini API client
            consistency_manager: Consistency manager
            rate_limiter: Rate limiter for API calls
            reference_manager: Reference manager for character/location consistency
        """
        self.client = gemini_client or GeminiClient()
        self.consistency_manager = consistency_manager or ConsistencyManager()
        self.rate_limiter = rate_limiter or RateLimiter(calls_per_minute=30)
        self.reference_builder = ReferenceSheetBuilder()
        self.reference_manager = reference_manager  # May be None if not using references
        self.debug_output_dir = None  # Will be set per session
        
        # Track generation statistics
        self.stats = {
            'panels_generated': 0,
                        'api_calls': 0,
            'total_time': 0.0,
            'errors': 0,
        }
        
    async def generate_panel(
        self,
        panel: Panel,
        page_context: Optional[Page] = None,
        previous_panels: Optional[List[GeneratedPanel]] = None,
    ) -> GeneratedPanel:
        """Generate a single panel with consistency.
        
        Args:
            panel: Panel to generate
            page_context: Page containing the panel
            previous_panels: Previously generated panels
        Returns:
            Generated panel with image data
        """
        import time
        start_time = time.time()
        
        try:
            # No caching - removed
            
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
                }
            )
            
            # Register with consistency manager
            self.consistency_manager.register_panel(generated_panel)
            
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
    
    def set_debug_output_dir(self, debug_dir: str):
        """Set the debug output directory for this session.
        
        Args:
            debug_dir: Directory to save debug output
        """
        from pathlib import Path
        self.debug_output_dir = Path(debug_dir) if debug_dir else None
        if self.debug_output_dir:
            self.debug_output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Debug output enabled: {self.debug_output_dir}")
    
    async def generate_page_with_references(
        self,
        page: Page,
        previous_pages: Optional[List[GeneratedPanel]] = None
    ) -> List[GeneratedPanel]:
        """Generate a page using progressive reference sheets.
        
        This method builds the page incrementally, using a comprehensive
        reference sheet that includes the page-in-progress and all character/location
        references to maintain consistency.
        
        Args:
            page: Page containing panels
            previous_pages: Previously generated panels from other pages
            
        Returns:
            List of generated panels
        """
        generated_panels = []
        page_canvas = Image.new('RGB', (2400, 3600), 'white')
        
        # Extract initial references from previous pages
        if previous_pages:
            for prev_panel in previous_pages[-6:]:  # Use last 6 panels as references
                if prev_panel.image_data:
                    try:
                        img = Image.open(io.BytesIO(prev_panel.image_data))
                        panel_metadata = {
                            'characters': prev_panel.panel.characters if prev_panel.panel else [],
                            'panel_number': prev_panel.panel.number if prev_panel.panel else 0
                        }
                        self.reference_builder.extract_references_from_panel(img, panel_metadata)
                    except Exception as e:
                        logger.warning(f"Could not extract references: {e}")
        
        # Generate each panel with progressive context
        for i, panel in enumerate(page.panels):
            logger.info(f"Generating panel {i+1}/{len(page.panels)} with reference sheet")
            
            # Calculate panel position
            panel_position = self.reference_builder.calculate_panel_position(i, len(page.panels))
            
            # Create comprehensive reference sheet
            reference_sheet = self.reference_builder.create_comprehensive_reference(
                page_in_progress=page_canvas,
                target_panel_position=panel_position,
                panel_number=i + 1,
                total_panels=len(page.panels)
            )
            
            # Build prompt for this specific panel
            # Calculate exact panel dimensions
            panel_width = panel_position[2] - panel_position[0]
            panel_height = panel_position[3] - panel_position[1]
            
            prompt = f"""
            CRITICAL: Generate EXACTLY ONE SINGLE PANEL IMAGE.
            
            EXACT DIMENSIONS REQUIRED: {panel_width}x{panel_height} pixels
            This is panel {i+1} of {len(page.panels)} for this page.
            
            PANEL CONTENT TO ILLUSTRATE:
            {getattr(panel, 'raw_text', panel.description)}
            
            STRICT REQUIREMENTS:
            1. Generate EXACTLY ONE rectangular panel image of EXACTLY {panel_width}x{panel_height} pixels
            2. DO NOT create multiple panels or subdivide the image
            3. ALL text elements (captions, speech bubbles, thought bubbles) MUST be INSIDE the panel boundaries
            4. Captions should be rectangular boxes at the top or bottom INSIDE the panel
            5. Speech bubbles should be INSIDE the panel area, not extending beyond edges
            6. This is a SINGLE SCENE/MOMENT in time
            7. Fill the ENTIRE {panel_width}x{panel_height} area with the illustration
            8. The artwork should extend to the edges - no white borders
            
            The reference image shows the page layout and style to match.
            The RED RECTANGLE shows where this single panel will be placed.
            
            OUTPUT: One complete rectangular comic panel of EXACTLY {panel_width}x{panel_height} pixels with ALL text elements contained within.
            """
            
            # Save debug files if debug directory specified
            if self.debug_output_dir:
                # Save the reference sheet
                ref_sheet_path = self.debug_output_dir / f"page_{page.number}_panel_{i+1}_reference_sheet.png"
                ref_sheet_img = Image.open(io.BytesIO(reference_sheet))
                ref_sheet_img.save(ref_sheet_path)
                logger.debug(f"Saved reference sheet to {ref_sheet_path}")
                
                # Save the prompt
                prompt_path = self.debug_output_dir / f"page_{page.number}_panel_{i+1}_prompt.txt"
                with open(prompt_path, 'w') as f:
                    f.write(prompt)
                logger.debug(f"Saved prompt to {prompt_path}")
                
                # Save the page state before this panel
                page_state_path = self.debug_output_dir / f"page_{page.number}_panel_{i+1}_page_before.png"
                page_canvas.save(page_state_path)
                logger.debug(f"Saved page state to {page_state_path}")
            
            try:
                # Generate panel with reference sheet
                panel_image_data = await self.rate_limiter.execute_with_retry(
                    self.client.generate_panel_image,
                    prompt,
                    [reference_sheet],  # Use reference sheet as context
                    self._get_style_config()
                )
                
                # Convert generated panel to image
                panel_img = Image.open(io.BytesIO(panel_image_data))
                
                # Ensure exact dimensions without distortion
                target_width = panel_position[2] - panel_position[0]
                target_height = panel_position[3] - panel_position[1]
                
                # If the image isn't exactly the right size, resize to fit while maintaining aspect ratio,
                # then crop or pad to exact dimensions
                if panel_img.size != (target_width, target_height):
                    # Calculate scale to fit
                    scale_x = target_width / panel_img.width
                    scale_y = target_height / panel_img.height
                    scale = max(scale_x, scale_y)  # Use max to ensure we cover the full area
                    
                    # Resize maintaining aspect ratio
                    new_width = int(panel_img.width * scale)
                    new_height = int(panel_img.height * scale)
                    panel_img = panel_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    
                    # Crop to exact size (center crop)
                    if new_width > target_width or new_height > target_height:
                        left = (new_width - target_width) // 2
                        top = (new_height - target_height) // 2
                        panel_img = panel_img.crop((left, top, left + target_width, top + target_height))
                    
                    # Pad if needed (shouldn't happen with max scale)
                    if panel_img.size != (target_width, target_height):
                        padded = Image.new('RGB', (target_width, target_height), 'white')
                        x = (target_width - panel_img.width) // 2
                        y = (target_height - panel_img.height) // 2
                        padded.paste(panel_img, (x, y))
                        panel_img = padded
                
                # Add panel to page canvas
                page_canvas.paste(panel_img, (panel_position[0], panel_position[1]))
                
                # Save debug output if specified
                if self.debug_output_dir:
                    # Save the generated panel
                    panel_path = self.debug_output_dir / f"page_{page.number}_panel_{i+1}_generated.png"
                    panel_img.save(panel_path)
                    logger.debug(f"Saved generated panel to {panel_path}")
                    
                    # Save the page state after adding this panel
                    page_after_path = self.debug_output_dir / f"page_{page.number}_panel_{i+1}_page_after.png"
                    page_canvas.save(page_after_path)
                    logger.debug(f"Saved page state after panel to {page_after_path}")
                
                # Update reference builder with new panel
                self.reference_builder.update_page_state(page_canvas)
                
                # Extract any new references from this panel
                panel_metadata = {
                    'characters': panel.characters if panel.characters else [],
                    'panel_number': panel.number,
                    'location': getattr(panel, 'location', None)
                }
                self.reference_builder.extract_references_from_panel(panel_img, panel_metadata)
                
                # Create GeneratedPanel object
                generated_panel = GeneratedPanel(
                    panel=panel,
                    image_data=panel_image_data,
                    generation_time=0,  # We'd track this properly
                    metadata={
                        'prompt': prompt,
                        'used_reference_sheet': True,
                        'panel_position': panel_position
                    }
                )
                
                generated_panels.append(generated_panel)
                
                # Register with consistency manager
                self.consistency_manager.register_panel(generated_panel)
                
                logger.info(f"Successfully generated panel {i+1}")
                
            except Exception as e:
                logger.error(f"Error generating panel {i+1}: {e}")
                # Add placeholder panel on error
                generated_panels.append(GeneratedPanel(
                    panel=panel,
                    image_data=b"",
                    generation_time=0,
                    metadata={'error': str(e)}
                ))
        
        return generated_panels
    
    def _extract_references_from_text(self, text: str) -> Dict[str, List[str]]:
        """Extract reference names from panel text.
        
        Args:
            text: Panel description or dialogue text
            
        Returns:
            Dictionary of reference types to names found
        """
        if not self.reference_manager:
            return {}
        
        # Use reference manager to find references in text
        return self.reference_manager.find_references_in_text(text)
    
    def _get_reference_images(
        self,
        panel: Panel,
        characters: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        objects: Optional[List[str]] = None
    ) -> List[Image.Image]:
        """Get reference images for the panel.
        
        Args:
            panel: Panel being generated
            characters: Character names to include
            locations: Location names to include
            objects: Object names to include
            
        Returns:
            List of PIL Images to use as references
        """
        if not self.reference_manager:
            return []
        
        reference_images = []
        
        # Get character images
        if characters:
            char_images = self.reference_manager.get_character_images(characters)
            for char_name, images in char_images.items():
                for key, image_data in images.items():
                    try:
                        img = Image.open(io.BytesIO(image_data))
                        reference_images.append(img)
                    except Exception as e:
                        logger.warning(f"Could not load reference image for {char_name}/{key}: {e}")
        
        # Get location images
        if locations:
            for loc_name in locations:
                loc = self.reference_manager.get_reference("location", loc_name)
                if loc and hasattr(loc, 'images'):
                    for key, filename in loc.images.items():
                        try:
                            image_data = self.reference_manager.storage.load_reference_image(
                                "location", loc_name, filename
                            )
                            img = Image.open(io.BytesIO(image_data))
                            reference_images.append(img)
                        except Exception as e:
                            logger.warning(f"Could not load location image {loc_name}/{key}: {e}")
        
        # Get object images
        if objects:
            for obj_name in objects:
                obj = self.reference_manager.get_reference("object", obj_name)
                if obj and hasattr(obj, 'images'):
                    for key, filename in obj.images.items():
                        try:
                            image_data = self.reference_manager.storage.load_reference_image(
                                "object", obj_name, filename
                            )
                            img = Image.open(io.BytesIO(image_data))
                            reference_images.append(img)
                        except Exception as e:
                            logger.warning(f"Could not load object image {obj_name}/{key}: {e}")
        
        return reference_images
    
    async def generate_panel_with_references(
        self,
        panel: Panel,
        page_context: Optional[Page] = None,
        previous_panels: Optional[List[GeneratedPanel]] = None,
    ) -> GeneratedPanel:
        """Generate a panel using reference images from the reference manager.
        
        Args:
            panel: Panel to generate
            page_context: Page containing the panel
            previous_panels: Previously generated panels
            
        Returns:
            Generated panel with image data
        """
        import time
        start_time = time.time()
        
        try:
            # Extract references from panel text
            panel_text = getattr(panel, 'raw_text', panel.description)
            found_refs = self._extract_references_from_text(panel_text)
            
            # Get reference images
            ref_images = self._get_reference_images(
                panel,
                characters=found_refs.get('character', []),
                locations=found_refs.get('location', []),
                objects=found_refs.get('object', [])
            )
            
            # Get style guide if available
            style_guide = None
            if self.reference_manager:
                style_guides = self.reference_manager.list_references('styleguide')
                if style_guides.get('styleguide'):
                    # Use first style guide found
                    style_name = style_guides['styleguide'][0]
                    style_guide = self.reference_manager.get_reference('styleguide', style_name)
            
            # Build enhanced prompt with references
            enhanced_desc = await self._enhance_description(panel)
            
            # Add reference context to prompt
            if found_refs:
                enhanced_desc += "\n\nREFERENCE CONTEXT:"
                if found_refs.get('character'):
                    enhanced_desc += f"\nCharacters: {', '.join(found_refs['character'])}"
                if found_refs.get('location'):
                    enhanced_desc += f"\nLocations: {', '.join(found_refs['location'])}"
                if found_refs.get('object'):
                    enhanced_desc += f"\nObjects: {', '.join(found_refs['object'])}"
            
            if style_guide:
                enhanced_desc += f"\n\nSTYLE: {style_guide.art_style}"
                if style_guide.color_palette:
                    enhanced_desc += f"\nColors: {', '.join(style_guide.color_palette)}"
            
            # Build consistent prompt
            prompt = self.consistency_manager.build_consistent_prompt(
                enhanced_desc,
                previous_panels
            )
            
            # Combine reference images with consistency images
            consistency_images = self.consistency_manager.get_reference_images(
                previous_panels,
                panel.characters
            )
            
            all_ref_images = ref_images + consistency_images
            
            # Get style configuration
            style_config = self._get_style_config()
            
            # Generate image with rate limiting
            logger.info(f"Generating panel {panel.number} with {len(ref_images)} reference images")
            image_data = await self.rate_limiter.execute_with_retry(
                self.client.generate_panel_image,
                prompt,
                all_ref_images,
                style_config
            )
            
            # Update statistics
            self.stats['panels_generated'] += 1
            self.stats['api_calls'] += 1
            self.stats['total_time'] += time.time() - start_time
            
            # Create GeneratedPanel object
            generated_panel = GeneratedPanel(
                panel=panel,
                image_data=image_data,
                generation_time=time.time() - start_time,
                metadata={
                    'prompt': prompt,
                    'used_references': bool(ref_images),
                    'reference_count': len(ref_images),
                    'found_references': found_refs
                }
            )
            
            # Register with consistency manager
            self.consistency_manager.register_panel(generated_panel)
            
            logger.info(f"Successfully generated panel {panel.number}")
            return generated_panel
            
        except Exception as e:
            logger.error(f"Error generating panel {panel.number}: {e}")
            self.stats['errors'] += 1
            # Return error panel
            return GeneratedPanel(
                panel=panel,
                image_data=b"",
                generation_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
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
        else:
            stats['avg_generation_time'] = 0
        
        return stats
    
    def reset_statistics(self):
        """Reset generation statistics."""
        self.stats = {
            'panels_generated': 0,
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
    
