"""Reference images tracker for maintaining experiment history."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List
import logging

from .models import ExperimentSession, GeneratedImage, RefExperiment

logger = logging.getLogger(__name__)


class ReferenceTracker:
    """Track and document reference experiment results."""
    
    def __init__(self, output_dir: str = "."):
        """Initialize reference tracker.
        
        Args:
            output_dir: Base output directory for project
        """
        self.output_dir = Path(output_dir)
        self.reference_doc = self.output_dir / "reference_images.md"
    
    def update_reference_doc(self, session: ExperimentSession) -> None:
        """Update reference_images.md with experiment results.
        
        Args:
            session: Completed experiment session
        """
        # Create backup if file exists
        if self.reference_doc.exists():
            self.create_backup()
        
        # Format markdown content
        content = self._format_session_markdown(session)
        
        # Append to file (create if doesn't exist)
        mode = 'a' if self.reference_doc.exists() else 'w'
        
        with open(self.reference_doc, mode, encoding='utf-8') as f:
            if mode == 'w':
                # Add header for new file
                f.write("# Reference Experiments History\n\n")
                f.write("This document tracks all reference experiment sessions.\n\n")
                f.write("---\n\n")
            
            f.write(content)
            f.write("\n---\n\n")
        
        logger.info(f"Updated reference document: {self.reference_doc}")
    
    def create_backup(self) -> str:
        """Create backup of existing reference document.
        
        Returns:
            Path to backup file
        """
        if not self.reference_doc.exists():
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.reference_doc.with_suffix(f".{timestamp}.bak")
        
        shutil.copy2(self.reference_doc, backup_path)
        logger.info(f"Created backup: {backup_path}")
        
        # Clean old backups (keep last 5)
        self._clean_old_backups()
        
        return str(backup_path)
    
    def _clean_old_backups(self, keep: int = 5):
        """Clean old backup files.
        
        Args:
            keep: Number of backups to keep
        """
        backup_files = sorted(
            self.output_dir.glob("reference_images.*.bak"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        for backup in backup_files[keep:]:
            backup.unlink()
            logger.debug(f"Removed old backup: {backup}")
    
    def _format_session_markdown(self, session: ExperimentSession) -> str:
        """Format experiment session as markdown.
        
        Args:
            session: Experiment session
            
        Returns:
            Formatted markdown string
        """
        lines = []
        
        # Session header
        lines.append(f"## Reference Experiment: {session.session_id}")
        lines.append("")
        
        # Experiment details
        lines.append(f"**Name**: {session.experiment.name}")
        if session.experiment.description:
            lines.append(f"**Description**: {session.experiment.description}")
        lines.append(f"**Source File**: {session.experiment.source_file}")
        lines.append(f"**Total Combinations**: {session.total_combinations}")
        lines.append(f"**Generated**: {session.generated_count}")
        
        if session.failed_count > 0:
            lines.append(f"**Failed**: {session.failed_count}")
        
        # Timing information
        lines.append(f"**Started**: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if session.end_time:
            lines.append(f"**Completed**: {session.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            duration = session.get_duration()
            lines.append(f"**Duration**: {duration:.1f} seconds")
        
        # Settings if present
        if session.experiment.settings:
            lines.append("")
            lines.append("**Settings**:")
            for key, value in session.experiment.settings.items():
                lines.append(f"- {key}: {value}")
        
        lines.append("")
        
        # Generated images
        if session.generated_images:
            lines.append("### Generated Images")
            lines.append("")
            
            for image in session.generated_images:
                lines.append(self._format_image_markdown(image, session.experiment))
                lines.append("")
        
        # Errors if any
        if session.errors:
            lines.append("### Errors")
            lines.append("")
            for error in session.errors:
                lines.append(f"- {error}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_image_markdown(
        self,
        image: GeneratedImage,
        experiment: RefExperiment
    ) -> str:
        """Format single image as markdown.
        
        Args:
            image: GeneratedImage object
            experiment: RefExperiment object
            
        Returns:
            Formatted markdown string
        """
        lines = []
        
        # Image header
        lines.append(f"#### Combination {image.combination.id}")
        
        # Variables
        lines.append("- **Variables**:")
        for var_name, var_value in sorted(image.combination.variables.items()):
            lines.append(f"  - {var_name}: {var_value}")
        
        # Prompt
        lines.append(f"- **Prompt**: {image.combination.prompt}")
        
        # Image path (relative to project root)
        rel_path = image.get_relative_path(str(self.output_dir))
        lines.append(f"- **Image**: `{rel_path}`")
        
        # Model and timestamp
        lines.append(f"- **Model**: {image.model_used}")
        lines.append(f"- **Generated**: {image.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Image metadata if present
        if image.generation_metadata:
            meta = image.generation_metadata
            if 'width' in meta and 'height' in meta:
                lines.append(f"- **Dimensions**: {meta['width']}x{meta['height']}")
            if 'quality' in meta:
                lines.append(f"- **Quality**: {meta['quality']}")
        
        return "\n".join(lines)
    
    def get_session_summary(self, session: ExperimentSession) -> str:
        """Get a brief summary of the session.
        
        Args:
            session: Experiment session
            
        Returns:
            Summary string
        """
        success_rate = session.get_success_rate()
        duration = session.get_duration()
        
        return (
            f"Session {session.session_id}: "
            f"{session.generated_count}/{session.total_combinations} images generated "
            f"({success_rate:.1f}% success) in {duration:.1f}s"
        )