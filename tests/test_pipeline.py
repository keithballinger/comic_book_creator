"""Tests for processing pipeline."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import tempfile
import shutil
from pathlib import Path

from src.processor.pipeline import ProcessingPipeline
from src.models import (
    ComicScript,
    Page,
    Panel,
    GeneratedPanel,
    GeneratedPage,
    ProcessingResult,
    ProcessingOptions,
    ValidationResult,
)
from src.config import ConfigLoader


class TestProcessingPipeline:
    """Test cases for ProcessingPipeline class."""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary output directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        config = MagicMock()
        config.api_key = "test_key"
        config.cache = {'directory': '.cache'}
        config.api = {'rate_limit': 30}
        config.get_style = MagicMock(return_value=None)
        return config
    
    @pytest.fixture
    def mock_panel_generator(self):
        """Create mock panel generator."""
        generator = MagicMock()
        generator.generate_panel = AsyncMock(
            return_value=GeneratedPanel(
                panel=None,
                image_data=b"fake_image",
                generation_time=1.0
            )
        )
        generator.generate_page_panels = AsyncMock(
            return_value=[
                GeneratedPanel(panel=None, image_data=b"fake1", generation_time=1.0),
                GeneratedPanel(panel=None, image_data=b"fake2", generation_time=1.0),
            ]
        )
        generator.initialize_characters = AsyncMock()
        generator.set_style = MagicMock()
        return generator
    
    @pytest.fixture
    def mock_text_renderer(self):
        """Create mock text renderer."""
        from PIL import Image
        renderer = MagicMock()
        renderer.render_panel_text.return_value = Image.new('RGB', (100, 100))
        return renderer
    
    @pytest.fixture
    def pipeline(self, mock_config, mock_panel_generator, mock_text_renderer, temp_output_dir):
        """Create pipeline with mocks."""
        return ProcessingPipeline(
            config=mock_config,
            panel_generator=mock_panel_generator,
            text_renderer=mock_text_renderer,
            output_dir=temp_output_dir
        )
    
    @pytest.fixture
    def test_script(self):
        """Create test script."""
        script = ComicScript(title="Test Comic")
        
        # Add pages with panels
        for page_num in range(1, 3):
            page = Page(number=page_num)
            for panel_num in range(1, 4):
                panel = Panel(
                    number=panel_num,
                    description=f"Panel {panel_num} on page {page_num}"
                )
                panel.add_dialogue("Hero", "Test dialogue")
                page.add_panel(panel)
            script.add_page(page)
        
        return script
    
    @pytest.mark.asyncio
    async def test_process_script_success(self, pipeline, test_script, temp_output_dir):
        """Test successful script processing."""
        # Create test script file
        script_path = Path(temp_output_dir) / "test_script.txt"
        with open(script_path, 'w') as f:
            f.write("PAGE 1\n\nPANEL 1\nTest panel\n")
        
        # Mock parser and validator
        pipeline.parser.parse_file = MagicMock(return_value=test_script)
        pipeline.validator.validate = MagicMock(
            return_value=ValidationResult(is_valid=True)
        )
        
        result = await pipeline.process_script(str(script_path))
        
        assert result.success
        assert result.script == test_script
        assert result.processing_time > 0
        assert pipeline.stats['scripts_processed'] == 1
    
    @pytest.mark.asyncio
    async def test_process_script_validation_failure(self, pipeline, temp_output_dir):
        """Test script processing with validation failure."""
        script_path = Path(temp_output_dir) / "invalid_script.txt"
        script_path.touch()
        
        # Mock invalid script
        invalid_script = ComicScript(title="Invalid")
        pipeline.parser.parse_file = MagicMock(return_value=invalid_script)
        pipeline.validator.validate = MagicMock(
            return_value=ValidationResult(
                is_valid=False,
                errors=["No pages found"]
            )
        )
        
        result = await pipeline.process_script(str(script_path))
        
        assert not result.success
        assert result.validation_result.errors == ["No pages found"]
    
    @pytest.mark.asyncio
    async def test_process_script_with_options(self, pipeline, test_script, temp_output_dir):
        """Test script processing with options."""
        script_path = Path(temp_output_dir) / "test_script.txt"
        script_path.touch()
        
        pipeline.parser.parse_file = MagicMock(return_value=test_script)
        pipeline.validator.validate = MagicMock(
            return_value=ValidationResult(is_valid=True)
        )
        
        options = ProcessingOptions(
            page_range=(1, 1),
            parallel_generation=True,
            render_text=True,
            skip_cache=True
        )
        
        result = await pipeline.process_script(str(script_path), options)
        
        assert result.success
        # Should only process page 1
        assert len(result.generated_pages) == 1
    
    @pytest.mark.asyncio
    async def test_process_page(self, pipeline, test_script):
        """Test page processing."""
        page = test_script.pages[0]
        
        generated_page = await pipeline.process_page(page)
        
        assert isinstance(generated_page, GeneratedPage)
        assert generated_page.page == page
        assert len(generated_page.panels) == 2  # Mock returns 2 panels
        assert generated_page.generation_time > 0
        
        pipeline.panel_generator.generate_page_panels.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_page_with_text_rendering(self, pipeline, test_script):
        """Test page processing with text rendering."""
        page = test_script.pages[0]
        
        # Create minimal valid PNG data
        valid_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\xd8\xdc\xfd\xad\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Update mock panels to include panel data and valid image
        pipeline.panel_generator.generate_page_panels.return_value = [
            GeneratedPanel(
                panel=page.panels[0],
                image_data=valid_png,
                generation_time=1.0
            ),
            GeneratedPanel(
                panel=page.panels[1],
                image_data=valid_png,
                generation_time=1.0
            ),
        ]
        
        options = ProcessingOptions(render_text=True)
        generated_page = await pipeline.process_page(page, options=options)
        
        assert isinstance(generated_page, GeneratedPage)
        # Text renderer should have been called
        assert pipeline.text_renderer.render_panel_text.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_process_panel(self, pipeline, test_script):
        """Test single panel processing."""
        panel = test_script.pages[0].panels[0]
        
        generated_panel = await pipeline.process_panel(panel)
        
        assert isinstance(generated_panel, GeneratedPanel)
        assert generated_panel.image_data == b"fake_image"
        assert generated_panel.generation_time == 1.0
        
        pipeline.panel_generator.generate_panel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_panel_with_options(self, pipeline, test_script):
        """Test panel processing with options."""
        panel = test_script.pages[0].panels[0]
        
        # Update mock to return panel with panel data
        pipeline.panel_generator.generate_panel.return_value = GeneratedPanel(
            panel=panel,
            image_data=b"fake_image",
            generation_time=1.0
        )
        
        options = ProcessingOptions(
            render_text=True,
            skip_cache=True
        )
        
        generated_panel = await pipeline.process_panel(
            panel,
            options=options
        )
        
        assert generated_panel.image_data is not None
        # Check that skip_cache was passed
        pipeline.panel_generator.generate_panel.assert_called_with(
            panel,
            None,
            None,
            skip_cache=True
        )
    
    @pytest.mark.asyncio
    async def test_initialize_generator(self, pipeline, test_script):
        """Test generator initialization."""
        pipeline.panel_generator = None
        
        options = ProcessingOptions(style_preset="comic_style")
        
        from src.generator import PanelGenerator
        from src.api import GeminiClient
        
        with patch('src.processor.pipeline.GeminiClient') as MockClient:
            with patch('src.processor.pipeline.PanelGenerator') as MockGen:
                mock_gen = MagicMock()
                mock_gen.initialize_characters = AsyncMock()
                MockGen.return_value = mock_gen
                MockClient.return_value = MagicMock()
                
                await pipeline._initialize_generator(test_script, options)
                
                assert pipeline.panel_generator is not None
                MockGen.assert_called_once()
    
    def test_extract_characters(self, pipeline, test_script):
        """Test character extraction from script."""
        # Add more characters
        test_script.pages[0].panels[0].add_dialogue("Villain", "Ha ha!")
        test_script.pages[1].panels[0].add_dialogue("Sidekick", "Help!")
        
        characters = pipeline._extract_characters(test_script)
        
        assert "Hero" in characters
        assert "Villain" in characters
        assert "Sidekick" in characters
        assert len(characters) == 3
        assert characters == sorted(characters)  # Should be sorted
    
    def test_should_process_page(self, pipeline):
        """Test page filtering logic."""
        page1 = Page(number=1)
        page2 = Page(number=2)
        page3 = Page(number=3)
        
        # No filter
        options = ProcessingOptions()
        assert pipeline._should_process_page(page1, options)
        assert pipeline._should_process_page(page2, options)
        assert pipeline._should_process_page(page3, options)
        
        # With page range
        options = ProcessingOptions(page_range=(1, 2))
        assert pipeline._should_process_page(page1, options)
        assert pipeline._should_process_page(page2, options)
        assert not pipeline._should_process_page(page3, options)
    
    def test_get_statistics(self, pipeline):
        """Test statistics retrieval."""
        pipeline.stats = {
            'scripts_processed': 2,
            'pages_generated': 10,
            'panels_generated': 50,
            'total_time': 100.0,
            'errors': [],
        }
        
        stats = pipeline.get_statistics()
        
        assert stats['scripts_processed'] == 2
        assert stats['avg_processing_time'] == 50.0
        assert stats['avg_pages_per_script'] == 5.0
        assert stats['avg_panels_per_page'] == 5.0
    
    def test_reset_statistics(self, pipeline):
        """Test statistics reset."""
        pipeline.stats['scripts_processed'] = 10
        pipeline.stats['errors'].append("test error")
        
        pipeline.reset_statistics()
        
        assert pipeline.stats['scripts_processed'] == 0
        assert len(pipeline.stats['errors']) == 0
    
    @pytest.mark.asyncio
    async def test_save_results(self, pipeline, test_script, temp_output_dir):
        """Test saving results to disk."""
        # Create mock result
        result = ProcessingResult(
            success=True,
            script=test_script,
            generated_pages=[
                GeneratedPage(
                    page=test_script.pages[0],
                    panels=[
                        GeneratedPanel(
                            panel=test_script.pages[0].panels[0],
                            image_data=b"\x89PNG\r\n\x1a\n",  # Minimal PNG header
                            generation_time=1.0
                        )
                    ],
                    generation_time=1.0
                )
            ],
            processing_time=10.0
        )
        
        output_path = await pipeline.save_results(result, "test_output")
        
        assert output_path.exists()
        assert (output_path / "metadata.json").exists()
        assert (output_path / "page_001").exists()
    
    @pytest.mark.asyncio
    async def test_process_script_error_handling(self, pipeline, temp_output_dir):
        """Test error handling in script processing."""
        script_path = Path(temp_output_dir) / "error_script.txt"
        script_path.touch()
        
        # Make parser raise an exception
        pipeline.parser.parse_file = MagicMock(
            side_effect=Exception("Parse error")
        )
        
        result = await pipeline.process_script(str(script_path))
        
        assert not result.success
        assert 'error' in result.metadata
        assert result.metadata['error'] == "Parse error"
        assert len(pipeline.stats['errors']) == 1
    
    @pytest.mark.asyncio
    async def test_render_text_error_handling(self, pipeline):
        """Test error handling in text rendering."""
        panel = GeneratedPanel(
            panel=Panel(1, "Test"),
            image_data=b"invalid_image",
            generation_time=1.0
        )
        
        # Make PIL raise an error
        from PIL import Image
        with patch.object(Image, 'open', side_effect=Exception("Invalid image")):
            result = await pipeline._render_text_on_panels(
                [panel],
                ProcessingOptions()
            )
        
        # Should return panel unchanged
        assert len(result) == 1
        assert result[0] == panel