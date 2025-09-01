"""Tests for panel generator."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import shutil

from src.generator import PanelGenerator, ConsistencyManager
from src.processor import CacheManager
from src.api import GeminiClient, RateLimiter
from src.models import (
    Panel,
    Page,
    GeneratedPanel,
    StyleConfig,
    CharacterReference,
)


class TestPanelGenerator:
    """Test cases for PanelGenerator class."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_client(self):
        """Create mock Gemini client."""
        client = MagicMock(spec=GeminiClient)
        client.generate_panel_image = AsyncMock(return_value=b"fake_image_data")
        client.enhance_panel_description = AsyncMock(return_value="Enhanced description")
        client.generate_character_reference = AsyncMock(
            side_effect=lambda name, desc: CharacterReference(name, desc)
        )
        return client
    
    @pytest.fixture
    def generator(self, mock_client, temp_cache_dir):
        """Create panel generator with mocks."""
        consistency_manager = ConsistencyManager(cache_dir=temp_cache_dir)
        cache_manager = CacheManager(cache_dir=temp_cache_dir)
        rate_limiter = RateLimiter(calls_per_minute=60)
        
        return PanelGenerator(
            gemini_client=mock_client,
            consistency_manager=consistency_manager,
            cache_manager=cache_manager,
            rate_limiter=rate_limiter
        )
    
    @pytest.mark.asyncio
    async def test_generate_panel_basic(self, generator, mock_client):
        """Test basic panel generation."""
        panel = Panel(number=1, description="Test panel")
        
        result = await generator.generate_panel(panel)
        
        assert isinstance(result, GeneratedPanel)
        assert result.image_data == b"fake_image_data"
        assert result.panel == panel
        assert result.generation_time > 0
        
        # Check that API was called
        mock_client.generate_panel_image.assert_called_once()
        mock_client.enhance_panel_description.assert_called_once()
        
        # Check statistics
        stats = generator.get_statistics()
        assert stats['panels_generated'] == 1
        assert stats['api_calls'] == 1
    
    @pytest.mark.asyncio
    async def test_generate_panel_with_cache(self, generator):
        """Test panel generation with caching."""
        panel = Panel(number=1, description="Cached panel")
        
        # Generate first time
        result1 = await generator.generate_panel(panel)
        assert result1.image_data == b"fake_image_data"
        
        # Generate second time (should hit cache)
        result2 = await generator.generate_panel(panel)
        
        # Check cache hit
        stats = generator.get_statistics()
        assert stats['cache_hits'] == 1
        assert stats['api_calls'] == 1  # Only one API call
    
    @pytest.mark.asyncio
    async def test_generate_panel_skip_cache(self, generator):
        """Test skipping cache."""
        panel = Panel(number=1, description="No cache panel")
        
        # Generate with cache
        await generator.generate_panel(panel)
        
        # Generate again skipping cache
        await generator.generate_panel(panel, skip_cache=True)
        
        stats = generator.get_statistics()
        assert stats['cache_hits'] == 0
        assert stats['api_calls'] == 2
    
    @pytest.mark.asyncio
    async def test_generate_panel_with_style(self, generator):
        """Test panel generation with style."""
        style = StyleConfig(
            name="test_style",
            art_style="comic",
            color_palette="vibrant",
            line_weight="medium",
            shading="cel"
        )
        generator.set_style(style)
        
        panel = Panel(number=1, description="Styled panel")
        result = await generator.generate_panel(panel)
        
        assert result.image_data == b"fake_image_data"
        assert generator.consistency_manager.style_config == style
    
    @pytest.mark.asyncio
    async def test_generate_panel_with_characters(self, generator, mock_client):
        """Test panel generation with character consistency."""
        # Initialize character
        await generator.initialize_characters(["Hero"])
        
        # Create panel with character
        panel = Panel(number=1, description="Hero appears")
        panel.characters = ["Hero"]
        
        result = await generator.generate_panel(panel)
        
        assert result.image_data == b"fake_image_data"
        
        # Check that character was registered
        assert "Hero" in generator.consistency_manager.character_refs
        mock_client.generate_character_reference.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_panel_with_previous(self, generator):
        """Test panel generation with previous panels for consistency."""
        # Generate first panel
        panel1 = Panel(number=1, description="First panel")
        gen_panel1 = await generator.generate_panel(panel1)
        
        # Generate second panel with first as context
        panel2 = Panel(number=2, description="Second panel")
        gen_panel2 = await generator.generate_panel(
            panel2,
            previous_panels=[gen_panel1]
        )
        
        assert gen_panel2.image_data == b"fake_image_data"
        assert len(generator.consistency_manager.panel_history) == 2
    
    @pytest.mark.asyncio
    async def test_generate_panel_error_handling(self, generator, mock_client):
        """Test error handling in panel generation."""
        # Make API call fail
        mock_client.generate_panel_image.side_effect = Exception("API Error")
        
        panel = Panel(number=1, description="Error panel")
        result = await generator.generate_panel(panel)
        
        # Should return placeholder panel with empty image
        assert result.image_data == b""
        assert 'error' in result.metadata
        assert result.metadata['error'] == "API Error"
        
        # Check error statistics
        stats = generator.get_statistics()
        assert stats['errors'] == 1
    
    @pytest.mark.asyncio
    async def test_generate_page_panels_sequential(self, generator):
        """Test generating all panels for a page sequentially."""
        page = Page(number=1)
        page.add_panel(Panel(number=1, description="Panel 1"))
        page.add_panel(Panel(number=2, description="Panel 2"))
        page.add_panel(Panel(number=3, description="Panel 3"))
        
        results = await generator.generate_page_panels(page, parallel=False)
        
        assert len(results) == 3
        assert all(r.image_data == b"fake_image_data" for r in results)
        
        # Check that panels were generated sequentially
        stats = generator.get_statistics()
        assert stats['panels_generated'] == 3
    
    @pytest.mark.asyncio
    async def test_generate_page_panels_parallel(self, generator):
        """Test generating all panels for a page in parallel."""
        page = Page(number=1)
        page.add_panel(Panel(number=1, description="Panel 1"))
        page.add_panel(Panel(number=2, description="Panel 2"))
        
        results = await generator.generate_page_panels(page, parallel=True)
        
        assert len(results) == 2
        assert all(r.image_data == b"fake_image_data" for r in results)
    
    @pytest.mark.asyncio
    async def test_initialize_characters_with_descriptions(self, generator, mock_client):
        """Test initializing characters with descriptions."""
        descriptions = {
            "Hero": "A brave superhero in blue",
            "Villain": "An evil mastermind in black"
        }
        
        await generator.initialize_characters(["Hero", "Villain"], descriptions)
        
        assert "Hero" in generator.consistency_manager.character_refs
        assert "Villain" in generator.consistency_manager.character_refs
        
        # Check API calls
        assert mock_client.generate_character_reference.call_count == 2
    
    def test_get_statistics(self, generator):
        """Test getting statistics."""
        stats = generator.get_statistics()
        
        assert 'panels_generated' in stats
        assert 'cache_hits' in stats
        assert 'api_calls' in stats
        assert 'avg_generation_time' in stats
        assert 'cache_hit_rate' in stats
    
    def test_reset_statistics(self, generator):
        """Test resetting statistics."""
        generator.stats['panels_generated'] = 10
        generator.stats['cache_hits'] = 5
        
        generator.reset_statistics()
        
        stats = generator.get_statistics()
        assert stats['panels_generated'] == 0
        assert stats['cache_hits'] == 0
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self, generator):
        """Test cache key generation is consistent."""
        panel = Panel(number=1, description="Test panel")
        
        key1 = generator._generate_cache_key(panel)
        key2 = generator._generate_cache_key(panel)
        
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hash length
    
    @pytest.mark.asyncio
    async def test_cache_key_different_panels(self, generator):
        """Test cache keys are different for different panels."""
        panel1 = Panel(number=1, description="Panel 1")
        panel2 = Panel(number=2, description="Panel 2")
        
        key1 = generator._generate_cache_key(panel1)
        key2 = generator._generate_cache_key(panel2)
        
        assert key1 != key2
    
    def test_serialize_deserialize_panel(self, generator):
        """Test panel serialization and deserialization."""
        panel = Panel(number=1, description="Test")
        gen_panel = GeneratedPanel(
            panel=panel,
            image_data=b"test_image",
            generation_time=1.5,
            metadata={'test': 'data'}
        )
        
        # Serialize
        serialized = generator._serialize_panel(gen_panel)
        assert serialized['panel_number'] == 1
        assert serialized['image_data'] == "746573745f696d616765"  # hex of b"test_image"
        
        # Deserialize
        deserialized = generator._deserialize_panel(serialized)
        assert deserialized.image_data == b"test_image"
        assert deserialized.generation_time == 1.5
        assert deserialized.metadata == {'test': 'data'}