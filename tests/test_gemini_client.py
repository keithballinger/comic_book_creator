"""Tests for Gemini API client."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import os

from src.api import GeminiClient, RateLimiter
from src.models import Panel, CharacterReference


class TestGeminiClient:
    """Test cases for GeminiClient class."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock Gemini client."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key'}):
            with patch('src.api.gemini_client.genai.Client'):
                client = GeminiClient()
                yield client
    
    @pytest.mark.asyncio
    async def test_init_with_api_key(self):
        """Test client initialization with API key."""
        with patch('src.api.gemini_client.genai.Client') as mock_genai:
            client = GeminiClient(api_key='test-key-direct')
            assert client.api_key == 'test-key-direct'
            mock_genai.assert_called_once_with(api_key='test-key-direct')
    
    @pytest.mark.asyncio
    async def test_init_from_env(self):
        """Test client initialization from environment."""
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'test-key-env'}):
            with patch('src.api.gemini_client.genai.Client') as mock_genai:
                client = GeminiClient()
                assert client.api_key == 'test-key-env'
                mock_genai.assert_called_once_with(api_key='test-key-env')
    
    def test_init_no_api_key(self):
        """Test client initialization without API key."""
        # Test that ValueError is raised when no API key provided
        with patch('src.api.gemini_client.load_dotenv'):  # Prevent loading .env file
            with patch.dict(os.environ, {}, clear=True):
                with pytest.raises(ValueError, match="GEMINI_API_KEY"):
                    GeminiClient()
    
    @pytest.mark.asyncio
    async def test_generate_panel_image(self, mock_client):
        """Test panel image generation."""
        # Mock the API response
        mock_response = MagicMock()
        mock_image = MagicMock()
        mock_image.image.data = b'fake_image_data'
        mock_response.generated_images = [mock_image]
        
        mock_client.client.models.generate_images = MagicMock(return_value=mock_response)
        
        # Generate image
        prompt = "A hero standing on a rooftop"
        style_config = {
            'art_style': 'comic book',
            'color_palette': 'vibrant'
        }
        
        result = await mock_client.generate_panel_image(prompt, style_config=style_config)
        
        assert result == b'fake_image_data'
        mock_client.client.models.generate_images.assert_called_once()
        
        # Check that style was included in prompt
        call_args = mock_client.client.models.generate_images.call_args
        assert 'comic book' in call_args.kwargs['prompt']
        assert 'vibrant' in call_args.kwargs['prompt']
    
    @pytest.mark.asyncio
    async def test_generate_panel_image_error(self, mock_client):
        """Test panel image generation with error."""
        mock_client.client.models.generate_images = MagicMock(
            side_effect=Exception("API Error")
        )
        
        with pytest.raises(Exception, match="API Error"):
            await mock_client.generate_panel_image("test prompt")
    
    @pytest.mark.asyncio
    async def test_enhance_panel_description(self, mock_client):
        """Test panel description enhancement."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.text = "Enhanced description"
        
        mock_client.client.models.generate_content = MagicMock(
            return_value=mock_response
        )
        
        # Create panel
        panel = Panel(number=1, description="Basic description")
        
        # Enhance description
        result = await mock_client.enhance_panel_description(panel)
        
        assert result == "Enhanced description"
        mock_client.client.models.generate_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_enhance_panel_description_with_characters(self, mock_client):
        """Test panel description enhancement with character references."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.text = "Enhanced with character details"
        
        mock_client.client.models.generate_content = MagicMock(
            return_value=mock_response
        )
        
        # Create panel with characters
        panel = Panel(number=1, description="Hero enters")
        panel.characters = ["Hero"]
        
        # Create character reference
        char_refs = {
            "Hero": CharacterReference(
                name="Hero",
                appearance_description="Tall, blue costume"
            )
        }
        
        # Enhance description
        result = await mock_client.enhance_panel_description(panel, char_refs)
        
        assert result == "Enhanced with character details"
        
        # Check that character info was included in prompt
        call_args = mock_client.client.models.generate_content.call_args
        prompt = call_args[1]['contents']
        assert "Hero" in prompt
        assert "blue costume" in prompt
    
    @pytest.mark.asyncio
    async def test_enhance_panel_description_error_fallback(self, mock_client):
        """Test panel description enhancement with error fallback."""
        mock_client.client.models.generate_content = MagicMock(
            side_effect=Exception("API Error")
        )
        
        panel = Panel(number=1, description="Original description")
        
        # Should return original description on error
        result = await mock_client.enhance_panel_description(panel)
        assert result == "Original description"
    
    @pytest.mark.asyncio
    async def test_generate_character_reference(self, mock_client):
        """Test character reference generation."""
        # Create mock response
        mock_response = MagicMock()
        mock_response.text = "Detailed character appearance"
        
        mock_client.client.models.generate_content = MagicMock(
            return_value=mock_response
        )
        
        # Generate character reference
        result = await mock_client.generate_character_reference(
            "Hero",
            "A brave superhero"
        )
        
        assert isinstance(result, CharacterReference)
        assert result.name == "Hero"
        assert result.appearance_description == "Detailed character appearance"
    
    def test_build_image_prompt(self, mock_client):
        """Test image prompt building."""
        base_prompt = "A hero flying"
        style_config = {
            'art_style': 'manga',
            'color_palette': 'black and white',
            'line_weight': 'thin',
            'shading': 'cross-hatching'
        }
        
        result = mock_client._build_image_prompt(base_prompt, style_config)
        
        assert "manga" in result
        assert "black and white" in result
        assert "thin" in result
        assert "cross-hatching" in result
        assert "A hero flying" in result
        assert "High quality comic book panel" in result
    
    def test_build_enhancement_prompt(self, mock_client):
        """Test enhancement prompt building."""
        panel = Panel(number=1, description="Test panel")
        panel.add_dialogue("Hero", "Hello!", "happy")
        panel.characters = ["Hero"]
        
        char_refs = {
            "Hero": CharacterReference(
                name="Hero",
                appearance_description="Blue costume"
            )
        }
        
        result = mock_client._build_enhancement_prompt(panel, char_refs)
        
        assert "Panel 1" in result
        assert "Test panel" in result
        assert "Hero" in result
        assert "Blue costume" in result
        assert "Hello!" in result
        assert "happy" in result


