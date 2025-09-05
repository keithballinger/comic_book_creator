"""Page compositor for arranging panels into comic pages."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageOps
import numpy as np

from src.models import (
    GeneratedPanel,
    GeneratedPage,
    Page,
    Panel,
    PanelType,
)
from src.output.layout_config import (
    DEFAULT_PAGE_WIDTH,
    DEFAULT_PAGE_HEIGHT,
    PAGE_MARGIN,
    PANEL_GUTTER,
    calculate_panel_position,
    get_panel_dimensions,
)

logger = logging.getLogger(__name__)


class PageCompositor:
    """Composes multiple panels into a complete comic page."""
    
    # Use shared layout configuration defaults
    DEFAULT_DPI = 300
    
    # Layout configurations with shared values
    LAYOUTS = {
        'standard': {
            'margins': (PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN, PAGE_MARGIN),  # top, right, bottom, left
            'gutter': PANEL_GUTTER,  # Space between panels
            'background': 'white',
        },
        'full_bleed': {
            'margins': (0, 0, 0, 0),
            'gutter': 0,
            'background': 'black',
        },
        'manga': {
            'margins': (40, 40, 40, 40),
            'gutter': 15,
            'background': 'white',
            'reading_order': 'right_to_left',
        },
        'webcomic': {
            'margins': (20, 20, 20, 20),
            'gutter': 30,
            'background': '#f0f0f0',
            'vertical_scroll': True,
        },
    }
    
    def __init__(
        self,
        page_width: Optional[int] = None,
        page_height: Optional[int] = None,
        dpi: int = DEFAULT_DPI,
        layout_style: str = 'standard'
    ):
        """Initialize page compositor.
        
        Args:
            page_width: Page width in pixels
            page_height: Page height in pixels
            dpi: Dots per inch for output
            layout_style: Layout style name
        """
        self.page_width = page_width or DEFAULT_PAGE_WIDTH
        self.page_height = page_height or DEFAULT_PAGE_HEIGHT
        self.dpi = dpi
        self.layout_style = layout_style
        self.layout_config = self.LAYOUTS.get(layout_style, self.LAYOUTS['standard'])
    
    def compose_page(
        self,
        panels: List[GeneratedPanel],
        page: Optional[Page] = None,
        layout_override: Optional[Dict[str, Any]] = None
    ) -> Image.Image:
        """Compose panels into a complete page.
        
        Args:
            panels: List of generated panels
            page: Page object with layout information
            layout_override: Optional layout override
            
        Returns:
            Composed page image
        """
        # Get layout configuration
        layout = layout_override or self._determine_layout(panels, page)
        
        # Create page canvas
        page_image = self._create_page_canvas()
        
        # Calculate panel positions
        panel_positions = self._calculate_panel_positions(panels, layout)
        
        # Place panels on page
        for panel, position in zip(panels, panel_positions):
            if panel.image_data:
                self._place_panel(page_image, panel, position)
        
        # Add page decorations (borders, page numbers, etc.)
        if page:
            self._add_page_decorations(page_image, page)
        
        return page_image
    
    def compose_spread(
        self,
        left_panels: List[GeneratedPanel],
        right_panels: List[GeneratedPanel],
        left_page: Optional[Page] = None,
        right_page: Optional[Page] = None
    ) -> Image.Image:
        """Compose a two-page spread.
        
        Args:
            left_panels: Panels for left page
            right_panels: Panels for right page
            left_page: Left page object
            right_page: Right page object
            
        Returns:
            Composed spread image
        """
        # Create individual pages
        left_image = self.compose_page(left_panels, left_page)
        right_image = self.compose_page(right_panels, right_page)
        
        # Create spread canvas
        spread_width = self.page_width * 2
        spread_image = Image.new('RGB', (spread_width, self.page_height), 'white')
        
        # Paste pages
        spread_image.paste(left_image, (0, 0))
        spread_image.paste(right_image, (self.page_width, 0))
        
        # Add center line
        draw = ImageDraw.Draw(spread_image)
        center_x = self.page_width
        draw.line(
            [(center_x, 0), (center_x, self.page_height)],
            fill='gray',
            width=1
        )
        
        return spread_image
    
    def _determine_layout(
        self,
        panels: List[GeneratedPanel],
        page: Optional[Page] = None
    ) -> Dict[str, Any]:
        """Determine the layout for panels.
        
        Args:
            panels: List of panels
            page: Page object with layout hints
            
        Returns:
            Layout configuration
        """
        num_panels = len(panels)
        
        # Check for splash page
        if num_panels == 1 and panels[0].panel and panels[0].panel.panel_type == PanelType.SPLASH:
            return self._get_splash_layout()
        
        # Standard layouts based on panel count
        if num_panels <= 3:
            return self._get_simple_grid_layout(num_panels)
        elif num_panels <= 6:
            return self._get_standard_grid_layout(num_panels)
        elif num_panels <= 9:
            return self._get_complex_grid_layout(num_panels)
        else:
            return self._get_dense_grid_layout(num_panels)
    
    def _get_splash_layout(self) -> Dict[str, Any]:
        """Get layout for splash page."""
        return {
            'type': 'splash',
            'rows': 1,
            'cols': 1,
            'panel_sizes': [(1.0, 1.0)],  # Full page
        }
    
    def _get_simple_grid_layout(self, num_panels: int) -> Dict[str, Any]:
        """Get layout for 1-3 panels."""
        if num_panels == 1:
            return {'type': 'single', 'rows': 1, 'cols': 1}
        elif num_panels == 2:
            return {'type': 'two_panel', 'rows': 2, 'cols': 1}
        else:  # 3 panels
            return {'type': 'three_panel', 'rows': 3, 'cols': 1}
    
    def _get_standard_grid_layout(self, num_panels: int) -> Dict[str, Any]:
        """Get layout for 4-6 panels."""
        if num_panels == 4:
            return {'type': 'four_panel', 'rows': 2, 'cols': 2}
        elif num_panels == 5:
            return {'type': 'five_panel', 'rows': 3, 'cols': 2, 'irregular': True}
        else:  # 6 panels
            return {'type': 'six_panel', 'rows': 3, 'cols': 2}
    
    def _get_complex_grid_layout(self, num_panels: int) -> Dict[str, Any]:
        """Get layout for 7-9 panels."""
        if num_panels == 7:
            return {'type': 'seven_panel', 'rows': 3, 'cols': 3, 'irregular': True}
        elif num_panels == 8:
            return {'type': 'eight_panel', 'rows': 4, 'cols': 2}
        else:  # 9 panels
            return {'type': 'nine_panel', 'rows': 3, 'cols': 3}
    
    def _get_dense_grid_layout(self, num_panels: int) -> Dict[str, Any]:
        """Get layout for 10+ panels."""
        cols = 3
        rows = (num_panels + cols - 1) // cols
        return {'type': 'dense', 'rows': rows, 'cols': cols}
    
    def _create_page_canvas(self) -> Image.Image:
        """Create blank page canvas.
        
        Returns:
            Blank page image
        """
        background_color = self.layout_config.get('background', 'white')
        return Image.new('RGB', (self.page_width, self.page_height), background_color)
    
    def _calculate_panel_positions(
        self,
        panels: List[GeneratedPanel],
        layout: Dict[str, Any]
    ) -> List[Tuple[int, int, int, int]]:
        """Calculate panel positions on page.
        
        Args:
            panels: List of panels
            layout: Layout configuration
            
        Returns:
            List of (x1, y1, x2, y2) tuples (coordinates for panel corners)
        """
        positions = []
        num_panels = len(panels)
        
        # Handle special layouts
        if layout['type'] == 'splash':
            # Full page panel
            margins = self.layout_config['margins']
            positions.append((
                margins[3],
                margins[0],
                self.page_width - margins[1],
                self.page_height - margins[2]
            ))
            return positions
        
        # Use shared layout calculation for standard layouts
        for i in range(num_panels):
            position = calculate_panel_position(
                i,
                num_panels,
                self.page_width,
                self.page_height,
                self.layout_config['margins'][0],  # Use top margin as general margin
                self.layout_config['gutter']
            )
            positions.append(position)
        
        return positions
    
    def _calculate_irregular_positions(
        self,
        panels: List[GeneratedPanel],
        layout: Dict[str, Any],
        margins: Tuple[int, int, int, int],
        gutter: int,
        content_width: int,
        content_height: int
    ) -> List[Tuple[int, int, int, int]]:
        """Calculate positions for irregular layouts.
        
        Args:
            panels: List of panels
            layout: Layout configuration
            margins: Page margins
            gutter: Gutter size
            content_width: Available width
            content_height: Available height
            
        Returns:
            List of panel positions
        """
        positions = []
        num_panels = len(panels)
        
        if num_panels == 5:
            # 2-2-1 layout
            half_width = (content_width - gutter) // 2
            third_height = (content_height - 2 * gutter) // 3
            
            # Top row (2 panels)
            positions.append((margins[3], margins[0], half_width, third_height))
            positions.append((margins[3] + half_width + gutter, margins[0], half_width, third_height))
            
            # Middle row (2 panels)
            y_mid = margins[0] + third_height + gutter
            positions.append((margins[3], y_mid, half_width, third_height))
            positions.append((margins[3] + half_width + gutter, y_mid, half_width, third_height))
            
            # Bottom row (1 panel, full width)
            y_bot = margins[0] + 2 * (third_height + gutter)
            positions.append((margins[3], y_bot, content_width, third_height))
            
        elif num_panels == 7:
            # 3-3-1 layout
            third_width = (content_width - 2 * gutter) // 3
            third_height = (content_height - 2 * gutter) // 3
            
            # Top two rows (3 panels each)
            for row in range(2):
                y = margins[0] + row * (third_height + gutter)
                for col in range(3):
                    x = margins[3] + col * (third_width + gutter)
                    positions.append((x, y, third_width, third_height))
            
            # Bottom row (1 panel, full width)
            y_bot = margins[0] + 2 * (third_height + gutter)
            positions.append((margins[3], y_bot, content_width, third_height))
            
        else:
            # Fall back to regular grid
            return self._calculate_regular_grid_positions(
                panels, layout, margins, gutter,
                content_width, content_height
            )
        
        return positions
    
    def _calculate_regular_grid_positions(
        self,
        panels: List[GeneratedPanel],
        layout: Dict[str, Any],
        margins: Tuple[int, int, int, int],
        gutter: int,
        content_width: int,
        content_height: int
    ) -> List[Tuple[int, int, int, int]]:
        """Calculate regular grid positions.
        
        Args:
            panels: List of panels
            layout: Layout configuration
            margins: Page margins
            gutter: Gutter size
            content_width: Available width
            content_height: Available height
            
        Returns:
            List of panel positions
        """
        positions = []
        rows = layout.get('rows', 1)
        cols = layout.get('cols', 1)
        
        panel_width = (content_width - (cols - 1) * gutter) // cols
        panel_height = (content_height - (rows - 1) * gutter) // rows
        
        for i in range(len(panels)):
            row = i // cols
            col = i % cols
            
            x = margins[3] + col * (panel_width + gutter)
            y = margins[0] + row * (panel_height + gutter)
            
            positions.append((x, y, panel_width, panel_height))
        
        return positions
    
    def _place_panel(
        self,
        page_image: Image.Image,
        panel: GeneratedPanel,
        position: Tuple[int, int, int, int]
    ):
        """Place a panel on the page.
        
        Args:
            page_image: Page image to modify
            panel: Panel to place
            position: (x1, y1, x2, y2) position
        """
        import io
        
        x1, y1, x2, y2 = position
        width = x2 - x1
        height = y2 - y1
        
        try:
            # Load panel image
            panel_img = Image.open(io.BytesIO(panel.image_data))
            
            # Resize to fit position
            panel_img = self._resize_panel(panel_img, width, height)
            
            # Add border
            panel_img = self._add_panel_border(panel_img)
            
            # Paste onto page
            page_image.paste(panel_img, (x1, y1))
            
        except Exception as e:
            logger.error(f"Error placing panel: {e}")
            # Draw placeholder
            self._draw_placeholder(page_image, position)
    
    def _resize_panel(
        self,
        panel_image: Image.Image,
        target_width: int,
        target_height: int
    ) -> Image.Image:
        """Resize panel to fit target dimensions.
        
        Args:
            panel_image: Panel image
            target_width: Target width
            target_height: Target height
            
        Returns:
            Resized panel image
        """
        # Calculate scaling
        scale_x = target_width / panel_image.width
        scale_y = target_height / panel_image.height
        
        # Use the smaller scale to maintain aspect ratio
        scale = min(scale_x, scale_y)
        
        new_width = int(panel_image.width * scale)
        new_height = int(panel_image.height * scale)
        
        # Resize
        resized = panel_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create canvas at target size
        canvas = Image.new('RGB', (target_width, target_height), 'white')
        
        # Center the resized image
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        canvas.paste(resized, (x_offset, y_offset))
        
        return canvas
    
    def _add_panel_border(
        self,
        panel_image: Image.Image,
        border_width: int = 2,
        border_color: str = 'black'
    ) -> Image.Image:
        """Add border to panel.
        
        Args:
            panel_image: Panel image
            border_width: Border width in pixels
            border_color: Border color
            
        Returns:
            Panel with border
        """
        return ImageOps.expand(panel_image, border=border_width, fill=border_color)
    
    def _draw_placeholder(
        self,
        page_image: Image.Image,
        position: Tuple[int, int, int, int]
    ):
        """Draw placeholder for missing panel.
        
        Args:
            page_image: Page image
            position: Panel position (x1, y1, x2, y2)
        """
        draw = ImageDraw.Draw(page_image)
        x1, y1, x2, y2 = position
        
        # Draw rectangle
        draw.rectangle(
            [x1, y1, x2, y2],
            outline='gray',
            width=2
        )
        
        # Draw X
        draw.line([(x1, y1), (x2, y2)], fill='gray', width=1)
        draw.line([(x2, y1), (x1, y2)], fill='gray', width=1)
    
    def _add_page_decorations(
        self,
        page_image: Image.Image,
        page: Page
    ):
        """Add page decorations like page numbers.
        
        Args:
            page_image: Page image
            page: Page object
        """
        draw = ImageDraw.Draw(page_image)
        
        # Add page number
        if page.number:
            self._add_page_number(draw, page.number)
        
        # Add issue/title if available
        if hasattr(page, 'metadata') and page.metadata:
            if title := page.metadata.get('title'):
                self._add_title(draw, title)
    
    def _add_page_number(
        self,
        draw: ImageDraw.Draw,
        page_number: int
    ):
        """Add page number to page.
        
        Args:
            draw: Draw object
            page_number: Page number
        """
        # Position at bottom center
        text = str(page_number)
        x = self.page_width // 2
        y = self.page_height - 30
        
        # Draw page number
        draw.text(
            (x, y),
            text,
            fill='black',
            anchor='mm'
        )
    
    def _add_title(
        self,
        draw: ImageDraw.Draw,
        title: str
    ):
        """Add title to page header.
        
        Args:
            draw: Draw object
            title: Title text
        """
        # Position at top center
        x = self.page_width // 2
        y = 20
        
        draw.text(
            (x, y),
            title,
            fill='gray',
            anchor='mm'
        )