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
from src.generator import PanelGenerator
from src.output import TextRenderer
from src.api import GeminiClient, RateLimiter
from src.config import ConfigLoader

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Orchestrates the complete comic generation pipeline."""
    
    def __init__(
        self,
        config: Optional[ConfigLoader] = None,
        panel_generator: Optional[PanelGenerator] = None,
        text_renderer: Optional[TextRenderer] = None,
        output_dir: str = "output"
    ):
        """Initialize processing pipeline.
        
        Args:
            config: Configuration loader
            panel_generator: Panel generator instance
            text_renderer: Text renderer instance
            output_dir: Output directory for generated comics
        """
        self.config_loader = config or ConfigLoader()
        self.config = self.config_loader.load()  # Load the actual config
        self.panel_generator = panel_generator
        self.text_renderer = text_renderer or TextRenderer()
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
            
            # Initialize panel generator if not provided
            if not self.panel_generator:
                await self._initialize_generator(script, options)
            
            # Set up debug output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"comic_{timestamp}"
            output_path = self.output_dir / output_name
            debug_dir = output_path / "debug"
            self.panel_generator.set_debug_output_dir(str(debug_dir))
            
            # Extract and initialize characters
            characters = self._extract_characters(script)
            if characters:
                logger.info(f"Initializing {len(characters)} characters")
                await self.panel_generator.initialize_characters(characters)
            
            # Process pages
            generated_pages = []
            for page in script.pages:
                if self._should_process_page(page, options):
                    logger.info(f"Processing page {page.number}")
                    generated_page = await self.process_page(
                        page,
                        previous_pages=generated_pages,
                        options=options
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
        
        # Apply text rendering if enabled
        if options.render_text:
            generated_panels = await self._render_text_on_panels(
                generated_panels,
                options
            )
        
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
        
        # Apply text rendering if enabled
        if options.render_text and generated_panel.image_data:
            generated_panel = await self._render_text_on_panel(
                generated_panel,
                options
            )
        
        return generated_panel
    
    async def _initialize_generator(
        self,
        script: ComicScript,
        options: ProcessingOptions
    ):
        """Initialize panel generator with configuration.
        
        Args:
            script: Comic script
            options: Processing options
        """
        from src.generator import ConsistencyManager
        
        # Create components
        client = GeminiClient(api_key=self.config.api_key)
        consistency_manager = ConsistencyManager()
        rate_limiter = RateLimiter(
            calls_per_minute=self.config.max_concurrent_requests * 10  # Approximate rate limit
        )
        
        # Create panel generator
        self.panel_generator = PanelGenerator(
            gemini_client=client,
            consistency_manager=consistency_manager,
            rate_limiter=rate_limiter
        )
        
        # Set style if configured
        if style_name := options.style_preset:
            # For now, just use the style name - we can expand this later
            # to load actual style configurations
            pass
    
    async def _render_text_on_panels(
        self,
        panels: List[GeneratedPanel],
        options: ProcessingOptions
    ) -> List[GeneratedPanel]:
        """Render text on generated panels.
        
        Args:
            panels: Generated panels
            options: Processing options
            
        Returns:
            Panels with rendered text
        """
        from PIL import Image
        import io
        
        rendered_panels = []
        
        for gen_panel in panels:
            if gen_panel.image_data and gen_panel.panel:
                try:
                    # Convert image data to PIL Image
                    image = Image.open(io.BytesIO(gen_panel.image_data))
                    
                    # Render text
                    rendered_image = self.text_renderer.render_panel_text(
                        image,
                        gen_panel.panel
                    )
                    
                    # Convert back to bytes
                    output_buffer = io.BytesIO()
                    rendered_image.save(output_buffer, format='PNG')
                    gen_panel.image_data = output_buffer.getvalue()
                    
                except Exception as e:
                    logger.error(f"Error rendering text on panel: {e}")
            
            rendered_panels.append(gen_panel)
        
        return rendered_panels
    
    async def _render_text_on_panel(
        self,
        panel: GeneratedPanel,
        options: ProcessingOptions
    ) -> GeneratedPanel:
        """Render text on a single panel.
        
        Args:
            panel: Generated panel
            options: Processing options
            
        Returns:
            Panel with rendered text
        """
        return (await self._render_text_on_panels([panel], options))[0]
    
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
        
        # Save pages and panels
        if result.generated_pages:
            # Initialize compositor for page layout
            from src.output import PageCompositor
            compositor = PageCompositor(
                page_width=self.config.output.page_size[0],
                page_height=self.config.output.page_size[1],
                dpi=self.config.output.dpi,
                layout_style='standard'
            )
            
            for page_idx, gen_page in enumerate(result.generated_pages, 1):
                page_dir = output_path / f"page_{page_idx:03d}"
                page_dir.mkdir(exist_ok=True)
                
                # Save individual panels
                for panel_idx, gen_panel in enumerate(gen_page.panels, 1):
                    if gen_panel.image_data:
                        # Save panel image
                        panel_path = page_dir / f"panel_{panel_idx:03d}.png"
                        
                        try:
                            image = Image.open(io.BytesIO(gen_panel.image_data))
                            image.save(panel_path)
                            logger.debug(f"Saved panel to {panel_path}")
                        except Exception as e:
                            logger.error(f"Error saving panel: {e}")
                
                # Compose and save complete page
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