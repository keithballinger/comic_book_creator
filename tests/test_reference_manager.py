"""Unit tests for reference manager."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
import tempfile
import shutil

from src.references.manager import ReferenceManager, ReferenceCache
from src.references.models import (
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
)
from src.references.storage import ReferenceStorage, ReferenceNotFoundError
from src.api import GeminiClient


class TestReferenceManager:
    """Test ReferenceManager class."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        temp_dir = tempfile.mkdtemp()
        storage = ReferenceStorage(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client."""
        client = Mock(spec=GeminiClient)
        client.generate_image = AsyncMock()
        return client
    
    @pytest.fixture
    def manager(self, temp_storage, mock_gemini_client):
        """Create reference manager."""
        return ReferenceManager(
            storage=temp_storage,
            gemini_client=mock_gemini_client,
            cache_size=10,
            cache_ttl_minutes=5
        )
    
    @pytest.fixture
    def manager_no_gemini(self, temp_storage):
        """Create reference manager without Gemini client."""
        return ReferenceManager(storage=temp_storage)
    
    # === CRUD Operations Tests ===
    
    def test_create_reference_character(self, manager):
        """Test creating a character reference."""
        char = manager.create_reference(
            "character",
            "Test Hero",
            "A brave hero",
            poses=["standing"],
            expressions=["happy"]
        )
        
        assert char.name == "Test Hero"
        assert char.description == "A brave hero"
        assert isinstance(char, CharacterReference)
        
        # Verify saved to storage
        loaded = manager.storage.load_reference("character", "Test Hero")
        assert loaded.name == "Test Hero"
    
    def test_create_reference_location(self, manager):
        """Test creating a location reference."""
        loc = manager.create_reference(
            "location",
            "Test Forest",
            "A mystical forest",
            location_type="exterior"
        )
        
        assert loc.name == "Test Forest"
        assert isinstance(loc, LocationReference)
    
    def test_create_reference_invalid_name(self, manager):
        """Test creating reference with invalid name."""
        with pytest.raises(ValueError, match="Invalid name format"):
            manager.create_reference(
                "character",
                "123InvalidName",  # Starts with number
                "Description"
            )
    
    def test_create_reference_already_exists(self, manager):
        """Test creating reference that already exists."""
        manager.create_reference("character", "Hero", "A hero")
        
        with pytest.raises(ValueError, match="Reference already exists"):
            manager.create_reference("character", "Hero", "Another hero")
    
    def test_get_reference(self, manager):
        """Test getting a reference."""
        # Create reference
        manager.create_reference("character", "Hero", "A hero")
        
        # Get reference
        char = manager.get_reference("character", "Hero")
        assert char is not None
        assert char.name == "Hero"
    
    def test_get_reference_not_found(self, manager):
        """Test getting non-existent reference."""
        ref = manager.get_reference("character", "NonExistent")
        assert ref is None
    
    def test_get_reference_with_cache(self, manager):
        """Test cache functionality."""
        # Create reference
        manager.create_reference("character", "Hero", "A hero")
        
        # First get - loads from storage
        char1 = manager.get_reference("character", "Hero")
        
        # Second get - should come from cache
        char2 = manager.get_reference("character", "Hero")
        
        assert char1 is char2  # Same object from cache
        assert ("character", "Hero") in manager.cache
    
    def test_update_reference(self, manager):
        """Test updating a reference."""
        # Create reference
        manager.create_reference("character", "Hero", "A hero")
        
        # Update reference
        updated = manager.update_reference(
            "character",
            "Hero",
            {"description": "An updated hero", "age_range": "young adult"}
        )
        
        assert updated.description == "An updated hero"
        assert updated.age_range == "young adult"
        
        # Verify saved
        loaded = manager.storage.load_reference("character", "Hero")
        assert loaded.description == "An updated hero"
    
    def test_update_reference_not_found(self, manager):
        """Test updating non-existent reference."""
        with pytest.raises(ReferenceNotFoundError):
            manager.update_reference("character", "NonExistent", {})
    
    def test_delete_reference(self, manager):
        """Test deleting a reference."""
        # Create reference
        manager.create_reference("character", "Hero", "A hero")
        
        # Delete reference
        manager.delete_reference("character", "Hero")
        
        # Verify deleted
        ref = manager.get_reference("character", "Hero")
        assert ref is None
    
    def test_list_references(self, manager):
        """Test listing references."""
        # Create multiple references
        manager.create_reference("character", "Hero", "A hero")
        manager.create_reference("character", "Villain", "A villain")
        manager.create_reference("location", "Forest", "A forest")
        
        # List all
        refs = manager.list_references()
        assert len(refs["character"]) == 2
        assert "Hero" in refs["character"]
        assert "Villain" in refs["character"]
        assert len(refs["location"]) == 1
        assert "Forest" in refs["location"]
        
        # List specific type
        chars = manager.list_references("character")
        assert len(chars["character"]) == 2
        assert "location" not in chars
    
    def test_list_references_with_tags(self, manager):
        """Test listing references filtered by tags."""
        # Create references with tags
        manager.create_reference(
            "character", "Hero", "A hero", tags=["protagonist", "warrior"]
        )
        manager.create_reference(
            "character", "Villain", "A villain", tags=["antagonist"]
        )
        manager.create_reference(
            "character", "Sidekick", "A sidekick", tags=["protagonist", "comic"]
        )
        
        # Filter by tags
        protagonists = manager.list_references(tags=["protagonist"])
        assert len(protagonists["character"]) == 2
        assert "Hero" in protagonists["character"]
        assert "Sidekick" in protagonists["character"]
        assert "Villain" not in protagonists["character"]
    
    # === Generation Operations Tests ===
    
    @pytest.mark.asyncio
    async def test_generate_character(self, manager):
        """Test generating a character reference."""
        # Mock generator
        manager.character_generator.generate_reference = AsyncMock(
            return_value=CharacterReference(
                name="Generated Hero",
                description="A generated hero",
                poses=["standing"],
                expressions=["happy"]
            )
        )
        
        # Generate character
        char = await manager.generate_character(
            "Generated Hero",
            "A generated hero",
            poses=["standing"],
            expressions=["happy"]
        )
        
        assert char.name == "Generated Hero"
        assert "standing" in char.poses
        assert "happy" in char.expressions
    
    @pytest.mark.asyncio
    async def test_generate_character_no_client(self, manager_no_gemini):
        """Test generating character without Gemini client."""
        with pytest.raises(ValueError, match="generator not available"):
            await manager_no_gemini.generate_character("Hero", "A hero")
    
    @pytest.mark.asyncio
    async def test_generate_with_style_guide(self, manager):
        """Test generation with style guide."""
        # Create style guide
        style = manager.create_reference(
            "styleguide",
            "Comic Style",
            "Comic book style",
            art_style="comic-book"
        )
        
        # Mock generator
        manager.character_generator.generate_reference = AsyncMock(
            return_value=CharacterReference(
                name="Styled Hero",
                description="A hero with style"
            )
        )
        
        # Generate with style
        char = await manager.generate_character(
            "Styled Hero",
            "A hero with style",
            style_guide="Comic Style"
        )
        
        # Verify style was passed
        call_args = manager.character_generator.generate_reference.call_args
        assert call_args.kwargs.get("style_guide") is not None
    
    # === Lookup and Matching Tests ===
    
    def test_find_references_in_text(self, manager):
        """Test finding references in text."""
        # Create references
        manager.create_reference("character", "Alex the Hero", "A hero")
        manager.create_reference("location", "Enchanted Forest", "A forest")
        manager.create_reference("object", "Magic Sword", "A sword")
        
        # Test text
        text = "Alex entered the Enchanted Forest carrying the Magic Sword."
        
        # Find references
        found = manager.find_references_in_text(text)
        
        assert "Alex the Hero" in found["character"]
        assert "Enchanted Forest" in found["location"]
        assert "Magic Sword" in found["object"]
    
    def test_find_references_partial_match(self, manager):
        """Test partial name matching."""
        manager.create_reference("character", "Alex the Hero", "A hero")
        
        text = "Alex walked through the forest."
        found = manager.find_references_in_text(text)
        
        assert "Alex the Hero" in found["character"]
    
    def test_get_character_images(self, manager):
        """Test getting character images."""
        # Create character with images
        char = manager.create_reference(
            "character",
            "Hero",
            "A hero"
        )
        
        # Save image and get the actual filename returned
        filename = manager.storage.save_reference_image(
            "character", "Hero", "standing", b"image_data"
        )
        
        # Update character with the actual filename
        char.images = {"standing": filename}
        manager.storage.save_reference(char)
        
        # Get images
        images = manager.get_character_images(["Hero"])
        assert "Hero" in images
        assert "standing" in images["Hero"]
        assert images["Hero"]["standing"] == b"image_data"
    
    # === Cache Management Tests ===
    
    def test_cache_eviction(self, manager):
        """Test cache eviction when size limit reached."""
        manager.cache_size = 3
        
        # Create more references than cache size
        for i in range(5):
            manager.create_reference("character", f"Hero{i}", f"Hero {i}")
        
        # Cache should only have last 3
        assert len(manager.cache) <= 3
    
    def test_cache_ttl(self, manager):
        """Test cache TTL expiration."""
        manager.cache_ttl = timedelta(seconds=0.1)
        
        # Create reference
        manager.create_reference("character", "Hero", "A hero")
        
        # Get reference (cached)
        ref1 = manager.get_reference("character", "Hero")
        assert ("character", "Hero") in manager.cache
        
        # Wait for TTL to expire
        import time
        time.sleep(0.2)
        
        # Get again - should reload from storage
        ref2 = manager.get_reference("character", "Hero")
        # Cache should be refreshed
        assert manager.cache[("character", "Hero")].reference == ref2
    
    def test_clear_cache(self, manager):
        """Test clearing cache."""
        # Create and cache references
        manager.create_reference("character", "Hero", "A hero")
        manager.create_reference("location", "Forest", "A forest")
        
        assert len(manager.cache) == 2
        
        # Clear cache
        manager.clear_cache()
        assert len(manager.cache) == 0
    
    # === Validation and Cleanup Tests ===
    
    def test_validate_name_patterns(self, manager):
        """Test name validation patterns."""
        # Valid names
        assert manager._validate_name("character", "Hero")
        assert manager._validate_name("character", "Hero_2")
        assert manager._validate_name("character", "Alex the Hero")
        
        # Invalid names
        assert not manager._validate_name("character", "123Hero")  # Starts with number
        assert not manager._validate_name("character", "@Hero")    # Special char
    
    def test_validate_all_references(self, manager):
        """Test validating all references."""
        # Create valid reference
        manager.create_reference("character", "Hero", "A hero")
        
        # Test validation - should pass for valid references
        errors = manager.validate_all_references()
        
        # Should have no errors for valid reference
        assert "character/Hero" not in errors
        assert len(errors) == 0
    
    def test_cleanup_unused_references(self, manager):
        """Test cleaning up unused references."""
        # Create old reference
        old_char = manager.create_reference("character", "OldHero", "An old hero")
        old_char.updated_at = datetime.now() - timedelta(days=40)
        manager.storage.save_reference(old_char)
        
        # Create recent reference
        manager.create_reference("character", "NewHero", "A new hero")
        
        # Cleanup old references
        removed = manager.cleanup_unused_references(days_unused=30)
        
        assert len(removed) == 1
        assert ("character", "OldHero") in removed
        
        # Verify old reference deleted
        assert manager.get_reference("character", "OldHero") is None
        # New reference still exists
        assert manager.get_reference("character", "NewHero") is not None
    
    def test_get_statistics(self, manager):
        """Test getting manager statistics."""
        # Create some references
        manager.create_reference("character", "Hero", "A hero")
        manager.create_reference("location", "Forest", "A forest")
        
        # Get some references to populate cache
        manager.get_reference("character", "Hero")
        manager.get_reference("character", "Hero")  # Cache hit
        
        # Get statistics
        stats = manager.get_statistics()
        
        assert stats["total_references"] == 2
        assert stats["references_by_type"]["character"] == 1
        assert stats["references_by_type"]["location"] == 1
        assert stats["cache_size"] == 2
        assert "storage_info" in stats


class TestReferenceCache:
    """Test ReferenceCache class."""
    
    def test_cache_touch(self):
        """Test cache touch functionality."""
        ref = CharacterReference(name="Hero", description="A hero")
        cache = ReferenceCache(
            reference=ref,
            last_accessed=datetime.now()
        )
        
        original_time = cache.last_accessed
        original_count = cache.access_count
        
        # Touch cache
        import time
        time.sleep(0.01)
        cache.touch()
        
        assert cache.last_accessed > original_time
        assert cache.access_count == original_count + 1