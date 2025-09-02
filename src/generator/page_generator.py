"""Page generator for creating complete comic pages in a single pass."""

import logging
from typing import List, Optional, Dict, Any
from PIL import Image
from io import BytesIO

from src.models import Page, Panel

logger = logging.getLogger(__name__)


class PageGenerator:
    """Generates complete comic pages in a single API call."""
    
    def __init__(self, gemini_client):
        """Initialize page generator.
        
        Args:
            gemini_client: Gemini API client
        """
        self.client = gemini_client
        self.page_width = 2400
        self.page_height = 3600
        
    async def generate_page(
        self,
        page: Page,
        previous_pages: Optional[List[Image.Image]] = None,
        style_context: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generate a complete comic page with all panels.
        
        Args:
            page: Page object containing panels to generate
            previous_pages: Previous page images for context (PIL Images)
            style_context: Style configuration
            
        Returns:
            Complete page image as bytes
        """
        import time
        start_time = time.time()
        
        try:
            # Build comprehensive page prompt
            prompt = self._build_page_prompt(page)
            
            # Log prompt for debugging
            logger.info(f"Generating page {page.number} with {len(page.panels)} panels")
            logger.debug(f"Page prompt:\n{prompt}")
            
            # Prepare previous pages as context (limit to last 2 pages)
            context_images = previous_pages[-2:] if previous_pages else []
            
            # Call Gemini with prompt and context
            page_image_bytes = await self.client.generate_page_image(
                prompt=prompt,
                context_images=context_images,
                style_config=style_context
            )
            
            generation_time = time.time() - start_time
            logger.info(f"Page {page.number} generated in {generation_time:.2f}s")
            
            return page_image_bytes
            
        except Exception as e:
            logger.error(f"Error generating page {page.number}: {e}")
            raise
    
    def _build_page_prompt(self, page: Page) -> str:
        """Build detailed prompt for entire page generation.
        
        Args:
            page: Page object with panels
            
        Returns:
            Detailed prompt string
        """
        num_panels = len(page.panels)
        
        prompt = f"""Generate a complete comic book page with EXACTLY {num_panels} panels.

PAGE SPECIFICATIONS:
- Dimensions: EXACTLY 2400x3600 pixels
- Layout: {self._get_layout_description(num_panels)}
- Margins: 15px around the entire page
- Panel gutters: 5px between panels
- All panels must be EXACTLY the same size
- Black panel borders (2px width)

PANEL CONTENT:
{self._build_panels_description(page.panels)}

CRITICAL REQUIREMENTS:
1. Generate the ENTIRE page as a single 2400x3600px image
2. All {num_panels} panels must be clearly separated with black borders
3. Each panel must contain its specified content EXACTLY as described
4. ALL TEXT IN DOUBLE QUOTES MUST APPEAR EXACTLY AS WRITTEN IN THE IMAGE
5. ALL text (captions, dialogue, sound effects) must be INSIDE panel boundaries
6. Captions (text after "Caption:") should be in yellow/white rectangular boxes at top or bottom of panels
7. Character dialogue (text after character names) should be in white speech bubbles with tails pointing to speakers
8. Thought bubbles (marked with "Thought Bubble") should be cloud-shaped
9. Sound effects (text after "SFX:") should be stylized text integrated into the artwork
10. Maintain consistent art style across all panels
11. Maintain consistent character appearances across all panels
12. The page should read naturally from top-left to bottom-right

STYLE REQUIREMENTS:
- Professional comic book art style
- Clear, readable text in appropriate bubbles/boxes
- Consistent color palette throughout the page
- Dynamic and engaging visual composition

OUTPUT: One complete comic page image of EXACTLY 2400x3600 pixels containing all {num_panels} panels arranged in the specified layout."""
        
        return prompt
    
    def _get_layout_description(self, num_panels: int) -> str:
        """Get layout description for number of panels.
        
        Args:
            num_panels: Number of panels on the page
            
        Returns:
            Layout description string
        """
        layouts = {
            1: "Single full-page panel filling the entire page",
            2: "Two panels stacked vertically (1x2 grid) of equal size",
            3: "Three panels stacked vertically (1x3 grid) of equal size", 
            4: "Four panels in a 2x2 grid, all exactly the same size",
            5: "Five panels: 2 equal-sized panels on top row, 3 equal-sized panels on bottom row",
            6: "Six panels in a 2x3 grid (2 columns, 3 rows), all exactly the same size",
            7: "Seven panels: 3 panels top row, 3 panels middle row, 1 full-width panel bottom",
            8: "Eight panels in a 2x4 grid, all exactly the same size",
            9: "Nine panels in a 3x3 grid, all exactly the same size",
            10: "Ten panels in a 2x5 grid, all exactly the same size",
            11: "Eleven panels: 3x3 grid plus 2 panels at bottom",
            12: "Twelve panels in a 3x4 grid, all exactly the same size"
        }
        return layouts.get(num_panels, f"{num_panels} panels in an appropriate grid layout with all panels the same size")
    
    def _build_panels_description(self, panels: List[Panel]) -> str:
        """Build detailed description of all panels.
        
        Args:
            panels: List of Panel objects
            
        Returns:
            Combined panel descriptions
        """
        descriptions = []
        
        for i, panel in enumerate(panels, 1):
            # Use raw_text if available, otherwise use description
            content = getattr(panel, 'raw_text', panel.description)
            
            # Process the content to add quotes around text elements
            processed_content = self._add_quotes_to_text(content)
            
            panel_desc = f"""
PANEL {i} (Position: {self._get_panel_position(i, len(panels))}):
{processed_content}

Visual requirements for Panel {i}:
- This panel must be clearly separated from other panels with a black border
- All dialogue, captions, and sound effects must be INSIDE this panel's boundaries
- All text in quotes must appear EXACTLY as written
- Maintain character consistency with previous panels
- Follow standard comic book panel composition"""
            
            descriptions.append(panel_desc.strip())
        
        return "\n\n".join(descriptions)
    
    def _add_quotes_to_text(self, content: str) -> str:
        """Add quotes around text elements that should appear in the image.
        
        Args:
            content: Panel content text
            
        Returns:
            Content with quoted text elements
        """
        import re
        
        lines = content.split('\n')
        processed_lines = []
        
        for line in lines:
            # Handle Caption: lines
            if line.startswith('Caption:'):
                text = line[8:].strip()
                processed_lines.append(f'Caption: "{text}"')
            
            # Handle character dialogue (Name: dialogue or Name (emotion): dialogue)
            elif ':' in line and not line.startswith('Setting:') and not line.startswith('SFX:'):
                # Check if it looks like character dialogue
                parts = line.split(':', 1)
                if len(parts) == 2:
                    speaker = parts[0].strip()
                    dialogue = parts[1].strip()
                    
                    # Check if speaker looks like a character name (could include emotion in parens)
                    if speaker and not any(word in speaker.lower() for word in ['setting', 'panel', 'note']):
                        # Handle thought bubbles specially
                        if '(Thought' in speaker or '(thought' in speaker:
                            processed_lines.append(f'{speaker}: "{dialogue}"')
                        else:
                            processed_lines.append(f'{speaker}: "{dialogue}"')
            
            # Handle SFX: lines
            elif line.startswith('SFX:'):
                text = line[4:].strip()
                processed_lines.append(f'SFX: "{text}"')
            
            # Leave other lines unchanged (like Setting: descriptions)
            else:
                processed_lines.append(line)
        
        return '\n'.join(processed_lines)
    
    def _get_panel_position(self, panel_num: int, total_panels: int) -> str:
        """Get position description for a panel.
        
        Args:
            panel_num: Panel number (1-based)
            total_panels: Total number of panels
            
        Returns:
            Position description
        """
        if total_panels == 1:
            return "Full page"
        elif total_panels == 2:
            return "Top half" if panel_num == 1 else "Bottom half"
        elif total_panels == 4:
            positions = ["Top-left", "Top-right", "Bottom-left", "Bottom-right"]
            return positions[panel_num - 1]
        elif total_panels == 6:
            positions = ["Top-left", "Top-right", "Middle-left", "Middle-right", "Bottom-left", "Bottom-right"]
            return positions[panel_num - 1]
        elif total_panels == 9:
            row = (panel_num - 1) // 3
            col = (panel_num - 1) % 3
            rows = ["Top", "Middle", "Bottom"]
            cols = ["left", "center", "right"]
            return f"{rows[row]}-{cols[col]}"
        else:
            return f"Panel {panel_num} of {total_panels}"