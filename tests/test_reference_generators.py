"""Unit tests for reference generators."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from io import BytesIO
from PIL import Image
import tempfile
import shutil

from src.references.generators import (
    GenerationConfig,
    BaseReferenceGenerator,
    CharacterReferenceGenerator,
    LocationReferenceGenerator,
    ObjectReferenceGenerator,
    StyleGuideGenerator,
)
from src.references.models import (
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
)
from src.references.storage import ReferenceStorage
from src.api import GeminiClient


class TestGenerationConfig:
    """Test GenerationConfig class."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = GenerationConfig()
        
        assert config.image_width == 1024
        assert config.image_height == 1024
        assert config.quality == "high"
        assert config.style_consistency == 0.8
        assert config.batch_size == 3
        assert config.retry_attempts == 3
        assert config.timeout_seconds == 60
    
    def test_quality_settings(self):
        """Test quality-specific settings."""
        config = GenerationConfig(quality="high")
        settings = config.get_quality_settings()
        assert settings["steps"] == 50
        assert settings["cfg_scale"] == 7.5
        
        config.quality = "medium"
        settings = config.get_quality_settings()
        assert settings["steps"] == 30
        assert settings["cfg_scale"] == 7.0
        
        config.quality = "low"
        settings = config.get_quality_settings()
        assert settings["steps"] == 20
        assert settings["cfg_scale"] == 6.5


