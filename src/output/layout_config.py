"""Shared layout configuration for consistent panel positioning."""

# Page dimensions
DEFAULT_PAGE_WIDTH = 2400
DEFAULT_PAGE_HEIGHT = 3600

# Layout settings
PAGE_MARGIN = 15  # Margin around the entire page
PANEL_GUTTER = 5  # Space between panels

# Layout configurations for different panel counts
PANEL_LAYOUTS = {
    1: {'cols': 1, 'rows': 1},  # Single panel
    2: {'cols': 1, 'rows': 2},  # Two panels stacked
    3: {'cols': 1, 'rows': 3},  # Three panels stacked
    4: {'cols': 2, 'rows': 2},  # 2x2 grid
    5: {'cols': 'special', 'rows': 2},  # 2 on top, 3 on bottom
    6: {'cols': 2, 'rows': 3},  # 2x3 grid
    7: {'cols': 3, 'rows': 3},  # 3x3 with empty spaces
    8: {'cols': 3, 'rows': 3},  # 3x3 with empty space
    9: {'cols': 3, 'rows': 3},  # 3x3 full
    10: {'cols': 3, 'rows': 4},  # 3x4 with empty spaces
    11: {'cols': 3, 'rows': 4},  # 3x4 with empty space
    12: {'cols': 3, 'rows': 4},  # 3x4 full
}


def calculate_panel_position(
    panel_index: int,
    total_panels: int,
    page_width: int = DEFAULT_PAGE_WIDTH,
    page_height: int = DEFAULT_PAGE_HEIGHT,
    margin: int = PAGE_MARGIN,
    gutter: int = PANEL_GUTTER
) -> tuple[int, int, int, int]:
    """Calculate the position for a panel on the page.
    
    ALL panels will be EXACTLY the same size regardless of layout.
    
    Args:
        panel_index: Index of the panel (0-based)
        total_panels: Total number of panels
        page_width: Width of the page
        page_height: Height of the page
        margin: Margin around the page
        gutter: Space between panels
        
    Returns:
        (x1, y1, x2, y2) coordinates for the panel
    """
    # Get layout configuration
    if total_panels in PANEL_LAYOUTS:
        layout = PANEL_LAYOUTS[total_panels]
    else:
        # Default to 4x4 grid for large panel counts
        layout = {'cols': 4, 'rows': 4}
    
    # Calculate usable area
    usable_width = page_width - (2 * margin)
    usable_height = page_height - (2 * margin)
    
    # For ALL layouts, use a uniform grid approach
    # Determine grid size based on total panels
    if total_panels <= 1:
        cols, rows = 1, 1
    elif total_panels <= 2:
        cols, rows = 1, 2
    elif total_panels <= 4:
        cols, rows = 2, 2
    elif total_panels <= 6:
        cols, rows = 2, 3
    elif total_panels <= 9:
        cols, rows = 3, 3
    elif total_panels <= 12:
        cols, rows = 3, 4
    else:
        cols, rows = 4, 4
    
    # Calculate EXACT panel dimensions - all panels same size
    panel_width = (usable_width - (cols - 1) * gutter) // cols
    panel_height = (usable_height - (rows - 1) * gutter) // rows
    
    # Calculate position in grid
    row = panel_index // cols
    col = panel_index % cols
    
    # Calculate exact position
    x1 = margin + col * (panel_width + gutter)
    y1 = margin + row * (panel_height + gutter)
    x2 = x1 + panel_width
    y2 = y1 + panel_height
    
    return (x1, y1, x2, y2)


def get_panel_dimensions(
    total_panels: int,
    page_width: int = DEFAULT_PAGE_WIDTH,
    page_height: int = DEFAULT_PAGE_HEIGHT,
    margin: int = PAGE_MARGIN,
    gutter: int = PANEL_GUTTER
) -> tuple[int, int]:
    """Get the dimensions for panels given the total count.
    
    Args:
        total_panels: Total number of panels
        page_width: Width of the page
        page_height: Height of the page
        margin: Margin around the page
        gutter: Space between panels
        
    Returns:
        (width, height) for each panel
    """
    # Get layout configuration
    if total_panels in PANEL_LAYOUTS:
        layout = PANEL_LAYOUTS[total_panels]
    else:
        layout = {'cols': 4, 'rows': 4}
    
    cols = layout['cols'] if isinstance(layout['cols'], int) else 3
    rows = layout['rows']
    
    # Calculate usable area
    usable_width = page_width - (2 * margin)
    usable_height = page_height - (2 * margin)
    
    # Calculate panel dimensions
    panel_width = (usable_width - (cols - 1) * gutter) // cols
    panel_height = (usable_height - (rows - 1) * gutter) // rows
    
    return (panel_width, panel_height)