"""Unit tests for reference models."""

import pytest
from datetime import datetime
from src.references.models import (
    BaseReference,
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
    create_reference_from_dict,
)


class TestCharacterReference:
    """Test CharacterReference model."""
    
    def test_character_reference_creation(self):
        """Test basic character reference creation."""
        char = CharacterReference(
            name="Test Hero",
            description="A brave adventurer",
            poses=["standing", "running"],
            expressions=["happy", "determined"]
        )
        
        assert char.name == "Test Hero"
        assert char.description == "A brave adventurer"
        assert char.poses == ["standing", "running"]
        assert char.expressions == ["happy", "determined"]
        assert isinstance(char.created_at, datetime)
        assert isinstance(char.updated_at, datetime)
    
    def test_character_validation_empty_name(self):
        """Test validation fails with empty name."""
        with pytest.raises(ValueError, match="Reference name cannot be empty"):
            CharacterReference(name="", description="A hero")
    
    def test_character_validation_empty_description(self):
        """Test validation fails with empty description."""
        with pytest.raises(ValueError, match="Reference description cannot be empty"):
            CharacterReference(name="Hero", description="")
    
    def test_character_validation_invalid_name_chars(self):
        """Test validation fails with invalid filename characters."""
        with pytest.raises(ValueError, match="Reference name contains invalid characters"):
            CharacterReference(name="Hero/Villain", description="A character")
    
    def test_character_image_key_generation(self):
        """Test image key generation."""
        char = CharacterReference(name="Hero", description="A hero")
        
        key = char.get_image_key("standing", "happy", "armor")
        assert key == "standing_happy_armor"
        
        # Test default values
        key_default = char.get_image_key("running")
        assert key_default == "running_neutral_default"
    
    def test_character_image_management(self):
        """Test image management methods."""
        char = CharacterReference(name="Hero", description="A hero")
        
        # Initially no images
        assert not char.has_image("standing")
        
        # Add image
        char.add_image("standing", "hero_standing.png")
        assert char.has_image("standing")
        assert char.images["standing_neutral_default"] == "hero_standing.png"
        
        # Add image with specific expression
        char.add_image("running", "hero_running_happy.png", "happy")
        assert char.has_image("running", "happy")
        assert char.images["running_happy_default"] == "hero_running_happy.png"
    
    def test_character_to_dict(self):
        """Test dictionary serialization."""
        char = CharacterReference(
            name="Hero",
            description="A hero",
            poses=["standing"],
            expressions=["happy"],
            outfits=["armor"],
            age_range="young adult",
            physical_traits=["tall", "strong"],
            personality_traits=["brave", "kind"]
        )
        
        data = char.to_dict()
        assert data["name"] == "Hero"
        assert data["type"] == "character"
        assert data["poses"] == ["standing"]
        assert data["expressions"] == ["happy"]
        assert data["outfits"] == ["armor"]
        assert data["age_range"] == "young adult"
        assert data["physical_traits"] == ["tall", "strong"]
        assert data["personality_traits"] == ["brave", "kind"]
    
    def test_character_from_dict(self):
        """Test creating character from dictionary."""
        data = {
            "name": "Hero",
            "description": "A hero",
            "poses": ["standing"],
            "expressions": ["happy"],
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-01T12:00:00",
            "type": "character"
        }
        
        char = CharacterReference.from_dict(data)
        assert char.name == "Hero"
        assert char.description == "A hero"
        assert char.poses == ["standing"]
        assert char.expressions == ["happy"]
        assert isinstance(char.created_at, datetime)


