"""Integration tests for reference system with comic generation."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import shutil
from PIL import Image
import io

from src.processor.pipeline import ProcessingPipeline
from src.generator.panel_generator import PanelGenerator
from src.references.manager import ReferenceManager
from src.references.storage import ReferenceStorage
from src.references.models import CharacterReference, LocationReference, StyleGuide
from src.models import (
    ComicScript,
    Page,
    Panel,
    ProcessingOptions,
    GeneratedPanel,
)
from src.api import GeminiClient


class TestReferenceIntegration:
    """Test integration of reference system with comic generation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client."""
        client = Mock(spec=GeminiClient)
        # Create a small valid image
        img = Image.new('RGB', (512, 512), color='blue')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        client.generate_panel_image = AsyncMock(return_value=img_bytes.getvalue())
        client.generate_image = AsyncMock(return_value=img_bytes.getvalue())
        return client
    
    @pytest.fixture
    def reference_manager(self, temp_dir):
        """Create reference manager with test data."""
        storage = ReferenceStorage(temp_dir)
        manager = ReferenceManager(storage=storage)
        
        # Create test references
        char = CharacterReference(
            name="Hero",
            description="A brave hero",
            poses=["standing"],
            expressions=["determined"]
        )
        char.images = {"standing": "hero_standing.png"}
        storage.save_reference(char)
        
        loc = LocationReference(
            name="Castle",
            description="A medieval castle",
            location_type="exterior",
            angles=["wide"],
            lighting_conditions=["daylight"]
        )
        loc.images = {"wide": "castle_wide.png"}
        storage.save_reference(loc)
        
        style = StyleGuide(
            name="Fantasy",
            description="Fantasy art style",
            art_style="fantasy-illustration",
            color_palette=["#8B4513", "#4682B4", "#DAA520"]
        )
        storage.save_reference(style)
        
        # Save mock images
        img_data = b"test_image_data"
        storage.save_reference_image("character", "Hero", "standing", img_data)
        storage.save_reference_image("location", "Castle", "wide", img_data)
        
        return manager
    
    @pytest.fixture
    def panel_generator(self, mock_gemini_client, reference_manager):
        """Create panel generator with reference manager."""
        from src.generator.consistency import ConsistencyManager
        
        return PanelGenerator(
            gemini_client=mock_gemini_client,
            consistency_manager=ConsistencyManager(),
            reference_manager=reference_manager
        )
    
    @pytest.mark.asyncio
    async def test_panel_generator_with_references(self, panel_generator):
        """Test panel generator using reference manager."""
        # Create test panel
        panel = Panel(
            number=1,
            description="Hero stands before the Castle gates",
            characters=["Hero"]
        )
        
        # Generate panel with references
        result = await panel_generator.generate_panel_with_references(panel)
        
        # Verify result
        assert result is not None
        assert isinstance(result, GeneratedPanel)
        assert result.panel == panel
        assert result.metadata.get('used_references') is True
        assert result.metadata.get('reference_count', 0) > 0
        
        # Check that references were found
        found_refs = result.metadata.get('found_references', {})
        assert 'character' in found_refs
        assert 'Hero' in found_refs['character']
        assert 'location' in found_refs
        assert 'Castle' in found_refs['location']
    
    @pytest.mark.asyncio
    async def test_pipeline_with_reference_manager(self, temp_dir, mock_gemini_client, reference_manager):
        """Test processing pipeline with reference manager."""
        # Create pipeline with reference manager
        with patch('src.processor.pipeline.GeminiClient', return_value=mock_gemini_client):
            pipeline = ProcessingPipeline(
                output_dir=temp_dir,
                reference_manager=reference_manager,
                use_references=True
            )
            
            # Create test script
            script = ComicScript(
                title="Test Comic",
                author="Test Author",
                pages=[
                    Page(
                        number=1,
                        panels=[
                            Panel(
                                number=1,
                                description="Hero enters the Castle",
                                characters=["Hero"]
                            )
                        ]
                    )
                ]
            )
            
            # Process page
            page = script.pages[0]
            result = await pipeline.process_page(page)
            
            # Verify result
            assert result is not None
            assert len(result.panels) == 1
            assert result.panels[0].metadata.get('used_references') is True
    
    @pytest.mark.asyncio
    async def test_reference_extraction_from_text(self, panel_generator):
        """Test automatic reference extraction from panel text."""
        # Create panel with references in text
        panel = Panel(
            number=1,
            description="The Hero walks through the Castle courtyard"
        )
        
        # Extract references
        found_refs = panel_generator._extract_references_from_text(panel.description)
        
        # Verify extraction
        assert 'character' in found_refs
        assert 'Hero' in found_refs['character']
        assert 'location' in found_refs
        assert 'Castle' in found_refs['location']
    
    @pytest.mark.asyncio
    async def test_get_reference_images(self, panel_generator):
        """Test getting reference images for a panel."""
        panel = Panel(number=1, description="Test panel")
        
        # Get reference images
        ref_images = panel_generator._get_reference_images(
            panel,
            characters=["Hero"],
            locations=["Castle"]
        )
        
        # Should get images (though they're mock data)
        assert isinstance(ref_images, list)
        # Note: actual image loading might fail with mock data
    
    @pytest.mark.asyncio
    async def test_style_guide_integration(self, panel_generator):
        """Test style guide integration in generation."""
        panel = Panel(
            number=1,
            description="A fantasy scene"
        )
        
        # Generate with style guide
        result = await panel_generator.generate_panel_with_references(panel)
        
        # The prompt should include style information
        # (would need to inspect the actual prompt passed to Gemini)
        assert result is not None
    
    def test_pipeline_init_with_references(self, temp_dir, mock_gemini_client):
        """Test pipeline initialization with reference system."""
        with patch('src.processor.pipeline.GeminiClient', return_value=mock_gemini_client):
            with patch('src.processor.pipeline.ConfigLoader') as mock_config:
                mock_config.return_value.load.return_value = {'gemini_api_key': 'test-key'}
                mock_config.return_value.get.return_value = 'test-key'
                # Create pipeline with references enabled
                pipeline = ProcessingPipeline(
                    output_dir=temp_dir,
                    use_references=True
                )
            
            # Should have created reference manager
            assert pipeline.reference_manager is not None
            assert pipeline.use_references is True
            
            # Panel generator should have reference manager
            assert pipeline.panel_generator.reference_manager is not None
    
    def test_pipeline_init_without_references(self, temp_dir, mock_gemini_client):
        """Test pipeline initialization without reference system."""
        with patch('src.processor.pipeline.GeminiClient', return_value=mock_gemini_client):
            with patch('src.processor.pipeline.ConfigLoader') as mock_config:
                mock_config.return_value.load.return_value = {'gemini_api_key': 'test-key'}
                mock_config.return_value.get.return_value = 'test-key'
                # Create pipeline with references disabled
                pipeline = ProcessingPipeline(
                    output_dir=temp_dir,
                    use_references=False
                )
            
            # Should not have reference manager
            assert pipeline.reference_manager is None
            assert pipeline.use_references is False
    
    @pytest.mark.asyncio
    async def test_panel_generation_without_references(self, mock_gemini_client):
        """Test panel generation works without reference manager."""
        from src.generator.consistency import ConsistencyManager
        
        # Create panel generator without reference manager
        panel_generator = PanelGenerator(
            gemini_client=mock_gemini_client,
            consistency_manager=ConsistencyManager(),
            reference_manager=None
        )
        
        panel = Panel(
            number=1,
            description="A scene without references"
        )
        
        # Should still work without references
        result = await panel_generator.generate_panel_with_references(panel)
        
        assert result is not None
        assert result.metadata.get('used_references') is False
        assert result.metadata.get('reference_count', 0) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_panels_with_consistency(self, panel_generator):
        """Test generating multiple panels maintains consistency."""
        panels = [
            Panel(number=1, description="Hero enters the Castle"),
            Panel(number=2, description="Hero explores the Castle halls"),
            Panel(number=3, description="Hero finds treasure in the Castle"),
        ]
        
        generated_panels = []
        for panel in panels:
            result = await panel_generator.generate_panel_with_references(
                panel,
                previous_panels=generated_panels
            )
            generated_panels.append(result)
        
        # All panels should use references
        assert len(generated_panels) == 3
        for gp in generated_panels:
            assert gp.metadata.get('found_references', {}).get('character') == ['Hero']
            assert gp.metadata.get('found_references', {}).get('location') == ['Castle']
    
    def test_reference_manager_in_panel_generator(self, panel_generator, reference_manager):
        """Test reference manager is properly set in panel generator."""
        assert panel_generator.reference_manager == reference_manager
        
        # Test extraction works
        refs = panel_generator._extract_references_from_text("Hero at Castle")
        assert 'character' in refs
        assert 'location' in refs