class TestRateLimiter:
    """Test cases for RateLimiter class."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_basic(self):
        """Test basic rate limiting."""
        limiter = RateLimiter(calls_per_minute=60)
        
        # First call should be immediate
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        
        assert elapsed < 0.1  # Should be nearly instant
        assert limiter.get_current_rate() == 1
        assert limiter.get_remaining_calls() == 59
    
    @pytest.mark.asyncio
    async def test_rate_limit_interval(self):
        """Test minimum interval between calls."""
        limiter = RateLimiter(calls_per_minute=30)  # 2 seconds between calls
        
        # Make two calls
        await limiter.acquire()
        start = asyncio.get_event_loop().time()
        await limiter.acquire()
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should wait at least 2 seconds
        assert elapsed >= 1.9  # Allow small tolerance
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self):
        """Test executing function with retry on success."""
        limiter = RateLimiter(calls_per_minute=60)
        
        async def test_func():
            return "success"
        
        result = await limiter.execute_with_retry(test_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_temporary_error(self):
        """Test retry on temporary error."""
        limiter = RateLimiter(calls_per_minute=60, max_retries=3)
        
        call_count = 0
        
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("timeout error")
            return "success"
        
        result = await limiter.execute_with_retry(test_func)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_execute_with_retry_permanent_error(self):
        """Test no retry on permanent error."""
        limiter = RateLimiter(calls_per_minute=60)
        
        async def test_func():
            raise ValueError("Invalid input")
        
        with pytest.raises(ValueError, match="Invalid input"):
            await limiter.execute_with_retry(test_func)
    
    def test_reset(self):
        """Test resetting rate limiter."""
        limiter = RateLimiter(calls_per_minute=60)
        limiter.call_times = [1, 2, 3]
        
        limiter.reset()
        assert len(limiter.call_times) == 0