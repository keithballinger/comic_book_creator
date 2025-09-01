"""Tests for text renderer."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from PIL import Image, ImageDraw, ImageFont
import tempfile
import shutil

from src.output import TextRenderer
from src.models import (
    Panel,
    Dialogue,
    Caption,
    SoundEffect,
    DialogueType,
)


class TestTextRenderer:
    """Test cases for TextRenderer class."""
    
    @pytest.fixture
    def renderer(self):
        """Create text renderer."""
        return TextRenderer()
    
    @pytest.fixture
    def test_image(self):
        """Create test image."""
        return Image.new('RGB', (800, 600), 'white')
    
    @pytest.fixture
    def test_panel(self):
        """Create test panel with text elements."""
        panel = Panel(number=1, description="Test panel")
        
        # Add dialogue
        panel.add_dialogue("Hero", "Hello, world!")
        
        # Add caption
        caption = Caption(text="Meanwhile...")
        panel.add_caption(caption)
        
        # Add sound effect
        panel.add_sound_effect("BOOM!", size="large")
        
        return panel
    
    def test_init(self, renderer):
        """Test renderer initialization."""
        assert renderer.default_font_size == 24
        assert renderer.balloon_padding == 20
        assert renderer.balloon_margin == 10
        assert len(renderer.balloon_styles) == 4
    
    def test_init_custom_params(self):
        """Test renderer with custom parameters."""
        renderer = TextRenderer(
            font_dir="/custom/fonts",
            default_font_size=32,
            balloon_padding=30,
            balloon_margin=15
        )
        
        assert renderer.default_font_size == 32
        assert renderer.balloon_padding == 30
        assert renderer.balloon_margin == 15
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_render_panel_text(self, mock_draw_class, renderer, test_image, test_panel):
        """Test rendering text on panel."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        
        # Mock text bbox for size calculations
        mock_draw.textbbox.return_value = (0, 0, 100, 20)
        
        result = renderer.render_panel_text(test_image, test_panel)
        
        # Check that image was copied
        assert result is not test_image
        assert result.size == test_image.size
        
        # Check that draw methods were called
        assert mock_draw.text.called
        assert mock_draw.rounded_rectangle.called or mock_draw.rectangle.called
    
    def test_render_empty_panel(self, renderer, test_image):
        """Test rendering panel with no text."""
        panel = Panel(number=1, description="Empty panel")
        
        result = renderer.render_panel_text(test_image, panel)
        
        # Should return copy without errors
        assert result is not test_image
        assert result.size == test_image.size
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_render_dialogue_types(self, mock_draw_class, renderer, test_image):
        """Test rendering different dialogue types."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        mock_draw.textbbox.return_value = (0, 0, 100, 20)
        
        # Test each dialogue type
        for dialogue_type in DialogueType:
            panel = Panel(number=1, description="Test")
            # Note: add_dialogue doesn't support type parameter directly
            # We'll need to update the dialogue after adding it
            panel.add_dialogue("Speaker", "Test dialogue")
            if panel.dialogue:
                panel.dialogue[-1].type = dialogue_type
            
            result = renderer.render_panel_text(test_image, panel)
            assert result is not None
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_render_multiple_dialogues(self, mock_draw_class, renderer, test_image):
        """Test rendering multiple dialogue balloons."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        mock_draw.textbbox.return_value = (0, 0, 100, 20)
        
        panel = Panel(number=1, description="Multi-dialogue")
        
        # Add multiple dialogues
        for i in range(3):
            panel.add_dialogue(f"Character{i}", f"Line {i}")
        
        result = renderer.render_panel_text(test_image, panel)
        
        # Check that all dialogues were rendered
        assert mock_draw.text.call_count >= 3
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_render_caption_positions(self, mock_draw_class, renderer, test_image):
        """Test rendering captions at different positions."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        mock_draw.textbbox.return_value = (0, 0, 100, 20)
        
        panel = Panel(number=1, description="Captions")
        
        # Add captions with different positions
        for pos in ['top', 'middle', 'bottom']:
            caption = Caption(text=f"Caption at {pos}", position=pos)
            panel.add_caption(caption)
        
        result = renderer.render_panel_text(test_image, panel)
        
        # Check that captions were rendered
        assert mock_draw.rectangle.call_count >= 3
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_render_sound_effects(self, mock_draw_class, renderer, test_image):
        """Test rendering sound effects."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        
        panel = Panel(number=1, description="SFX")
        
        # Add sound effects of different sizes
        for size in ['small', 'medium', 'large', 'huge']:
            panel.add_sound_effect(f"{size.upper()}!", size=size)
        
        result = renderer.render_panel_text(test_image, panel)
        
        # Check that effects were rendered with outlines
        assert mock_draw.text.called
    
    def test_calculate_text_positions(self, renderer):
        """Test text position calculation."""
        panel = Panel(number=1, description="Test")
        panel.add_dialogue("Hero", "Hi")
        panel.add_caption(Caption("Caption"))
        panel.add_sound_effect("POW!")
        
        positions = renderer._calculate_text_positions(
            (800, 600),
            panel
        )
        
        assert 'dialogue' in positions
        assert 'captions' in positions
        assert 'sfx' in positions
        assert len(positions['dialogue']) == 1
        assert len(positions['captions']) == 1
        assert len(positions['sfx']) == 1
    
    def test_get_font_default(self, renderer):
        """Test getting default font."""
        font = renderer._get_font()
        assert font is not None
    
    def test_get_font_with_size(self, renderer):
        """Test getting font with custom size."""
        font1 = renderer._get_font('default', 24)
        font2 = renderer._get_font('default', 32)
        
        # Should be different fonts
        assert font1 is not font2
    
    def test_get_font_caching(self, renderer):
        """Test font caching."""
        font1 = renderer._get_font('default', 24)
        font2 = renderer._get_font('default', 24)
        
        # Should return same cached font
        assert font1 is font2
    
    def test_get_sfx_font_size(self, renderer):
        """Test SFX font size mapping."""
        assert renderer._get_sfx_font_size('small') == 18
        assert renderer._get_sfx_font_size('medium') == 32
        assert renderer._get_sfx_font_size('large') == 48
        assert renderer._get_sfx_font_size('huge') == 64
        assert renderer._get_sfx_font_size(None) == 32
        assert renderer._get_sfx_font_size('unknown') == 32
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_draw_rounded_balloon(self, mock_draw_class, renderer):
        """Test drawing rounded balloon."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        
        style = {
            'fill': 'white',
            'outline': 'black',
            'outline_width': 2,
            'corner_radius': 20
        }
        
        renderer._draw_rounded_balloon(
            mock_draw,
            (10, 10, 100, 50),
            style
        )
        
        mock_draw.rounded_rectangle.assert_called_once()
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_draw_thought_cloud(self, mock_draw_class, renderer):
        """Test drawing thought cloud."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        
        style = {
            'fill': 'white',
            'outline': 'black',
            'outline_width': 2
        }
        
        renderer._draw_thought_cloud(
            mock_draw,
            (10, 10, 100, 50),
            style
        )
        
        # Should draw multiple circles for cloud effect
        assert mock_draw.ellipse.call_count > 5
        mock_draw.rectangle.assert_called_once()
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_draw_spiky_balloon(self, mock_draw_class, renderer):
        """Test drawing spiky balloon."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        
        style = {
            'fill': 'white',
            'outline': 'black',
            'outline_width': 3
        }
        
        renderer._draw_spiky_balloon(
            mock_draw,
            (10, 10, 100, 50),
            style
        )
        
        mock_draw.polygon.assert_called_once()
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_draw_balloon_tail(self, mock_draw_class, renderer):
        """Test drawing balloon tail."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        
        style = {
            'fill': 'white',
            'outline': 'black',
            'outline_width': 2
        }
        
        renderer._draw_balloon_tail(
            mock_draw,
            (10, 10, 100, 50),
            "Hero",
            style
        )
        
        mock_draw.polygon.assert_called_once()
    
    @patch('src.output.text_renderer.ImageDraw.Draw')
    def test_render_dialogue_with_emotion(self, mock_draw_class, renderer, test_image):
        """Test rendering dialogue with emotion."""
        mock_draw = MagicMock()
        mock_draw_class.return_value = mock_draw
        mock_draw.textbbox.return_value = (0, 0, 100, 20)
        
        panel = Panel(number=1, description="Emotional")
        panel.add_dialogue("Hero", "I'm angry!", emotion="angry")
        # Update the type after adding
        if panel.dialogue:
            panel.dialogue[-1].type = DialogueType.SHOUT
        
        result = renderer.render_panel_text(test_image, panel)
        assert result is not None
    
    def test_layout_config(self, renderer, test_image):
        """Test rendering with custom layout config."""
        panel = Panel(number=1, description="Test")
        panel.add_dialogue("Hero", "Hi")
        
        layout_config = {
            'dialogue_zone': (0, 0, 400, 200),
            'caption_zone': (0, 500, 800, 600)
        }
        
        result = renderer.render_panel_text(
            test_image,
            panel,
            layout_config
        )
        
        assert result is not None
        assert result.size == test_image.size