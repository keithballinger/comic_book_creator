"""Reference sheet builder for maintaining consistency across panels."""

import io
import logging
from typing import List, Dict, Optional, Tuple, Any
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from src.output.layout_config import calculate_panel_position

logger = logging.getLogger(__name__)


@dataclass
class ReferenceElement:
    """A single element in the reference sheet."""
    name: str
    image: Image.Image
    category: str  # 'character', 'location', 'prop', 'panel'
    metadata: Dict[str, Any] = None


class ReferenceSheetBuilder:
    """Builds comprehensive reference sheets for panel generation."""
    
    def __init__(
        self,
        page_width: int = 2400,
        page_height: int = 3600,
        reference_strip_height: int = 400
    ):
        """Initialize reference sheet builder.
        
        Args:
            page_width: Width of comic page
            page_height: Height of comic page  
            reference_strip_height: Height of reference strips
        """
        self.page_width = page_width
        self.page_height = page_height
        self.reference_strip_height = reference_strip_height
        
        # Store reference elements
        self.character_refs: List[ReferenceElement] = []
        self.location_refs: List[ReferenceElement] = []
        self.prop_refs: List[ReferenceElement] = []
        
        # Current page state
        self.current_page_canvas: Optional[Image.Image] = None
        self.completed_panels: List[Tuple[Image.Image, Dict]] = []
    
    def create_comprehensive_reference(
        self,
        page_in_progress: Optional[Image.Image] = None,
        target_panel_position: Optional[Tuple[int, int, int, int]] = None,
        panel_number: int = 0,
        total_panels: int = 0
    ) -> bytes:
        """Create a comprehensive reference sheet.
        
        Args:
            page_in_progress: Current state of the page being built
            target_panel_position: (x1, y1, x2, y2) position for the next panel
            panel_number: Current panel number
            total_panels: Total panels in page
            
        Returns:
            Reference sheet as PNG bytes
        """
        # Calculate dimensions
        # Reference sheet will be taller to accommodate reference strips
        sheet_height = self.page_height + (self.reference_strip_height * 3)  # 3 strips
        sheet = Image.new('RGB', (self.page_width, sheet_height), 'white')
        draw = ImageDraw.Draw(sheet)
        
        # Section 1: Page in progress (top section)
        if page_in_progress:
            sheet.paste(page_in_progress, (0, 0))
            
            # Highlight target panel area
            if target_panel_position:
                x1, y1, x2, y2 = target_panel_position
                # Draw a red border around where the next panel will go
                draw.rectangle([x1-2, y1-2, x2+2, y2+2], outline='red', width=3)
                # Add panel number
                draw.text((x1+5, y1+5), f"PANEL {panel_number}", fill='red')
        else:
            # Create empty page template
            self._draw_empty_page_template(draw, total_panels)
        
        # Section 2: Character reference strip
        y_offset = self.page_height
        if self.character_refs:
            draw.rectangle([0, y_offset, self.page_width, y_offset + 2], fill='black')
            draw.text((10, y_offset + 5), "CHARACTER REFERENCES", fill='black')
            self._add_reference_strip(
                sheet, 
                self.character_refs, 
                y_offset + 30,
                "Characters"
            )
        
        # Section 3: Location reference strip  
        y_offset += self.reference_strip_height
        if self.location_refs:
            draw.rectangle([0, y_offset, self.page_width, y_offset + 2], fill='black')
            draw.text((10, y_offset + 5), "LOCATION REFERENCES", fill='black')
            self._add_reference_strip(
                sheet,
                self.location_refs,
                y_offset + 30,
                "Locations"
            )
        
        # Section 4: Props reference strip
        y_offset += self.reference_strip_height
        if self.prop_refs:
            draw.rectangle([0, y_offset, self.page_width, y_offset + 2], fill='black')
            draw.text((10, y_offset + 5), "PROP REFERENCES", fill='black')
            self._add_reference_strip(
                sheet,
                self.prop_refs,
                y_offset + 30,
                "Props"
            )
        
        # Convert to bytes
        buffer = io.BytesIO()
        sheet.save(buffer, format='PNG', optimize=True)
        return buffer.getvalue()
    
    def _add_reference_strip(
        self,
        sheet: Image.Image,
        references: List[ReferenceElement],
        y_position: int,
        strip_title: str
    ):
        """Add a reference strip to the sheet.
        
        Args:
            sheet: Sheet to add strip to
            references: Reference elements to include
            y_position: Y position for the strip
            strip_title: Title for the strip
        """
        if not references:
            return
            
        # Calculate spacing
        ref_height = min(350, self.reference_strip_height - 50)
        spacing = 10
        max_width_per_ref = (self.page_width - (spacing * (len(references) + 1))) // len(references)
        
        x_offset = spacing
        for ref in references:
            # Resize reference to fit
            ref_image = ref.image.copy()
            
            # Calculate scaling to fit in allocated space
            scale = min(max_width_per_ref / ref_image.width, ref_height / ref_image.height)
            new_width = int(ref_image.width * scale)
            new_height = int(ref_image.height * scale)
            
            ref_image = ref_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Paste reference
            sheet.paste(ref_image, (x_offset, y_position))
            
            # Add label
            draw = ImageDraw.Draw(sheet)
            draw.text(
                (x_offset + 5, y_position + new_height - 25),
                ref.name,
                fill='white',
                stroke_width=2,
                stroke_fill='black'
            )
            
            x_offset += new_width + spacing
    
    def _draw_empty_page_template(self, draw: ImageDraw.Draw, total_panels: int):
        """Draw an empty page template with panel borders.
        
        Args:
            draw: PIL Draw object
            total_panels: Number of panels to layout
        """
        if total_panels <= 0:
            return
        
        # Use the same calculation method for consistency
        for i in range(total_panels):
            x1, y1, x2, y2 = self.calculate_panel_position(i, total_panels)
            
            # Draw panel border
            draw.rectangle([x1, y1, x2, y2], outline='lightgray', width=2)
            draw.text((x1 + 5, y1 + 5), f"Panel {i+1}", fill='lightgray')
    
    def add_character_reference(self, name: str, image: Image.Image, metadata: Dict = None):
        """Add a character reference.
        
        Args:
            name: Character name
            image: Reference image
            metadata: Additional metadata
        """
        self.character_refs.append(
            ReferenceElement(name, image, 'character', metadata)
        )
    
    def add_location_reference(self, name: str, image: Image.Image, metadata: Dict = None):
        """Add a location reference.
        
        Args:
            name: Location name
            image: Reference image
            metadata: Additional metadata
        """
        self.location_refs.append(
            ReferenceElement(name, image, 'location', metadata)
        )
    
    def add_prop_reference(self, name: str, image: Image.Image, metadata: Dict = None):
        """Add a prop reference.
        
        Args:
            name: Prop name
            image: Reference image
            metadata: Additional metadata
        """
        self.prop_refs.append(
            ReferenceElement(name, image, 'prop', metadata)
        )
    
    def update_page_state(self, page_canvas: Image.Image):
        """Update the current page state.
        
        Args:
            page_canvas: Current state of the page
        """
        self.current_page_canvas = page_canvas.copy()
    
    def extract_references_from_panel(self, panel_image: Image.Image, panel_data: Dict):
        """Extract reusable references from a generated panel.
        
        Args:
            panel_image: Generated panel image
            panel_data: Panel metadata (characters, locations, props)
        """
        # In a real implementation, we might use ML to extract character crops
        # For now, we'll store the whole panel as potential reference
        
        # Extract characters mentioned in this panel
        if 'characters' in panel_data and panel_data['characters']:
            for char in panel_data['characters']:
                # Check if we already have this character
                if not any(ref.name == char for ref in self.character_refs):
                    # For now, use the whole panel as reference
                    # In production, we'd crop the character
                    self.add_character_reference(char, panel_image, {
                        'source_panel': panel_data.get('panel_number', 0)
                    })
        
        # Similar for locations and props
        if 'location' in panel_data and panel_data['location']:
            location = panel_data['location']
            if not any(ref.name == location for ref in self.location_refs):
                self.add_location_reference(location, panel_image, {
                    'source_panel': panel_data.get('panel_number', 0)
                })
    
    def calculate_panel_position(self, panel_index: int, total_panels: int) -> Tuple[int, int, int, int]:
        """Calculate the position for a panel on the page.
        
        Args:
            panel_index: Index of the panel (0-based)
            total_panels: Total number of panels
            
        Returns:
            (x1, y1, x2, y2) coordinates
        """
        # Use the shared layout configuration
        return calculate_panel_position(
            panel_index,
            total_panels,
            self.page_width,
            self.page_height
        )
    
    def reset(self):
        """Reset the reference builder for a new page."""
        self.current_page_canvas = None
        self.completed_panels = []
        # Keep character/location/prop refs as they span pages
    
    def clear_all_references(self):
        """Clear all references for a new comic."""
        self.character_refs = []
        self.location_refs = []
        self.prop_refs = []
        self.reset()