"""Image generator for reference experiments."""

import asyncio
import os
from pathlib import Path
from datetime import datetime
from typing import Callable, List, Optional
import logging

from src.api.gemini_client import GeminiClient
from src.api.rate_limiter import RateLimiter
from src.config import Config

from .models import Combination, GeneratedImage, RefExperiment, ExperimentSession

logger = logging.getLogger(__name__)


class RefExpImageGenerator:
    """Generate images for reference experiment combinations."""
    
    def __init__(
        self,
        gemini_client: Optional[GeminiClient] = None,
        config: Optional[Config] = None,
        output_dir: str = "output/reference_experiments"
    ):
        """Initialize image generator.
        
        Args:
            gemini_client: Existing Gemini client or None to create new
            config: Configuration object or None to use defaults
            output_dir: Output directory for images
        """
        self.client = gemini_client or GeminiClient()
        self.config = config
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up rate limiter
        rate_limit = 10  # Default 10 per minute
        if config and hasattr(config, 'reference_experiments'):
            rate_limit = getattr(config.reference_experiments, 'api_rate_limit', 10)
        
        self.rate_limiter = RateLimiter(calls_per_minute=rate_limit)
    
    async def generate_images(
        self,
        experiment: RefExperiment,
        combinations: List[Combination],
        session: ExperimentSession,
        progress_callback: Optional[Callable] = None,
        parallel: int = 3
    ) -> List[GeneratedImage]:
        """Generate images for combinations.
        
        Args:
            experiment: RefExperiment object
            combinations: List of combinations to generate
            session: Experiment session for tracking
            progress_callback: Optional callback for progress updates
            parallel: Number of parallel generations
            
        Returns:
            List of GeneratedImage objects
        """
        generated_images = []
        semaphore = asyncio.Semaphore(parallel)
        
        # Create session directory
        session_dir = self.output_dir / f"session_{session.session_id}"
        session_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating {len(combinations)} images with {parallel} parallel workers")
        
        # Generate images
        tasks = []
        for combo in combinations:
            task = self._generate_with_semaphore(
                experiment, combo, session_dir, semaphore
            )
            tasks.append(task)
        
        # Process with progress updates
        for i, task in enumerate(asyncio.as_completed(tasks)):
            try:
                image = await task
                if image:
                    generated_images.append(image)
                    session.generated_count = len(generated_images)
                
                # Update progress
                if progress_callback:
                    progress = (i + 1) / len(combinations) * 100
                    progress_callback(progress, f"Generated {i + 1}/{len(combinations)} images")
                    
            except Exception as e:
                logger.error(f"Failed to generate image: {e}")
                session.add_error(str(e))
        
        logger.info(f"Successfully generated {len(generated_images)}/{len(combinations)} images")
        return generated_images
    
    async def _generate_with_semaphore(
        self,
        experiment: RefExperiment,
        combination: Combination,
        output_dir: Path,
        semaphore: asyncio.Semaphore
    ) -> Optional[GeneratedImage]:
        """Generate single image with semaphore control.
        
        Args:
            experiment: RefExperiment object
            combination: Combination to generate
            output_dir: Output directory
            semaphore: Semaphore for concurrency control
            
        Returns:
            GeneratedImage or None if failed
        """
        async with semaphore:
            await self.rate_limiter.acquire()
            return await self.generate_single_image(
                experiment, combination, output_dir
            )
    
    async def generate_single_image(
        self,
        experiment: RefExperiment,
        combination: Combination,
        output_dir: Path
    ) -> Optional[GeneratedImage]:
        """Generate a single image for a combination.
        
        Args:
            experiment: RefExperiment object
            combination: Combination to generate
            output_dir: Output directory
            
        Returns:
            GeneratedImage or None if failed
        """
        try:
            logger.debug(f"Generating image for combination {combination.id}")
            
            # Apply image settings
            width = 1024
            height = 1536
            quality = "high"
            
            if experiment.image_settings:
                width = experiment.image_settings.get('width', width)
                height = experiment.image_settings.get('height', height)
                quality = experiment.image_settings.get('quality', quality)
            
            # Apply settings overrides
            if experiment.settings:
                quality = experiment.settings.get('quality', quality)
            
            # Generate image using Gemini API - use generate_panel_image which is working
            # Note: generate_panel_image doesn't take width/height/quality directly,
            # but uses style_config for styling
            style_config = {}
            if quality:
                style_config['quality'] = quality
            if width and height:
                style_config['dimensions'] = f"{width}x{height}"
            
            image_data = await self.client.generate_panel_image(
                prompt=combination.prompt,
                reference_images=None,  # No reference images for experiments
                style_config=style_config
            )
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            suffix = combination.get_filename_suffix()
            filename = f"exp_{timestamp}_{combination.id:03d}_{suffix}.png"
            filepath = output_dir / filename
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.debug(f"Saved image to {filepath}")
            
            # Create GeneratedImage object
            generated_image = GeneratedImage(
                combination=combination,
                image_data=image_data,
                filepath=str(filepath),
                timestamp=datetime.now(),
                generation_metadata={
                    'width': width,
                    'height': height,
                    'quality': quality,
                    'model': experiment.image_settings.get('model', 'gemini-2.5-flash-image-preview')
                },
                experiment_name=experiment.name,
                model_used=experiment.image_settings.get('model', 'gemini-2.5-flash-image-preview')
            )
            
            return generated_image
            
        except Exception as e:
            logger.error(f"Failed to generate image for combination {combination.id}: {e}")
            return None
    
    def cleanup_old_sessions(self, days: int = 7):
        """Clean up old session directories.
        
        Args:
            days: Number of days to keep sessions
        """
        import shutil
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        
        for session_dir in self.output_dir.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith('session_'):
                # Parse timestamp from directory name
                try:
                    timestamp_str = session_dir.name.replace('session_', '')
                    dir_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    
                    if dir_time < cutoff:
                        logger.info(f"Removing old session directory: {session_dir}")
                        shutil.rmtree(session_dir)
                        
                except (ValueError, OSError) as e:
                    logger.warning(f"Could not process directory {session_dir}: {e}")