class TestLocationReference:
    """Test LocationReference model."""
    
    def test_location_reference_creation(self):
        """Test basic location reference creation."""
        location = LocationReference(
            name="Enchanted Forest",
            description="A mystical woodland",
            location_type="exterior",
            angles=["wide-shot", "close-up"],
            lighting_conditions=["dawn", "dusk"]
        )
        
        assert location.name == "Enchanted Forest"
        assert location.description == "A mystical woodland"
        assert location.location_type == "exterior"
        assert location.angles == ["wide-shot", "close-up"]
        assert location.lighting_conditions == ["dawn", "dusk"]
    
    def test_location_validation_invalid_type(self):
        """Test validation fails with invalid location type."""
        with pytest.raises(ValueError, match="Invalid location type"):
            LocationReference(
                name="Forest",
                description="A forest",
                location_type="invalid_type"
            )
    
    def test_location_image_management(self):
        """Test location image management."""
        location = LocationReference(name="Forest", description="A forest")
        
        # Add image
        location.add_image("wide-shot", "forest_wide.png", "dawn", "morning")
        assert location.has_image("wide-shot", "dawn", "morning")
        assert location.images["wide-shot_dawn_morning"] == "forest_wide.png"
    
    def test_location_to_dict(self):
        """Test dictionary serialization."""
        location = LocationReference(
            name="Castle",
            description="A medieval castle",
            location_type="exterior",
            angles=["aerial"],
            key_features=["towers", "moat"]
        )
        
        data = location.to_dict()
        assert data["name"] == "Castle"
        assert data["type"] == "location"
        assert data["location_type"] == "exterior"
        assert data["key_features"] == ["towers", "moat"]


class TestObjectReference:
    """Test ObjectReference model."""
    
    def test_object_reference_creation(self):
        """Test basic object reference creation."""
        obj = ObjectReference(
            name="Magic Sword",
            description="An enchanted blade",
            object_type="weapon",
            views=["front", "profile"],
            states=["new", "glowing"]
        )
        
        assert obj.name == "Magic Sword"
        assert obj.description == "An enchanted blade"
        assert obj.object_type == "weapon"
        assert obj.views == ["front", "profile"]
        assert obj.states == ["new", "glowing"]
    
    def test_object_validation_invalid_size(self):
        """Test validation fails with invalid size category."""
        with pytest.raises(ValueError, match="Invalid size category"):
            ObjectReference(
                name="Sword",
                description="A sword",
                size_category="gigantic"
            )
    
    def test_object_image_management(self):
        """Test object image management."""
        obj = ObjectReference(name="Sword", description="A sword")
        
        # Add image
        obj.add_image("front", "sword_front.png", "glowing")
        assert obj.has_image("front", "glowing")
        assert obj.images["front_glowing"] == "sword_front.png"
    
    def test_object_to_dict(self):
        """Test dictionary serialization."""
        obj = ObjectReference(
            name="Shield",
            description="A protective shield",
            object_type="armor",
            size_category="medium",
            materials=["metal", "leather"],
            colors=["silver", "brown"]
        )
        
        data = obj.to_dict()
        assert data["name"] == "Shield"
        assert data["type"] == "object"
        assert data["object_type"] == "armor"
        assert data["size_category"] == "medium"
        assert data["materials"] == ["metal", "leather"]
        assert data["colors"] == ["silver", "brown"]


