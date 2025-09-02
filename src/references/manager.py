"""Reference manager for centralized reference operations."""

import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
import re
from dataclasses import dataclass
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

from .models import (
    BaseReference,
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
)
from .storage import ReferenceStorage, ReferenceNotFoundError
from .generators import (
    CharacterReferenceGenerator,
    LocationReferenceGenerator,
    ObjectReferenceGenerator,
    StyleGuideGenerator,
    GenerationConfig,
)
from src.api import GeminiClient

logger = logging.getLogger(__name__)


@dataclass
class ReferenceCache:
    """Cache for frequently accessed references."""
    
    reference: BaseReference
    last_accessed: datetime
    access_count: int = 0
    
    def touch(self):
        """Update last accessed time and increment count."""
        self.last_accessed = datetime.now()
        self.access_count += 1


class ReferenceManager:
    """Central manager for all reference operations."""
    
    def __init__(
        self,
        storage: Optional[ReferenceStorage] = None,
        gemini_client: Optional[GeminiClient] = None,
        generation_config: Optional[GenerationConfig] = None,
        cache_size: int = 50,
        cache_ttl_minutes: int = 30
    ):
        """Initialize reference manager.
        
        Args:
            storage: Reference storage system
            gemini_client: Gemini API client for generation
            generation_config: Configuration for reference generation
            cache_size: Maximum number of references to cache
            cache_ttl_minutes: Cache time-to-live in minutes
        """
        self.storage = storage or ReferenceStorage()
        self.gemini_client = gemini_client
        self.generation_config = generation_config or GenerationConfig()
        
        # Initialize generators if Gemini client is provided
        if self.gemini_client:
            self.character_generator = CharacterReferenceGenerator(
                self.gemini_client, self.storage, self.generation_config
            )
            self.location_generator = LocationReferenceGenerator(
                self.gemini_client, self.storage, self.generation_config
            )
            self.object_generator = ObjectReferenceGenerator(
                self.gemini_client, self.storage, self.generation_config
            )
            self.style_generator = StyleGuideGenerator(
                self.gemini_client, self.storage, self.generation_config
            )
        else:
            self.character_generator = None
            self.location_generator = None
            self.object_generator = None
            self.style_generator = None
        
        # Cache management
        self.cache: Dict[Tuple[str, str], ReferenceCache] = {}
        self.cache_size = cache_size
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        
        # Reference naming patterns
        self.naming_patterns = {
            "character": re.compile(r"^[A-Za-z][A-Za-z0-9_\s-]*$"),
            "location": re.compile(r"^[A-Za-z][A-Za-z0-9_\s-]*$"),
            "object": re.compile(r"^[A-Za-z][A-Za-z0-9_\s-]*$"),
            "styleguide": re.compile(r"^[A-Za-z][A-Za-z0-9_\s-]*$"),
        }
    
    # === CRUD Operations ===
    
    def create_reference(
        self,
        ref_type: str,
        name: str,
        description: str,
        **kwargs
    ) -> BaseReference:
        """Create a new reference without generation.
        
        Args:
            ref_type: Type of reference
            name: Reference name
            description: Reference description
            **kwargs: Type-specific attributes
            
        Returns:
            Created reference
            
        Raises:
            ValueError: If reference already exists or invalid parameters
        """
        # Validate name
        if not self._validate_name(ref_type, name):
            raise ValueError(f"Invalid name format for {ref_type}: {name}")
        
        # Check if already exists
        if self.storage.exists(ref_type, name):
            raise ValueError(f"Reference already exists: {ref_type}/{name}")
        
        # Create reference based on type
        if ref_type == "character":
            reference = CharacterReference(name=name, description=description, **kwargs)
        elif ref_type == "location":
            reference = LocationReference(name=name, description=description, **kwargs)
        elif ref_type == "object":
            reference = ObjectReference(name=name, description=description, **kwargs)
        elif ref_type == "styleguide":
            reference = StyleGuide(name=name, description=description, **kwargs)
        else:
            raise ValueError(f"Unknown reference type: {ref_type}")
        
        # Save to storage
        self.storage.save_reference(reference)
        
        # Add to cache
        self._cache_reference(ref_type, name, reference)
        
        logger.info(f"Created {ref_type} reference: {name}")
        return reference
    
    def get_reference(
        self,
        ref_type: str,
        name: str,
        use_cache: bool = True
    ) -> Optional[BaseReference]:
        """Get a reference by type and name.
        
        Args:
            ref_type: Type of reference
            name: Reference name
            use_cache: Whether to use cache
            
        Returns:
            Reference if found, None otherwise
        """
        cache_key = (ref_type, name)
        
        # Check cache first
        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            
            # Check if cache is still valid
            if datetime.now() - cached.last_accessed < self.cache_ttl:
                cached.touch()
                logger.debug(f"Cache hit for {ref_type}/{name}")
                return cached.reference
            else:
                # Cache expired
                del self.cache[cache_key]
        
        # Load from storage
        try:
            reference = self.storage.load_reference(ref_type, name)
            
            # Update cache
            if use_cache:
                self._cache_reference(ref_type, name, reference)
            
            return reference
        
        except ReferenceNotFoundError:
            logger.debug(f"Reference not found: {ref_type}/{name}")
            return None
    
    def update_reference(
        self,
        ref_type: str,
        name: str,
        updates: Dict[str, Any]
    ) -> BaseReference:
        """Update an existing reference.
        
        Args:
            ref_type: Type of reference
            name: Reference name
            updates: Dictionary of updates to apply
            
        Returns:
            Updated reference
            
        Raises:
            ReferenceNotFoundError: If reference doesn't exist
        """
        # Load existing reference
        reference = self.get_reference(ref_type, name, use_cache=False)
        if not reference:
            raise ReferenceNotFoundError(f"Reference not found: {ref_type}/{name}")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(reference, key):
                setattr(reference, key, value)
        
        # Update timestamp
        reference.update_timestamp()
        
        # Save updated reference
        self.storage.save_reference(reference)
        
        # Invalidate cache
        self._invalidate_cache(ref_type, name)
        
        logger.info(f"Updated {ref_type} reference: {name}")
        return reference
    
    def delete_reference(self, ref_type: str, name: str) -> None:
        """Delete a reference.
        
        Args:
            ref_type: Type of reference
            name: Reference name
            
        Raises:
            ReferenceNotFoundError: If reference doesn't exist
        """
        # Delete from storage
        self.storage.delete_reference(ref_type, name)
        
        # Remove from cache
        self._invalidate_cache(ref_type, name)
        
        logger.info(f"Deleted {ref_type} reference: {name}")
    
    def list_references(
        self,
        ref_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """List available references.
        
        Args:
            ref_type: Specific type to list, or None for all
            tags: Filter by tags if provided
            
        Returns:
            Dictionary mapping types to reference names
        """
        references = self.storage.list_references(ref_type)
        
        # Filter by tags if provided
        if tags:
            filtered = {}
            for rtype, names in references.items():
                filtered_names = []
                for name in names:
                    ref = self.get_reference(rtype, name)
                    if ref and any(tag in ref.tags for tag in tags):
                        filtered_names.append(name)
                filtered[rtype] = filtered_names
            return filtered
        
        return references
    
    # === Generation Operations ===
    
    async def generate_character(
        self,
        name: str,
        description: str,
        poses: Optional[List[str]] = None,
        expressions: Optional[List[str]] = None,
        style_guide: Optional[str] = None,
        **kwargs
    ) -> CharacterReference:
        """Generate a new character reference with images.
        
        Args:
            name: Character name
            description: Character description
            poses: Poses to generate
            expressions: Expressions to generate
            style_guide: Name of style guide to use
            **kwargs: Additional character attributes
            
        Returns:
            Generated character reference
            
        Raises:
            ValueError: If generator not available or generation fails
        """
        if not self.character_generator:
            raise ValueError("Character generator not available (no Gemini client)")
        
        # Load style guide if specified
        style = None
        if style_guide:
            style = self.get_reference("styleguide", style_guide)
            if not style:
                logger.warning(f"Style guide not found: {style_guide}")
        
        # Generate character
        character = await self.character_generator.generate_reference(
            name=name,
            description=description,
            poses=poses,
            expressions=expressions,
            style_guide=style,
            **kwargs
        )
        
        # Add to cache
        self._cache_reference("character", name, character)
        
        logger.info(f"Generated character reference: {name}")
        return character
    
    async def generate_location(
        self,
        name: str,
        description: str,
        angles: Optional[List[str]] = None,
        lighting_conditions: Optional[List[str]] = None,
        style_guide: Optional[str] = None,
        **kwargs
    ) -> LocationReference:
        """Generate a new location reference with images.
        
        Args:
            name: Location name
            description: Location description
            angles: Camera angles to generate
            lighting_conditions: Lighting variations
            style_guide: Name of style guide to use
            **kwargs: Additional location attributes
            
        Returns:
            Generated location reference
        """
        if not self.location_generator:
            raise ValueError("Location generator not available (no Gemini client)")
        
        # Load style guide if specified
        style = None
        if style_guide:
            style = self.get_reference("styleguide", style_guide)
        
        # Generate location
        location = await self.location_generator.generate_reference(
            name=name,
            description=description,
            angles=angles,
            lighting_conditions=lighting_conditions,
            style_guide=style,
            **kwargs
        )
        
        # Add to cache
        self._cache_reference("location", name, location)
        
        logger.info(f"Generated location reference: {name}")
        return location
    
    async def generate_object(
        self,
        name: str,
        description: str,
        views: Optional[List[str]] = None,
        states: Optional[List[str]] = None,
        style_guide: Optional[str] = None,
        **kwargs
    ) -> ObjectReference:
        """Generate a new object reference with images.
        
        Args:
            name: Object name
            description: Object description
            views: Views to generate
            states: States to generate
            style_guide: Name of style guide to use
            **kwargs: Additional object attributes
            
        Returns:
            Generated object reference
        """
        if not self.object_generator:
            raise ValueError("Object generator not available (no Gemini client)")
        
        # Load style guide if specified
        style = None
        if style_guide:
            style = self.get_reference("styleguide", style_guide)
        
        # Generate object
        obj = await self.object_generator.generate_reference(
            name=name,
            description=description,
            views=views,
            states=states,
            style_guide=style,
            **kwargs
        )
        
        # Add to cache
        self._cache_reference("object", name, obj)
        
        logger.info(f"Generated object reference: {name}")
        return obj
    
    async def generate_style_guide(
        self,
        name: str,
        description: str,
        art_style: str,
        color_palette: Optional[List[str]] = None,
        **kwargs
    ) -> StyleGuide:
        """Generate a new style guide.
        
        Args:
            name: Style guide name
            description: Style description
            art_style: Art style name
            color_palette: Color codes
            **kwargs: Additional style attributes
            
        Returns:
            Generated style guide
        """
        if not self.style_generator:
            raise ValueError("Style generator not available (no Gemini client)")
        
        # Generate style guide
        style = await self.style_generator.generate_reference(
            name=name,
            description=description,
            art_style=art_style,
            color_palette=color_palette,
            **kwargs
        )
        
        # Add to cache
        self._cache_reference("styleguide", name, style)
        
        logger.info(f"Generated style guide: {name}")
        return style
    
    # === Lookup and Matching ===
    
    def find_references_in_text(
        self,
        text: str,
        ref_types: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """Find reference names mentioned in text.
        
        Args:
            text: Text to search
            ref_types: Types to search for, or None for all
            
        Returns:
            Dictionary mapping reference types to found names
        """
        found = defaultdict(list)
        types_to_check = ref_types or ["character", "location", "object"]
        
        for ref_type in types_to_check:
            references = self.list_references(ref_type)[ref_type]
            
            for ref_name in references:
                # Simple case-insensitive search
                if ref_name.lower() in text.lower():
                    found[ref_type].append(ref_name)
                
                # Also check for partial matches (e.g., "Alex" matches "Alex the Hero")
                name_parts = ref_name.split()
                if len(name_parts) > 1 and name_parts[0].lower() in text.lower():
                    if ref_name not in found[ref_type]:
                        found[ref_type].append(ref_name)
        
        return dict(found)
    
    def get_character_images(
        self,
        characters: List[str]
    ) -> Dict[str, Dict[str, bytes]]:
        """Get images for multiple characters.
        
        Args:
            characters: List of character names
            
        Returns:
            Dictionary mapping character names to their images
        """
        result = {}
        
        for char_name in characters:
            char = self.get_reference("character", char_name)
            if char and isinstance(char, CharacterReference):
                char_images = {}
                
                # Load each image file
                for key, filename in char.images.items():
                    try:
                        image_data = self.storage.load_reference_image(
                            "character", char_name, filename
                        )
                        char_images[key] = image_data
                    except Exception as e:
                        logger.warning(f"Could not load image {filename}: {e}")
                
                result[char_name] = char_images
        
        return result
    
    def get_location_images(
        self,
        locations: List[str]
    ) -> Dict[str, Dict[str, bytes]]:
        """Get images for multiple locations.
        
        Args:
            locations: List of location names
            
        Returns:
            Dictionary mapping location names to their images
        """
        result = {}
        
        for loc_name in locations:
            loc = self.get_reference("location", loc_name)
            if loc and isinstance(loc, LocationReference):
                loc_images = {}
                
                # Load each image file
                for key, filename in loc.images.items():
                    try:
                        image_data = self.storage.load_reference_image(
                            "location", loc_name, filename
                        )
                        loc_images[key] = image_data
                    except Exception as e:
                        logger.warning(f"Could not load image {filename}: {e}")
                
                result[loc_name] = loc_images
        
        return result
    
    # === Cache Management ===
    
    def _cache_reference(self, ref_type: str, name: str, reference: BaseReference):
        """Add reference to cache."""
        cache_key = (ref_type, name)
        
        # Check cache size limit
        if len(self.cache) >= self.cache_size:
            self._evict_oldest_cache()
        
        self.cache[cache_key] = ReferenceCache(
            reference=reference,
            last_accessed=datetime.now()
        )
    
    def _invalidate_cache(self, ref_type: str, name: str):
        """Remove reference from cache."""
        cache_key = (ref_type, name)
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def _evict_oldest_cache(self):
        """Evict least recently used cache entry."""
        if not self.cache:
            return
        
        # Find oldest entry
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: self.cache[k].last_accessed
        )
        
        del self.cache[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key}")
    
    def clear_cache(self):
        """Clear all cached references."""
        self.cache.clear()
        logger.info("Cleared reference cache")
    
    # === Validation and Cleanup ===
    
    def _validate_name(self, ref_type: str, name: str) -> bool:
        """Validate reference name format.
        
        Args:
            ref_type: Type of reference
            name: Name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if ref_type not in self.naming_patterns:
            return True  # No pattern defined, allow any
        
        pattern = self.naming_patterns[ref_type]
        return bool(pattern.match(name))
    
    def validate_all_references(self) -> Dict[str, List[str]]:
        """Validate all stored references.
        
        Returns:
            Dictionary of validation errors by reference
        """
        errors = {}
        
        for ref_type in ["character", "location", "object", "styleguide"]:
            names = self.list_references(ref_type)[ref_type]
            
            for name in names:
                ref = self.get_reference(ref_type, name)
                if ref:
                    try:
                        ref.validate()
                    except ValueError as e:
                        errors[f"{ref_type}/{name}"] = str(e)
        
        return errors
    
    def cleanup_unused_references(
        self,
        days_unused: int = 30
    ) -> List[Tuple[str, str]]:
        """Remove references that haven't been used recently.
        
        Args:
            days_unused: Days of inactivity before cleanup
            
        Returns:
            List of removed references (type, name)
        """
        removed = []
        cutoff_date = datetime.now() - timedelta(days=days_unused)
        
        for ref_type in ["character", "location", "object", "styleguide"]:
            names = self.list_references(ref_type)[ref_type]
            
            for name in names:
                ref = self.get_reference(ref_type, name)
                if ref and ref.updated_at < cutoff_date:
                    self.delete_reference(ref_type, name)
                    removed.append((ref_type, name))
        
        logger.info(f"Cleaned up {len(removed)} unused references")
        return removed
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get reference manager statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = {
            "total_references": 0,
            "references_by_type": {},
            "cache_size": len(self.cache),
            "cache_hit_rate": 0.0,
            "storage_info": self.storage.get_storage_info(),
        }
        
        # Count references by type
        all_refs = self.list_references()
        for ref_type, names in all_refs.items():
            stats["references_by_type"][ref_type] = len(names)
            stats["total_references"] += len(names)
        
        # Calculate cache hit rate
        total_accesses = sum(c.access_count for c in self.cache.values())
        if total_accesses > 0:
            cache_hits = sum(c.access_count - 1 for c in self.cache.values())
            stats["cache_hit_rate"] = cache_hits / total_accesses
        
        return stats