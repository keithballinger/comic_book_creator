"""Unit tests for reference storage system."""

import pytest
import tempfile
import shutil
import json
import threading
import time
from pathlib import Path

from src.references.models import (
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
)
from src.references.storage import (
    ReferenceStorage,
    ReferenceStorageError,
    ReferenceNotFoundError,
)


class TestReferenceStorage:
    """Test ReferenceStorage class."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing."""
        temp_dir = tempfile.mkdtemp()
        storage = ReferenceStorage(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_character(self):
        """Create sample character for testing."""
        return CharacterReference(
            name="Test Hero",
            description="A brave adventurer",
            poses=["standing", "running"],
            expressions=["happy", "determined"]
        )
    
    @pytest.fixture
    def sample_location(self):
        """Create sample location for testing."""
        return LocationReference(
            name="Enchanted Forest",
            description="A mystical woodland",
            location_type="exterior",
            angles=["wide-shot", "close-up"]
        )
    
    def test_storage_initialization(self, temp_storage):
        """Test storage initialization creates directory structure."""
        assert temp_storage.base_path.exists()
        assert (temp_storage.base_path / "characters").exists()
        assert (temp_storage.base_path / "locations").exists()
        assert (temp_storage.base_path / "objects").exists()
        assert (temp_storage.base_path / "styles").exists()
    
    def test_save_and_load_character(self, temp_storage, sample_character):
        """Test saving and loading character reference."""
        # Save character
        temp_storage.save_reference(sample_character)
        
        # Verify file exists
        assert temp_storage.exists("character", "Test Hero")
        
        # Load character
        loaded_char = temp_storage.load_reference("character", "Test Hero")
        
        # Verify loaded data
        assert loaded_char.name == sample_character.name
        assert loaded_char.description == sample_character.description
        assert loaded_char.poses == sample_character.poses
        assert loaded_char.expressions == sample_character.expressions
        assert isinstance(loaded_char, CharacterReference)
    
    def test_save_and_load_location(self, temp_storage, sample_location):
        """Test saving and loading location reference."""
        # Save location
        temp_storage.save_reference(sample_location)
        
        # Load location
        loaded_location = temp_storage.load_reference("location", "Enchanted Forest")
        
        # Verify loaded data
        assert loaded_location.name == sample_location.name
        assert loaded_location.description == sample_location.description
        assert loaded_location.location_type == sample_location.location_type
        assert isinstance(loaded_location, LocationReference)
    
    def test_save_object_reference(self, temp_storage):
        """Test saving and loading object reference."""
        obj = ObjectReference(
            name="Magic Sword",
            description="An enchanted blade",
            object_type="weapon",
            size_category="medium"
        )
        
        temp_storage.save_reference(obj)
        loaded_obj = temp_storage.load_reference("object", "Magic Sword")
        
        assert loaded_obj.name == obj.name
        assert loaded_obj.object_type == obj.object_type
        assert loaded_obj.size_category == obj.size_category
    
    def test_save_style_guide(self, temp_storage):
        """Test saving and loading style guide."""
        style = StyleGuide(
            name="Fantasy Style",
            description="Medieval fantasy art style",
            art_style="realistic",
            color_palette=["#8B4513", "#228B22"]
        )
        
        temp_storage.save_reference(style)
        loaded_style = temp_storage.load_reference("styleguide", "Fantasy Style")
        
        assert loaded_style.name == style.name
        assert loaded_style.art_style == style.art_style
        assert loaded_style.color_palette == style.color_palette
    
    def test_filename_sanitization(self, temp_storage):
        """Test filename sanitization for edge cases."""
        # Test with spaces and underscores (valid characters)
        char = CharacterReference(
            name="Hero with Spaces",
            description="A character with spaces in name"
        )
        
        # Should save without error
        temp_storage.save_reference(char)
        
        # Should be able to load
        loaded = temp_storage.load_reference("character", "Hero with Spaces")
        assert loaded.name == char.name
        
        # Test internal sanitization of filenames
        sanitized = temp_storage._sanitize_filename("Hero/Villain: Battle")
        assert "/" not in sanitized
        assert ":" not in sanitized
        assert sanitized == "Hero_Villain_ Battle"
    
    def test_load_nonexistent_reference(self, temp_storage):
        """Test loading non-existent reference raises error."""
        with pytest.raises(ReferenceNotFoundError):
            temp_storage.load_reference("character", "NonExistent")
    
    def test_list_references_empty(self, temp_storage):
        """Test listing references when storage is empty."""
        refs = temp_storage.list_references()
        
        assert "character" in refs
        assert "location" in refs
        assert "object" in refs
        assert "styleguide" in refs
        assert all(len(ref_list) == 0 for ref_list in refs.values())
    
    def test_list_references_with_data(self, temp_storage, sample_character, sample_location):
        """Test listing references with data."""
        temp_storage.save_reference(sample_character)
        temp_storage.save_reference(sample_location)
        
        refs = temp_storage.list_references()
        
        assert "Test Hero" in refs["character"]
        assert "Enchanted Forest" in refs["location"]
        assert len(refs["character"]) == 1
        assert len(refs["location"]) == 1
        assert len(refs["object"]) == 0
        assert len(refs["styleguide"]) == 0
    
    def test_list_specific_type(self, temp_storage, sample_character, sample_location):
        """Test listing specific reference type."""
        temp_storage.save_reference(sample_character)
        temp_storage.save_reference(sample_location)
        
        char_refs = temp_storage.list_references("character")
        assert "Test Hero" in char_refs["character"]
        assert "location" not in char_refs  # Only character type requested
    
    def test_exists_functionality(self, temp_storage, sample_character):
        """Test exists() method."""
        # Initially doesn't exist
        assert not temp_storage.exists("character", "Test Hero")
        
        # Save and check exists
        temp_storage.save_reference(sample_character)
        assert temp_storage.exists("character", "Test Hero")
        
        # Check non-existent
        assert not temp_storage.exists("character", "NonExistent")
        
        # Check invalid type
        assert not temp_storage.exists("invalid_type", "Test Hero")
    
    def test_delete_reference(self, temp_storage, sample_character):
        """Test deleting reference."""
        # Save reference
        temp_storage.save_reference(sample_character)
        assert temp_storage.exists("character", "Test Hero")
        
        # Delete reference
        temp_storage.delete_reference("character", "Test Hero")
        assert not temp_storage.exists("character", "Test Hero")
        
        # Verify file is gone
        refs = temp_storage.list_references("character")
        assert "Test Hero" not in refs["character"]
    
    def test_delete_nonexistent_reference(self, temp_storage):
        """Test deleting non-existent reference raises error."""
        with pytest.raises(ReferenceNotFoundError):
            temp_storage.delete_reference("character", "NonExistent")
    
    def test_image_operations(self, temp_storage, sample_character):
        """Test saving and loading reference images."""
        # Save reference first
        temp_storage.save_reference(sample_character)
        
        # Test image data
        image_data = b"fake_image_data_for_testing"
        
        # Save image
        filename = temp_storage.save_reference_image(
            "character", "Test Hero", "standing_happy", image_data, "png"
        )
        assert filename == "standing_happy.png"
        
        # Load image
        loaded_data = temp_storage.load_reference_image(
            "character", "Test Hero", filename
        )
        assert loaded_data == image_data
        
        # List images
        images = temp_storage.list_reference_images("character", "Test Hero")
        assert filename in images
    
    def test_load_nonexistent_image(self, temp_storage, sample_character):
        """Test loading non-existent image raises error."""
        temp_storage.save_reference(sample_character)
        
        with pytest.raises(ReferenceNotFoundError):
            temp_storage.load_reference_image(
                "character", "Test Hero", "nonexistent.png"
            )
    
    def test_list_images_empty(self, temp_storage, sample_character):
        """Test listing images when none exist."""
        temp_storage.save_reference(sample_character)
        
        images = temp_storage.list_reference_images("character", "Test Hero")
        assert images == []
    
    def test_storage_info(self, temp_storage, sample_character, sample_location):
        """Test storage information gathering."""
        # Initially empty
        info = temp_storage.get_storage_info()
        assert info["total_references"] == 0
        assert info["total_images"] == 0
        
        # Add some references
        temp_storage.save_reference(sample_character)
        temp_storage.save_reference(sample_location)
        
        # Add an image
        temp_storage.save_reference_image(
            "character", "Test Hero", "test_image", b"test_data", "png"
        )
        
        # Check updated info
        info = temp_storage.get_storage_info()
        assert info["total_references"] == 2
        assert info["references_by_type"]["character"] == 1
        assert info["references_by_type"]["location"] == 1
        assert info["total_images"] == 1
        assert info["storage_size_mb"] >= 0
    
    def test_cleanup_orphaned_images(self, temp_storage, sample_character):
        """Test cleanup of orphaned image directories."""
        # Save character and image
        temp_storage.save_reference(sample_character)
        temp_storage.save_reference_image(
            "character", "Test Hero", "test", b"test", "png"
        )
        
        # Manually delete the reference file (creating orphan)
        ref_path = temp_storage._get_reference_path("character", "Test Hero")
        ref_path.unlink()
        
        # Run cleanup
        removed = temp_storage.cleanup_orphaned_images()
        assert removed == 1
        
        # Verify image directory is gone
        images = temp_storage.list_reference_images("character", "Test Hero")
        assert len(images) == 0
    
    def test_invalid_reference_type(self, temp_storage):
        """Test operations with invalid reference type."""
        with pytest.raises(ValueError, match="Invalid reference type"):
            temp_storage._get_reference_path("invalid_type", "test")
    
    def test_concurrent_access(self, temp_storage, sample_character):
        """Test concurrent access to storage."""
        results = []
        errors = []
        
        def save_and_load(thread_id):
            try:
                # Create unique character for this thread
                char = CharacterReference(
                    name=f"Hero_{thread_id}",
                    description=f"Hero for thread {thread_id}"
                )
                
                # Save
                temp_storage.save_reference(char)
                
                # Load
                loaded = temp_storage.load_reference("character", f"Hero_{thread_id}")
                results.append((thread_id, loaded.name))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=save_and_load, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        
        # Verify all characters were saved
        refs = temp_storage.list_references("character")
        for i in range(5):
            assert f"Hero_{i}" in refs["character"]


class TestStorageErrorHandling:
    """Test error handling in storage operations."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing."""
        temp_dir = tempfile.mkdtemp()
        storage = ReferenceStorage(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_corrupted_json_handling(self, temp_storage):
        """Test handling of corrupted JSON files."""
        # Create a corrupted JSON file
        ref_path = temp_storage._get_reference_path("character", "Corrupted")
        ref_path.parent.mkdir(exist_ok=True)
        
        with open(ref_path, 'w') as f:
            f.write("{invalid json content")
        
        # Should raise ReferenceStorageError for corrupted JSON
        with pytest.raises(ReferenceStorageError, match="Invalid reference file format"):
            temp_storage.load_reference("character", "Corrupted")
    
    def test_permission_errors(self, temp_storage):
        """Test handling of permission errors."""
        # This test might not work on all systems, so we'll skip if needed
        try:
            # Make directory read-only
            char_dir = temp_storage._type_dirs["character"]
            char_dir.chmod(0o444)
            
            char = CharacterReference(name="Test", description="Test")
            
            with pytest.raises(ReferenceStorageError):
                temp_storage.save_reference(char)
        
        except (OSError, PermissionError):
            # Skip test if we can't modify permissions
            pytest.skip("Cannot test permission errors on this system")
        finally:
            # Restore permissions for cleanup
            try:
                char_dir.chmod(0o755)
            except:
                pass