class TestBaseReferenceGenerator:
    """Test BaseReferenceGenerator functionality."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client."""
        client = Mock(spec=GeminiClient)
        client.generate_image = AsyncMock()
        return client
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        temp_dir = tempfile.mkdtemp()
        storage = ReferenceStorage(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def test_generator(self, mock_gemini_client, temp_storage):
        """Create test generator instance."""
        # Create a concrete implementation for testing
        class TestGenerator(BaseReferenceGenerator):
            async def generate_reference(self, name, description, **kwargs):
                return CharacterReference(name=name, description=description)
            
            def _build_generation_prompt(self, description, specific_details):
                return f"Generate: {description}"
        
        return TestGenerator(mock_gemini_client, temp_storage)
    
    @pytest.mark.asyncio
    async def test_generate_single_image(self, test_generator, mock_gemini_client):
        """Test single image generation."""
        # Mock response
        test_image_data = b"test_image_data"
        mock_gemini_client.generate_image.return_value = test_image_data
        
        # Generate image
        result = await test_generator._generate_single_image("Test prompt")
        
        # Verify
        assert result == test_image_data
        mock_gemini_client.generate_image.assert_called_once()
        args = mock_gemini_client.generate_image.call_args
        assert "Test prompt" in str(args)
    
    @pytest.mark.asyncio
    async def test_generate_single_image_with_retry(self, test_generator, mock_gemini_client):
        """Test image generation with retry on failure."""
        # Mock first failure, then success
        mock_gemini_client.generate_image.side_effect = [
            Exception("API error"),
            b"test_image_data"
        ]
        
        # Generate image
        result = await test_generator._generate_single_image("Test prompt")
        
        # Verify retry worked
        assert result == b"test_image_data"
        assert mock_gemini_client.generate_image.call_count == 2
    
    @pytest.mark.asyncio
    async def test_generate_batch_images(self, test_generator, mock_gemini_client):
        """Test batch image generation."""
        # Mock responses
        mock_gemini_client.generate_image.side_effect = [
            b"image1", b"image2", b"image3"
        ]
        
        # Generate batch
        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        results = await test_generator._generate_batch_images(prompts)
        
        # Verify
        assert len(results) == 3
        assert results == [b"image1", b"image2", b"image3"]
        assert mock_gemini_client.generate_image.call_count == 3
    
    def test_create_consistency_prompt(self, test_generator):
        """Test consistency prompt creation."""
        prompt = test_generator._create_consistency_prompt("test character")
        
        assert "CONSISTENCY REQUIREMENTS" in prompt
        assert "EXACT same visual appearance" in prompt
        assert "test character" in prompt
    
    def test_add_style_context(self, test_generator):
        """Test adding style context to prompt."""
        style = StyleGuide(
            name="Test Style",
            description="Test style guide",
            art_style="comic-book",
            color_palette=["#FF0000", "#00FF00"],
            line_style="bold",
            lighting_style="dramatic"
        )
        
        base_prompt = "Generate image"
        result = test_generator._add_style_context(base_prompt, style)
        
        assert "STYLE GUIDE" in result
        assert "comic-book" in result
        assert "#FF0000" in result
        assert "bold" in result
    
    @pytest.mark.asyncio
    async def test_save_reference_with_images(self, test_generator, temp_storage):
        """Test saving reference with images."""
        # Create reference
        char = CharacterReference(
            name="Test Character",
            description="A test character"
        )
        
        # Create test images
        images = {
            "standing": b"standing_image",
            "running": b"running_image"
        }
        
        # Save
        await test_generator.save_reference_with_images(char, images)
        
        # Verify reference saved
        loaded = temp_storage.load_reference("character", "Test Character")
        assert loaded.name == "Test Character"
        
        # Verify images saved
        image_files = temp_storage.list_reference_images("character", "Test Character")
        assert len(image_files) == 2


class TestCharacterReferenceGenerator:
    """Test CharacterReferenceGenerator."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client."""
        client = Mock(spec=GeminiClient)
        # Create a small valid PNG image
        img = Image.new('RGB', (10, 10), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        # Return valid image data
        client.generate_image = AsyncMock(return_value=img_bytes.getvalue())
        return client
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        temp_dir = tempfile.mkdtemp()
        storage = ReferenceStorage(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def char_generator(self, mock_gemini_client, temp_storage):
        """Create character generator."""
        return CharacterReferenceGenerator(mock_gemini_client, temp_storage)
    
    @pytest.mark.asyncio
    async def test_generate_character_reference(self, char_generator, mock_gemini_client):
        """Test character reference generation."""
        # Generate character
        character = await char_generator.generate_reference(
            name="Hero",
            description="A brave hero",
            poses=["standing", "running"],
            expressions=["happy", "sad"]
        )
        
        # Verify character created
        assert character.name == "Hero"
        assert character.description == "A brave hero"
        assert "standing" in character.poses
        assert "running" in character.poses
        assert "happy" in character.expressions
        assert "sad" in character.expressions
        
        # Verify API calls made
        assert mock_gemini_client.generate_image.call_count > 0
    
    def test_build_character_prompt(self, char_generator):
        """Test character prompt building."""
        # Test character sheet prompt
        prompt = char_generator._build_generation_prompt(
            "A hero character",
            {"type": "character sheet", "pose": "standing", "expression": "neutral"}
        )
        
        assert "character reference sheet" in prompt
        assert "A hero character" in prompt
        assert "Full body view" in prompt
        
        # Test specific pose prompt
        prompt = char_generator._build_generation_prompt(
            "A hero character",
            {"pose": "running", "expression": "happy"}
        )
        
        assert "running pose" in prompt
        assert "happy" in prompt
        assert "EXACT appearance" in prompt
    
    @pytest.mark.asyncio
    async def test_generate_with_style_guide(self, char_generator, mock_gemini_client):
        """Test character generation with style guide."""
        style = StyleGuide(
            name="Comic Style",
            description="Comic book style",
            art_style="comic-book"
        )
        
        character = await char_generator.generate_reference(
            name="Styled Hero",
            description="A stylized hero",
            style_guide=style
        )
        
        # Verify style was applied
        calls = mock_gemini_client.generate_image.call_args_list
        # Check that at least one call includes style info
        prompts_contain_style = any(
            "comic-book" in str(call) for call in calls
        )
        assert prompts_contain_style


class TestLocationReferenceGenerator:
    """Test LocationReferenceGenerator."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client."""
        client = Mock(spec=GeminiClient)
        # Create a small valid PNG image
        img = Image.new('RGB', (10, 10), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        client.generate_image = AsyncMock(return_value=img_bytes.getvalue())
        return client
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        temp_dir = tempfile.mkdtemp()
        storage = ReferenceStorage(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def location_generator(self, mock_gemini_client, temp_storage):
        """Create location generator."""
        return LocationReferenceGenerator(mock_gemini_client, temp_storage)
    
    @pytest.mark.asyncio
    async def test_generate_location_reference(self, location_generator):
        """Test location reference generation."""
        location = await location_generator.generate_reference(
            name="Forest",
            description="A mystical forest",
            angles=["wide-shot", "close-up"],
            lighting_conditions=["dawn", "dusk"]
        )
        
        assert location.name == "Forest"
        assert location.description == "A mystical forest"
        assert "wide-shot" in location.angles
        assert "close-up" in location.angles
        assert "dawn" in location.lighting_conditions
        assert "dusk" in location.lighting_conditions
    
    def test_build_location_prompt(self, location_generator):
        """Test location prompt building."""
        # Test establishing shot
        prompt = location_generator._build_generation_prompt(
            "A forest location",
            {"type": "establishing", "angle": "wide-shot", "lighting": "dawn"}
        )
        
        assert "establishing shot" in prompt
        assert "A forest location" in prompt
        assert "dawn" in prompt
        
        # Test specific angle
        prompt = location_generator._build_generation_prompt(
            "A forest location",
            {"angle": "close-up", "lighting": "dusk", "time": "evening"}
        )
        
        assert "close-up" in prompt
        assert "dusk" in prompt
        assert "evening" in prompt


class TestObjectReferenceGenerator:
    """Test ObjectReferenceGenerator."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client."""
        client = Mock(spec=GeminiClient)
        # Create a small valid PNG image
        img = Image.new('RGB', (10, 10), color='green')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        client.generate_image = AsyncMock(return_value=img_bytes.getvalue())
        return client
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        temp_dir = tempfile.mkdtemp()
        storage = ReferenceStorage(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def object_generator(self, mock_gemini_client, temp_storage):
        """Create object generator."""
        return ObjectReferenceGenerator(mock_gemini_client, temp_storage)
    
    @pytest.mark.asyncio
    async def test_generate_object_reference(self, object_generator):
        """Test object reference generation."""
        obj = await object_generator.generate_reference(
            name="Magic Sword",
            description="An enchanted blade",
            views=["front", "side"],
            states=["new", "glowing"]
        )
        
        assert obj.name == "Magic Sword"
        assert obj.description == "An enchanted blade"
        assert "front" in obj.views
        assert "side" in obj.views
        assert "new" in obj.states
        assert "glowing" in obj.states
    
    def test_build_object_prompt(self, object_generator):
        """Test object prompt building."""
        prompt = object_generator._build_generation_prompt(
            "A magical sword",
            {"view": "front", "state": "glowing", "type": "reference"}
        )
        
        assert "reference image" in prompt
        assert "A magical sword" in prompt
        assert "glowing" in prompt


class TestStyleGuideGenerator:
    """Test StyleGuideGenerator."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client."""
        client = Mock(spec=GeminiClient)
        # Create a small valid PNG image
        img = Image.new('RGB', (10, 10), color='yellow')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        client.generate_image = AsyncMock(return_value=img_bytes.getvalue())
        return client
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage."""
        temp_dir = tempfile.mkdtemp()
        storage = ReferenceStorage(temp_dir)
        yield storage
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def style_generator(self, mock_gemini_client, temp_storage):
        """Create style generator."""
        return StyleGuideGenerator(mock_gemini_client, temp_storage)
    
    @pytest.mark.asyncio
    async def test_generate_style_guide(self, style_generator):
        """Test style guide generation."""
        style = await style_generator.generate_reference(
            name="Comic Style",
            description="Comic book style guide",
            art_style="comic-book",
            color_palette=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        assert style.name == "Comic Style"
        assert style.description == "Comic book style guide"
        assert style.art_style == "comic-book"
        assert len(style.color_palette) == 3
        assert "#FF0000" in style.color_palette
    
    def test_build_style_prompt(self, style_generator):
        """Test style guide prompt building."""
        prompt = style_generator._build_generation_prompt(
            "A comic book style",
            {
                "art_style": "comic-book",
                "colors": ["#FF0000", "#00FF00"],
                "sample": "character samples"
            }
        )
        
        assert "style guide reference" in prompt
        assert "A comic book style" in prompt
        assert "comic-book" in prompt
        assert "#FF0000" in prompt
        assert "character samples" in prompt