class TestStyleGuide:
    """Test StyleGuide model."""
    
    def test_style_guide_creation(self):
        """Test basic style guide creation."""
        style = StyleGuide(
            name="Fantasy Style",
            description="Medieval fantasy art style",
            art_style="realistic",
            color_palette=["#8B4513", "#228B22", "#4169E1"],
            lighting_style="dramatic"
        )
        
        assert style.name == "Fantasy Style"
        assert style.description == "Medieval fantasy art style"
        assert style.art_style == "realistic"
        assert style.color_palette == ["#8B4513", "#228B22", "#4169E1"]
        assert style.lighting_style == "dramatic"
    
    def test_style_guide_color_validation(self):
        """Test color validation in style guide."""
        with pytest.raises(ValueError, match="Invalid color code"):
            StyleGuide(
                name="Style",
                description="A style",
                color_palette=["invalid_color"]
            )
    
    def test_style_guide_add_color(self):
        """Test adding colors to palette."""
        style = StyleGuide(name="Style", description="A style")
        
        # Add valid color
        style.add_color("#FF0000")
        assert "#FF0000" in style.color_palette
        
        # Add color without hash
        style.add_color("00FF00")
        assert "#00FF00" in style.color_palette
        
        # Try to add invalid color
        with pytest.raises(ValueError, match="Invalid color code"):
            style.add_color("invalid")
    
    def test_style_guide_remove_color(self):
        """Test removing colors from palette."""
        style = StyleGuide(
            name="Style",
            description="A style",
            color_palette=["#FF0000", "#00FF00"]
        )
        
        style.remove_color("#FF0000")
        assert "#FF0000" not in style.color_palette
        assert "#00FF00" in style.color_palette
    
    def test_style_guide_to_dict(self):
        """Test dictionary serialization."""
        style = StyleGuide(
            name="Comic Style",
            description="Classic comic book style",
            art_style="comic-book",
            color_mood="vibrant",
            line_style="bold"
        )
        
        data = style.to_dict()
        assert data["name"] == "Comic Style"
        assert data["type"] == "styleguide"
        assert data["art_style"] == "comic-book"
        assert data["color_mood"] == "vibrant"
        assert data["line_style"] == "bold"


class TestReferenceFactory:
    """Test reference creation factory function."""
    
    def test_create_character_from_dict(self):
        """Test creating character reference from dict."""
        data = {
            "name": "Hero",
            "description": "A hero",
            "type": "character",
            "poses": ["standing"]
        }
        
        ref = create_reference_from_dict(data)
        assert isinstance(ref, CharacterReference)
        assert ref.name == "Hero"
        assert ref.poses == ["standing"]
    
    def test_create_location_from_dict(self):
        """Test creating location reference from dict."""
        data = {
            "name": "Forest",
            "description": "A forest",
            "type": "location",
            "location_type": "exterior"
        }
        
        ref = create_reference_from_dict(data)
        assert isinstance(ref, LocationReference)
        assert ref.name == "Forest"
        assert ref.location_type == "exterior"
    
    def test_create_object_from_dict(self):
        """Test creating object reference from dict."""
        data = {
            "name": "Sword",
            "description": "A sword",
            "type": "object",
            "object_type": "weapon"
        }
        
        ref = create_reference_from_dict(data)
        assert isinstance(ref, ObjectReference)
        assert ref.name == "Sword"
        assert ref.object_type == "weapon"
    
    def test_create_style_guide_from_dict(self):
        """Test creating style guide from dict."""
        data = {
            "name": "Style",
            "description": "A style",
            "type": "styleguide",
            "art_style": "realistic"
        }
        
        ref = create_reference_from_dict(data)
        assert isinstance(ref, StyleGuide)
        assert ref.name == "Style"
        assert ref.art_style == "realistic"
    
    def test_create_unknown_type_fails(self):
        """Test creating reference with unknown type fails."""
        data = {
            "name": "Unknown",
            "description": "Unknown type",
            "type": "unknown"
        }
        
        with pytest.raises(ValueError, match="Unknown reference type"):
            create_reference_from_dict(data)


class TestBaseReferenceCommon:
    """Test common BaseReference functionality."""
    
    def test_update_timestamp(self):
        """Test timestamp update functionality."""
        char = CharacterReference(name="Hero", description="A hero")
        original_time = char.updated_at
        
        # Wait a bit to ensure timestamp changes
        import time
        time.sleep(0.001)
        
        char.update_timestamp()
        assert char.updated_at > original_time
    
    def test_tags_functionality(self):
        """Test tags functionality."""
        char = CharacterReference(
            name="Hero",
            description="A hero",
            tags=["protagonist", "warrior"]
        )
        
        assert "protagonist" in char.tags
        assert "warrior" in char.tags
        
        # Test in serialization
        data = char.to_dict()
        assert data["tags"] == ["protagonist", "warrior"]