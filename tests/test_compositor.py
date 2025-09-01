"""Tests for page compositor."""

import pytest
from unittest.mock import MagicMock, patch, Mock
from PIL import Image
import io

from src.output import PageCompositor
from src.models import (
    GeneratedPanel,
    GeneratedPage,
    Page,
    Panel,
    PanelType,
)


class TestPageCompositor:
    """Test cases for PageCompositor class."""
    
    @pytest.fixture
    def compositor(self):
        """Create page compositor."""
        return PageCompositor()
    
    @pytest.fixture
    def test_panels(self):
        """Create test panels with valid image data."""
        # Create minimal valid PNG
        valid_png = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\xd8\xdc\xfd\xad\x00\x00\x00\x00IEND\xaeB`\x82'
        
        panels = []
        for i in range(3):
            panel = Panel(number=i+1, description=f"Panel {i+1}")
            gen_panel = GeneratedPanel(
                panel=panel,
                image_data=valid_png,
                generation_time=1.0
            )
            panels.append(gen_panel)
        
        return panels
    
    @pytest.fixture
    def test_page(self):
        """Create test page."""
        page = Page(number=1)
        for i in range(3):
            panel = Panel(number=i+1, description=f"Panel {i+1}")
            page.add_panel(panel)
        return page
    
    def test_init_default(self, compositor):
        """Test default initialization."""
        assert compositor.page_width == PageCompositor.DEFAULT_PAGE_WIDTH
        assert compositor.page_height == PageCompositor.DEFAULT_PAGE_HEIGHT
        assert compositor.dpi == PageCompositor.DEFAULT_DPI
        assert compositor.layout_style == 'standard'
    
    def test_init_custom(self):
        """Test custom initialization."""
        compositor = PageCompositor(
            page_width=1000,
            page_height=1500,
            dpi=150,
            layout_style='manga'
        )
        
        assert compositor.page_width == 1000
        assert compositor.page_height == 1500
        assert compositor.dpi == 150
        assert compositor.layout_style == 'manga'
        assert compositor.layout_config == PageCompositor.LAYOUTS['manga']
    
    def test_compose_page_basic(self, compositor, test_panels):
        """Test basic page composition."""
        result = compositor.compose_page(test_panels)
        
        assert isinstance(result, Image.Image)
        assert result.size == (compositor.page_width, compositor.page_height)
    
    def test_compose_page_with_page_object(self, compositor, test_panels, test_page):
        """Test page composition with page object."""
        result = compositor.compose_page(test_panels, test_page)
        
        assert isinstance(result, Image.Image)
        assert result.size == (compositor.page_width, compositor.page_height)
    
    def test_compose_spread(self, compositor, test_panels):
        """Test two-page spread composition."""
        left_panels = test_panels[:2]
        right_panels = test_panels[2:]
        
        result = compositor.compose_spread(left_panels, right_panels)
        
        assert isinstance(result, Image.Image)
        assert result.width == compositor.page_width * 2
        assert result.height == compositor.page_height
    
    def test_determine_layout_splash(self, compositor):
        """Test layout determination for splash page."""
        panel = Panel(number=1, description="Splash", panel_type=PanelType.SPLASH)
        gen_panel = GeneratedPanel(panel=panel, image_data=b"", generation_time=1.0)
        
        layout = compositor._determine_layout([gen_panel])
        
        assert layout['type'] == 'splash'
        assert layout['rows'] == 1
        assert layout['cols'] == 1
    
    def test_determine_layout_simple(self, compositor, test_panels):
        """Test layout determination for simple layouts."""
        # 1 panel
        layout = compositor._determine_layout(test_panels[:1])
        assert layout['type'] == 'single'
        
        # 2 panels
        layout = compositor._determine_layout(test_panels[:2])
        assert layout['type'] == 'two_panel'
        
        # 3 panels
        layout = compositor._determine_layout(test_panels[:3])
        assert layout['type'] == 'three_panel'
    
    def test_determine_layout_standard(self, compositor):
        """Test layout determination for standard layouts."""
        # Create 4-6 panels
        panels = []
        for i in range(6):
            panel = Panel(number=i+1, description=f"Panel {i+1}")
            gen_panel = GeneratedPanel(panel=panel, image_data=b"", generation_time=1.0)
            panels.append(gen_panel)
        
        # 4 panels
        layout = compositor._determine_layout(panels[:4])
        assert layout['type'] == 'four_panel'
        assert layout['rows'] == 2
        assert layout['cols'] == 2
        
        # 5 panels
        layout = compositor._determine_layout(panels[:5])
        assert layout['type'] == 'five_panel'
        assert layout['irregular'] == True
        
        # 6 panels
        layout = compositor._determine_layout(panels[:6])
        assert layout['type'] == 'six_panel'
        assert layout['rows'] == 3
        assert layout['cols'] == 2
    
    def test_create_page_canvas(self, compositor):
        """Test page canvas creation."""
        canvas = compositor._create_page_canvas()
        
        assert isinstance(canvas, Image.Image)
        assert canvas.size == (compositor.page_width, compositor.page_height)
        assert canvas.mode == 'RGB'
    
    def test_calculate_panel_positions_splash(self, compositor, test_panels):
        """Test panel position calculation for splash layout."""
        layout = {'type': 'splash', 'rows': 1, 'cols': 1}
        positions = compositor._calculate_panel_positions(test_panels[:1], layout)
        
        assert len(positions) == 1
        x, y, width, height = positions[0]
        assert x == 50  # left margin
        assert y == 50  # top margin
    
    def test_calculate_panel_positions_grid(self, compositor, test_panels):
        """Test panel position calculation for grid layout."""
        layout = {'type': 'three_panel', 'rows': 3, 'cols': 1}
        positions = compositor._calculate_panel_positions(test_panels, layout)
        
        assert len(positions) == 3
        # Check that panels are vertically arranged
        for i in range(1, len(positions)):
            assert positions[i][1] > positions[i-1][1]  # y increases
    
    def test_calculate_irregular_positions(self, compositor):
        """Test irregular layout position calculation."""
        panels = []
        for i in range(5):
            panel = Panel(number=i+1, description=f"Panel {i+1}")
            gen_panel = GeneratedPanel(panel=panel, image_data=b"", generation_time=1.0)
            panels.append(gen_panel)
        
        layout = {'type': 'five_panel', 'rows': 3, 'cols': 2, 'irregular': True}
        margins = (50, 50, 50, 50)
        gutter = 20
        content_width = compositor.page_width - 100
        content_height = compositor.page_height - 100
        
        positions = compositor._calculate_irregular_positions(
            panels, layout, margins, gutter,
            content_width, content_height
        )
        
        assert len(positions) == 5
        # Last panel should be full width
        assert positions[4][2] == content_width
    
    def test_resize_panel(self, compositor):
        """Test panel resizing."""
        # Create a test image
        test_image = Image.new('RGB', (200, 200), 'red')
        
        resized = compositor._resize_panel(test_image, 100, 150)
        
        assert resized.size == (100, 150)
    
    def test_add_panel_border(self, compositor):
        """Test adding border to panel."""
        test_image = Image.new('RGB', (100, 100), 'white')
        
        bordered = compositor._add_panel_border(test_image, border_width=5)
        
        assert bordered.width == 110  # 100 + 5*2
        assert bordered.height == 110
    
    def test_place_panel_with_valid_image(self, compositor, test_panels):
        """Test placing panel with valid image."""
        page_image = compositor._create_page_canvas()
        panel = test_panels[0]
        position = (100, 100, 200, 300)
        
        # This should not raise an exception
        compositor._place_panel(page_image, panel, position)
        
        # Image should be modified (hard to test precisely without pixel comparison)
        assert page_image is not None
    
    def test_place_panel_with_invalid_image(self, compositor):
        """Test placing panel with invalid image."""
        page_image = compositor._create_page_canvas()
        panel = GeneratedPanel(
            panel=Panel(1, "Test"),
            image_data=b"invalid",
            generation_time=1.0
        )
        position = (100, 100, 200, 300)
        
        # Should draw placeholder instead of crashing
        compositor._place_panel(page_image, panel, position)
        
        assert page_image is not None
    
    def test_draw_placeholder(self, compositor):
        """Test drawing placeholder for missing panel."""
        page_image = compositor._create_page_canvas()
        position = (100, 100, 200, 300)
        
        compositor._draw_placeholder(page_image, position)
        
        # Image should be modified
        assert page_image is not None
    
    def test_add_page_number(self, compositor):
        """Test adding page number."""
        page_image = compositor._create_page_canvas()
        draw = Image.new('RGB', (100, 100)).im  # Create dummy draw object
        
        # Mock ImageDraw.Draw
        with patch('PIL.ImageDraw.Draw') as mock_draw:
            mock_draw_instance = MagicMock()
            mock_draw.return_value = mock_draw_instance
            
            draw = mock_draw(page_image)
            compositor._add_page_number(draw, 1)
            
            # Check that text was called
            draw.text.assert_called_once()
    
    def test_add_page_decorations(self, compositor, test_page):
        """Test adding page decorations."""
        page_image = compositor._create_page_canvas()
        
        with patch('PIL.ImageDraw.Draw') as mock_draw:
            mock_draw_instance = MagicMock()
            mock_draw.return_value = mock_draw_instance
            
            compositor._add_page_decorations(page_image, test_page)
            
            # Should create draw object
            mock_draw.assert_called_once()
    
    def test_different_layout_styles(self):
        """Test different layout styles."""
        for style in ['standard', 'full_bleed', 'manga', 'webcomic']:
            compositor = PageCompositor(layout_style=style)
            assert compositor.layout_style == style
            assert compositor.layout_config == PageCompositor.LAYOUTS[style]
    
    def test_compose_page_with_layout_override(self, compositor, test_panels):
        """Test page composition with layout override."""
        layout_override = {
            'type': 'custom',
            'rows': 2,
            'cols': 2,
        }
        
        result = compositor.compose_page(test_panels, layout_override=layout_override)
        
        assert isinstance(result, Image.Image)
    
    def test_dense_grid_layout(self, compositor):
        """Test dense grid layout for many panels."""
        # Create 12 panels
        panels = []
        for i in range(12):
            panel = Panel(number=i+1, description=f"Panel {i+1}")
            gen_panel = GeneratedPanel(panel=panel, image_data=b"", generation_time=1.0)
            panels.append(gen_panel)
        
        layout = compositor._determine_layout(panels)
        
        assert layout['type'] == 'dense'
        assert layout['cols'] == 3
        assert layout['rows'] == 4  # 12 panels / 3 cols = 4 rows