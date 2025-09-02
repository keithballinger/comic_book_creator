"""Processing pipeline for comic book generation."""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.models import (
    ComicScript,
    Page,
    Panel,
    GeneratedPanel,
    GeneratedPage,
    ProcessingResult,
    ProcessingOptions,
    ValidationResult,
)
from src.parser import ScriptParser, ScriptValidator
from src.generator.page_generator import PageGenerator
# TextRenderer removed - Gemini handles all text
from src.api import GeminiClient, RateLimiter
from src.config import ConfigLoader
from PIL import Image
from io import BytesIO

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Orchestrates the complete comic generation pipeline."""
    
    def __init__(
        self,
        config: Optional[ConfigLoader] = None,
        page_generator: Optional[PageGenerator] = None,
        output_dir: str = "output"
    ):
        """Initialize processing pipeline.
        
        Args:
            config: Configuration loader
            page_generator: Page generator instance
            output_dir: Output directory for generated comics
        """
        self.config_loader = config or ConfigLoader()
        self.config = self.config_loader.load()  # Load the actual config
        self.page_generator = page_generator
        # TextRenderer removed - Gemini handles all text
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Parser and validator
        self.parser = ScriptParser()
        self.validator = ScriptValidator()
        
        # Processing statistics
        self.stats = {
            'scripts_processed': 0,
            'pages_generated': 0,
            'panels_generated': 0,
            'total_time': 0.0,
            'errors': [],
        }
    
    async def process_script(
        self,
        script_path: str,
        options: Optional[ProcessingOptions] = None
    ) -> ProcessingResult:
        """Process a complete comic script.
        
        Args:
            script_path: Path to the script file
            options: Processing options
            
        Returns:
            Processing result with generated comic
        """
        import time
        start_time = time.time()
        
        options = options or ProcessingOptions()
        
        try:
            # Parse script
            logger.info(f"Parsing script: {script_path}")
            script = self.parser.parse_script(script_path)
            
            # Validate script
            validation_result = self.validator.validate_script(script)
            if not validation_result.is_valid:
                logger.error(f"Script validation failed: {validation_result.get_message()}")
                return ProcessingResult(
                    success=False,
                    script=script,
                    validation_result=validation_result,
                    processing_time=time.time() - start_time
                )
            
            # Log any warnings
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logger.warning(f"Script warning: {warning}")
            
            # Initialize page generator if not provided
            if not self.page_generator:
                await self._initialize_generator(script, options)
            
            # Set up output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"comic_{timestamp}"
            output_path = self.output_dir / output_name
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Process pages with single-pass generation
            generated_pages = []
            previous_page_images = []
            
            for page in script.pages:
                if self._should_process_page(page, options):
                    logger.info(f"Processing page {page.number} with {len(page.panels)} panels")
                    
                    # Generate complete page in single pass
                    page_image_bytes = await self.page_generator.generate_page(
                        page=page,
                        previous_pages=previous_page_images[-2:] if previous_page_images else None,
                        style_context=self._get_style_context(options)
                    )
                    
                    # Convert to PIL Image for context
                    page_image = Image.open(BytesIO(page_image_bytes))
                    previous_page_images.append(page_image)
                    
                    # Create GeneratedPage object
                    generated_page = GeneratedPage(
                        page=page,
                        panels=[],  # No individual panels in single-pass
                        image_data=page_image_bytes,
                        generation_time=0  # Will be tracked by page_generator
                    )
                    generated_pages.append(generated_page)
            
            # Create processing result
            processing_time = time.time() - start_time
            result = ProcessingResult(
                success=True,
                script=script,
                generated_pages=generated_pages,
                validation_result=validation_result,
                processing_time=processing_time,
                metadata={
                    'total_pages': len(generated_pages),
                    'total_panels': sum(len(p.panels) for p in generated_pages),
                    'output_directory': str(self.output_dir),
                }
            )
            
            # Update statistics
            self.stats['scripts_processed'] += 1
            self.stats['pages_generated'] += len(generated_pages)
            self.stats['panels_generated'] += result.metadata['total_panels']
            self.stats['total_time'] += processing_time
            
            logger.info(f"Script processed successfully in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing script: {e}")
            self.stats['errors'].append(str(e))
            
            return ProcessingResult(
                success=False,
                script=script if 'script' in locals() else None,
                processing_time=time.time() - start_time,
                metadata={'error': str(e)}
            )
    
    async def process_page(
        self,
        page: Page,
        previous_pages: Optional[List[GeneratedPage]] = None,
        options: Optional[ProcessingOptions] = None
    ) -> GeneratedPage:
        """Process a single page.
        
        Args:
            page: Page to process
            previous_pages: Previously generated pages
            options: Processing options
            
        Returns:
            Generated page with panels
        """
        options = options or ProcessingOptions()
        
        # Get previous panels for consistency
        previous_panels = []
        if previous_pages:
            for prev_page in previous_pages[-2:]:  # Use last 2 pages for context
                previous_panels.extend(prev_page.panels)
        
        # Generate panels using reference-based approach for better consistency
        # Always use the new reference-based generation method
        generated_panels = await self.panel_generator.generate_page_with_references(
            page,
            previous_panels
        )
        
        # TextRenderer removed - Gemini handles all text
        
        # Create generated page
        generated_page = GeneratedPage(
            page=page,
            panels=generated_panels,
            generation_time=sum(p.generation_time for p in generated_panels)
        )
        
        return generated_page
    
    async def process_panel(
        self,
        panel: Panel,
        page: Optional[Page] = None,
        previous_panels: Optional[List[GeneratedPanel]] = None,
        options: Optional[ProcessingOptions] = None
    ) -> GeneratedPanel:
        """Process a single panel.
        
        Args:
            panel: Panel to process
            page: Page containing the panel
            previous_panels: Previously generated panels
            options: Processing options
            
        Returns:
            Generated panel
        """
        options = options or ProcessingOptions()
        
        # Generate panel image
        generated_panel = await self.panel_generator.generate_panel(
            panel,
            page,
            previous_panels,
        )
        
        # TextRenderer removed - Gemini handles all text
        
        return generated_panel
    
    def _get_style_context(self, options: ProcessingOptions) -> Optional[Dict]:
        """Get style context for page generation.
        
        Args:
            options: Processing options
            
        Returns:
            Style configuration dictionary or None
        """
        if options.style_preset:
            # Return style configuration based on preset
            # This could be expanded to load actual style configs
            return {
                'style': options.style_preset,
                'quality': options.quality
            }
        return None
    
    async def _initialize_generator(
        self,
        script: ComicScript,
        options: ProcessingOptions
    ):
        """Initialize page generator with configuration.
        
        Args:
            script: Comic script
            options: Processing options
        """
        # Create Gemini client
        client = GeminiClient(api_key=self.config.api_key)
        
        # Create page generator (much simpler than panel generator)
        self.page_generator = PageGenerator(gemini_client=client)
    
    # TextRenderer methods removed - Gemini handles all text
    
    def _extract_characters(self, script: ComicScript) -> List[str]:
        """Extract unique characters from script.
        
        Args:
            script: Comic script
            
        Returns:
            List of unique character names
        """
        characters = set()
        
        for page in script.pages:
            for panel in page.panels:
                characters.update(panel.characters)
        
        return sorted(list(characters))
    
    def _should_process_page(
        self,
        page: Page,
        options: ProcessingOptions
    ) -> bool:
        """Check if page should be processed based on options.
        
        Args:
            page: Page to check
            options: Processing options
            
        Returns:
            True if page should be processed
        """
        if options.page_range:
            start, end = options.page_range
            return start <= page.number <= end
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()
        
        # Calculate averages
        if stats['scripts_processed'] > 0:
            stats['avg_processing_time'] = stats['total_time'] / stats['scripts_processed']
            stats['avg_pages_per_script'] = stats['pages_generated'] / stats['scripts_processed']
            stats['avg_panels_per_page'] = (
                stats['panels_generated'] / stats['pages_generated']
                if stats['pages_generated'] > 0 else 0
            )
        else:
            stats['avg_processing_time'] = 0
            stats['avg_pages_per_script'] = 0
            stats['avg_panels_per_page'] = 0
        
        return stats
    
    def reset_statistics(self):
        """Reset processing statistics."""
        self.stats = {
            'scripts_processed': 0,
            'pages_generated': 0,
            'panels_generated': 0,
            'total_time': 0.0,
            'errors': [],
        }
    
    async def save_results(
        self,
        result: ProcessingResult,
        output_name: Optional[str] = None
    ) -> Path:
        """Save processing results to disk.
        
        Args:
            result: Processing result
            output_name: Optional output name
            
        Returns:
            Path to output directory
        """
        from PIL import Image
        import io
        import json
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_name = output_name or f"comic_{timestamp}"
        output_path = self.output_dir / output_name
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata = {
            'script_title': result.script.title if result.script else 'Unknown',
            'processing_time': result.processing_time,
            'total_pages': len(result.generated_pages) if result.generated_pages else 0,
            'timestamp': timestamp,
            'success': result.success,
        }
        
        with open(output_path / 'metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save pages
        if result.generated_pages:
            for page_idx, gen_page in enumerate(result.generated_pages, 1):
                # For single-pass generation, we have the complete page image
                if gen_page.image_data:
                    page_path = output_path / f"page_{page_idx:03d}_complete.png"
                    try:
                        image = Image.open(io.BytesIO(gen_page.image_data))
                        image.save(page_path)
                        logger.info(f"Saved page {page_idx} to {page_path}")
                    except Exception as e:
                        logger.error(f"Error saving page: {e}")
                
                # Legacy: Handle multi-panel pages if they exist
                elif gen_page.panels:
                    from src.output import PageCompositor
                    compositor = PageCompositor(
                        page_width=self.config.output.page_size[0],
                        page_height=self.config.output.page_size[1],
                        dpi=self.config.output.dpi,
                        layout_style='standard'
                    )
                    
                    try:
                        page_image = compositor.compose_page(
                            gen_page.panels,
                            gen_page.page
                        )
                        page_path = output_path / f"page_{page_idx:03d}_complete.png"
                        page_image.save(page_path)
                        logger.info(f"Saved composed page to {page_path}")
                    except Exception as e:
                        logger.error(f"Error composing page: {e}")
            
            # Generate complete comic book file if requested
            if 'pdf' in self.config.output.formats:
                self._generate_pdf(output_path, result)
            if 'cbz' in self.config.output.formats:
                self._generate_cbz(output_path, result)
        
        logger.info(f"Results saved to {output_path}")
        return output_path
    
    def _generate_pdf(self, output_path: Path, result: ProcessingResult):
        """Generate PDF file from composed pages."""
        try:
            from PIL import Image
            import img2pdf
            
            # Collect all composed page files
            page_files = sorted(output_path.glob("page_*_complete.png"))
            
            if page_files:
                pdf_path = output_path / f"{result.script.title or 'comic'}.pdf"
                
                # Convert to PDF
                with open(pdf_path, "wb") as f:
                    f.write(img2pdf.convert([str(p) for p in page_files]))
                
                logger.info(f"Generated PDF: {pdf_path}")
        except ImportError:
            logger.warning("img2pdf not installed. Skipping PDF generation.")
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
    
    def _generate_cbz(self, output_path: Path, result: ProcessingResult):
        """Generate CBZ (Comic Book Zip) file."""
        try:
            import zipfile
            
            # Collect all composed page files
            page_files = sorted(output_path.glob("page_*_complete.png"))
            
            if page_files:
                cbz_path = output_path / f"{result.script.title or 'comic'}.cbz"
                
                with zipfile.ZipFile(cbz_path, 'w', zipfile.ZIP_DEFLATED) as cbz:
                    for i, page_file in enumerate(page_files, 1):
                        cbz.write(page_file, f"page_{i:03d}.png")
                
                logger.info(f"Generated CBZ: {cbz_path}")
        except Exception as e:
            logger.error(f"Error generating CBZ: {e}")