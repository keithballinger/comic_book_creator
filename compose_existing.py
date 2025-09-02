#!/usr/bin/env python
"""Compose existing panels into comic pages."""

import sys
from pathlib import Path
from PIL import Image
import io

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.output import PageCompositor
from src.models import GeneratedPanel, Page

def compose_existing_panels(output_dir: str):
    """Compose existing panels into pages."""
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"Output directory {output_dir} does not exist")
        return
    
    # Initialize compositor
    compositor = PageCompositor(
        page_width=2400,
        page_height=3600,
        dpi=300,
        layout_style='standard'
    )
    
    # Process each page directory
    page_dirs = sorted([d for d in output_path.iterdir() if d.is_dir() and d.name.startswith('page_')])
    
    for page_dir in page_dirs:
        print(f"Processing {page_dir.name}...")
        
        # Load panels
        panel_files = sorted(page_dir.glob("panel_*.png"))
        panels = []
        
        for panel_file in panel_files:
            with open(panel_file, 'rb') as f:
                image_data = f.read()
                panel = GeneratedPanel(
                    panel=None,
                    image_data=image_data,
                    generation_time=0
                )
                panels.append(panel)
        
        if panels:
            # Create a page object
            page = Page(number=int(page_dir.name.split('_')[1]))
            
            # Compose the page
            try:
                page_image = compositor.compose_page(panels, page)
                page_path = output_path / f"{page_dir.name}_complete.png"
                page_image.save(page_path)
                print(f"  Saved composed page to {page_path}")
            except Exception as e:
                print(f"  Error composing page: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        compose_existing_panels(sys.argv[1])
    else:
        # Default to latest output
        output_dirs = sorted(Path("output").glob("comic_*"))
        if output_dirs:
            compose_existing_panels(str(output_dirs[-1]))
        else:
            print("No output directories found")