"""Reference storage system for comic book generation."""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
import threading
import time
from contextlib import contextmanager

from .models import (
    BaseReference,
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
    create_reference_from_dict,
)

logger = logging.getLogger(__name__)


class ReferenceStorageError(Exception):
    """Base exception for reference storage operations."""
    pass


class ReferenceNotFoundError(ReferenceStorageError):
    """Raised when a reference cannot be found."""
    pass


class ReferenceStorage:
    """File-based storage system for references."""
    
    def __init__(self, base_path: Union[str, Path] = "references/"):
        """Initialize reference storage.
        
        Args:
            base_path: Base directory for reference storage
        """
        self.base_path = Path(base_path)
        self._ensure_directory_structure()
        
        # File locking for concurrent access
        self._locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()
        
        # Type to directory mapping
        self._type_dirs = {
            "character": self.base_path / "characters",
            "location": self.base_path / "locations", 
            "object": self.base_path / "objects",
            "styleguide": self.base_path / "styles",
        }
    
    def _ensure_directory_structure(self):
        """Create directory structure if it doesn't exist."""
        directories = [
            self.base_path,
            self.base_path / "characters",
            self.base_path / "locations",
            self.base_path / "objects",
            self.base_path / "styles",
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    @contextmanager
    def _get_file_lock(self, file_path: Union[str, Path]):
        """Get a file-specific lock for thread-safe operations."""
        file_key = str(file_path)
        
        with self._global_lock:
            if file_key not in self._locks:
                self._locks[file_key] = threading.Lock()
            lock = self._locks[file_key]
        
        with lock:
            yield
    
    def _get_reference_path(self, ref_type: str, name: str) -> Path:
        """Get the file path for a reference.
        
        Args:
            ref_type: Type of reference (character, location, object, styleguide)
            name: Name of the reference
            
        Returns:
            Path to reference metadata file
            
        Raises:
            ValueError: If reference type is invalid
        """
        if ref_type not in self._type_dirs:
            raise ValueError(f"Invalid reference type: {ref_type}")
        
        # Sanitize filename
        safe_name = self._sanitize_filename(name)
        return self._type_dirs[ref_type] / f"{safe_name}.json"
    
    def _get_image_dir(self, ref_type: str, name: str) -> Path:
        """Get the image directory for a reference.
        
        Args:
            ref_type: Type of reference
            name: Name of the reference
            
        Returns:
            Path to reference image directory
        """
        safe_name = self._sanitize_filename(name)
        return self._type_dirs[ref_type] / f"{safe_name}_images"
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Replace invalid characters with underscores
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Ensure not empty
        if not filename:
            filename = "unnamed"
        
        return filename
    
    def save_reference(self, reference: BaseReference) -> None:
        """Save a reference to storage.
        
        Args:
            reference: Reference to save
            
        Raises:
            ReferenceStorageError: If save operation fails
        """
        ref_type = reference.__class__.__name__.lower().replace("reference", "")
        if ref_type == "styleguide":
            ref_type = "styleguide"  # Handle StyleGuide special case
        
        ref_path = self._get_reference_path(ref_type, reference.name)
        
        try:
            with self._get_file_lock(ref_path):
                # Convert to dictionary
                data = reference.to_dict()
                
                # Save metadata
                with open(ref_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                # Create image directory
                img_dir = self._get_image_dir(ref_type, reference.name)
                img_dir.mkdir(exist_ok=True)
                
                logger.info(f"Saved {ref_type} reference: {reference.name}")
        
        except Exception as e:
            logger.error(f"Failed to save reference {reference.name}: {e}")
            raise ReferenceStorageError(f"Failed to save reference: {e}") from e
    
    def load_reference(self, ref_type: str, name: str) -> BaseReference:
        """Load a reference from storage.
        
        Args:
            ref_type: Type of reference to load
            name: Name of the reference to load
            
        Returns:
            Loaded reference
            
        Raises:
            ReferenceNotFoundError: If reference doesn't exist
            ReferenceStorageError: If load operation fails
        """
        ref_path = self._get_reference_path(ref_type, name)
        
        if not ref_path.exists():
            raise ReferenceNotFoundError(f"Reference not found: {ref_type}/{name}")
        
        try:
            with self._get_file_lock(ref_path):
                with open(ref_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create reference from data
                reference = create_reference_from_dict(data)
                logger.debug(f"Loaded {ref_type} reference: {name}")
                return reference
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in reference file {ref_path}: {e}")
            raise ReferenceStorageError(f"Invalid reference file format: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load reference {name}: {e}")
            raise ReferenceStorageError(f"Failed to load reference: {e}") from e
    
    def list_references(self, ref_type: Optional[str] = None) -> Dict[str, List[str]]:
        """List available references.
        
        Args:
            ref_type: Specific type to list, or None for all types
            
        Returns:
            Dictionary mapping reference types to lists of names
        """
        result = {}
        
        types_to_check = [ref_type] if ref_type else self._type_dirs.keys()
        
        for rtype in types_to_check:
            if rtype not in self._type_dirs:
                continue
            
            references = []
            type_dir = self._type_dirs[rtype]
            
            if type_dir.exists():
                for json_file in type_dir.glob("*.json"):
                    # Extract name from filename
                    name = json_file.stem
                    # Skip files that look like they might be image directories
                    if not name.endswith("_images"):
                        references.append(name)
            
            result[rtype] = sorted(references)
        
        return result
    
    def exists(self, ref_type: str, name: str) -> bool:
        """Check if a reference exists.
        
        Args:
            ref_type: Type of reference
            name: Name of the reference
            
        Returns:
            True if reference exists, False otherwise
        """
        try:
            ref_path = self._get_reference_path(ref_type, name)
            return ref_path.exists()
        except ValueError:
            return False
    
    def delete_reference(self, ref_type: str, name: str) -> None:
        """Delete a reference from storage.
        
        Args:
            ref_type: Type of reference to delete
            name: Name of the reference to delete
            
        Raises:
            ReferenceNotFoundError: If reference doesn't exist
            ReferenceStorageError: If delete operation fails
        """
        ref_path = self._get_reference_path(ref_type, name)
        
        if not ref_path.exists():
            raise ReferenceNotFoundError(f"Reference not found: {ref_type}/{name}")
        
        try:
            with self._get_file_lock(ref_path):
                # Delete metadata file
                ref_path.unlink()
                
                # Delete image directory if it exists
                img_dir = self._get_image_dir(ref_type, name)
                if img_dir.exists():
                    shutil.rmtree(img_dir)
                
                logger.info(f"Deleted {ref_type} reference: {name}")
        
        except Exception as e:
            logger.error(f"Failed to delete reference {name}: {e}")
            raise ReferenceStorageError(f"Failed to delete reference: {e}") from e
    
    def save_reference_image(
        self, 
        ref_type: str, 
        name: str, 
        image_key: str, 
        image_data: bytes,
        format: str = "png"
    ) -> str:
        """Save an image file for a reference.
        
        Args:
            ref_type: Type of reference
            name: Name of the reference
            image_key: Key identifying the specific image
            image_data: Binary image data
            format: Image format (png, jpg, etc.)
            
        Returns:
            Filename of saved image
            
        Raises:
            ReferenceStorageError: If save operation fails
        """
        img_dir = self._get_image_dir(ref_type, name)
        img_dir.mkdir(exist_ok=True)
        
        # Create safe filename
        safe_key = self._sanitize_filename(image_key)
        filename = f"{safe_key}.{format.lower()}"
        img_path = img_dir / filename
        
        try:
            with self._get_file_lock(img_path):
                with open(img_path, 'wb') as f:
                    f.write(image_data)
                
                logger.debug(f"Saved image: {img_path}")
                return filename
        
        except Exception as e:
            logger.error(f"Failed to save image {img_path}: {e}")
            raise ReferenceStorageError(f"Failed to save image: {e}") from e
    
    def load_reference_image(
        self, 
        ref_type: str, 
        name: str, 
        filename: str
    ) -> bytes:
        """Load an image file for a reference.
        
        Args:
            ref_type: Type of reference
            name: Name of the reference
            filename: Filename of the image
            
        Returns:
            Binary image data
            
        Raises:
            ReferenceNotFoundError: If image file doesn't exist
            ReferenceStorageError: If load operation fails
        """
        img_dir = self._get_image_dir(ref_type, name)
        img_path = img_dir / filename
        
        if not img_path.exists():
            raise ReferenceNotFoundError(f"Image not found: {img_path}")
        
        try:
            with self._get_file_lock(img_path):
                with open(img_path, 'rb') as f:
                    return f.read()
        
        except Exception as e:
            logger.error(f"Failed to load image {img_path}: {e}")
            raise ReferenceStorageError(f"Failed to load image: {e}") from e
    
    def list_reference_images(self, ref_type: str, name: str) -> List[str]:
        """List image files for a reference.
        
        Args:
            ref_type: Type of reference
            name: Name of the reference
            
        Returns:
            List of image filenames
        """
        img_dir = self._get_image_dir(ref_type, name)
        
        if not img_dir.exists():
            return []
        
        images = []
        for img_file in img_dir.iterdir():
            if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']:
                images.append(img_file.name)
        
        return sorted(images)
    
    def get_storage_info(self) -> Dict[str, Any]:
        """Get storage statistics and information.
        
        Returns:
            Dictionary with storage information
        """
        info = {
            "base_path": str(self.base_path),
            "total_references": 0,
            "references_by_type": {},
            "total_images": 0,
            "storage_size_mb": 0,
        }
        
        # Count references and images
        for ref_type in self._type_dirs:
            refs = self.list_references(ref_type)[ref_type]
            info["references_by_type"][ref_type] = len(refs)
            info["total_references"] += len(refs)
            
            # Count images for each reference
            for ref_name in refs:
                images = self.list_reference_images(ref_type, ref_name)
                info["total_images"] += len(images)
        
        # Calculate storage size
        try:
            def get_dir_size(path: Path) -> int:
                total = 0
                for item in path.rglob('*'):
                    if item.is_file():
                        total += item.stat().st_size
                return total
            
            if self.base_path.exists():
                size_bytes = get_dir_size(self.base_path)
                info["storage_size_mb"] = round(size_bytes / 1024 / 1024, 2)
        except Exception as e:
            logger.warning(f"Could not calculate storage size: {e}")
            info["storage_size_mb"] = 0
        
        return info
    
    def cleanup_orphaned_images(self) -> int:
        """Clean up image directories that don't have corresponding references.
        
        Returns:
            Number of orphaned image directories removed
        """
        removed_count = 0
        
        for ref_type, type_dir in self._type_dirs.items():
            if not type_dir.exists():
                continue
            
            # Find all image directories
            for item in type_dir.iterdir():
                if item.is_dir() and item.name.endswith("_images"):
                    # Extract reference name
                    ref_name = item.name[:-7]  # Remove "_images" suffix
                    
                    # Check if corresponding reference file exists
                    ref_path = type_dir / f"{ref_name}.json"
                    if not ref_path.exists():
                        try:
                            shutil.rmtree(item)
                            logger.info(f"Removed orphaned image directory: {item}")
                            removed_count += 1
                        except Exception as e:
                            logger.error(f"Failed to remove orphaned directory {item}: {e}")
        
        return removed_count