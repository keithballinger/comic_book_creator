# Single-Pass Page Generation Architecture

## Overview

Instead of generating individual panels and compositing them, we'll generate entire comic pages in a single API call to Gemini. This approach ensures perfect visual consistency, proper panel flow, and eliminates layout/composition issues.

## Key Changes from Current Architecture

### Before (Multi-Pass Panel Generation)
```
Script → Parse → For Each Panel → Generate Panel → Resize/Crop → Compose Page
```

### After (Single-Pass Page Generation)
```
Script → Parse → For Each Page → Generate Complete Page
```

## Detailed Implementation Plan

### 1. New Page Generator (`src/generator/page_generator.py`)

```python
class PageGenerator:
    """Generates complete comic pages in a single pass."""
    
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client
        self.page_width = 2400
        self.page_height = 3600
        
    async def generate_page(
        self,
        page: Page,
        previous_pages: List[Image.Image] = None,
        style_context: Dict = None
    ) -> bytes:
        """Generate a complete comic page with all panels."""
        
        # Build comprehensive page prompt
        prompt = self._build_page_prompt(page)
        
        # Prepare previous pages as context
        context_images = previous_pages or []
        
        # Call Gemini with prompt and context
        response = await self.client.generate_page_image(
            prompt=prompt,
            context_images=context_images,
            style_config=style_context
        )
        
        return response
    
    def _build_page_prompt(self, page: Page) -> str:
        """Build detailed prompt for entire page generation."""
        
        num_panels = len(page.panels)
        
        prompt = f"""
        Generate a complete comic book page with EXACTLY {num_panels} panels.
        
        PAGE SPECIFICATIONS:
        - Dimensions: EXACTLY 2400x3600 pixels
        - Layout: {self._get_layout_description(num_panels)}
        - Margins: 15px around the page
        - Panel gutters: 5px between panels
        - All panels must be the same size
        - Black panel borders (2px)
        
        PANEL CONTENT:
        {self._build_panels_description(page.panels)}
        
        CRITICAL REQUIREMENTS:
        1. Generate the ENTIRE page as a single image
        2. All {num_panels} panels must be clearly separated with borders
        3. Each panel must contain its specified content
        4. All text (captions, dialogue, sound effects) must be INSIDE panel boundaries
        5. Maintain consistent art style across all panels
        6. Maintain consistent character appearances across all panels
        7. The page should read naturally from top-left to bottom-right
        
        STYLE REQUIREMENTS:
        - Comic book art style
        - Clear, readable text in appropriate bubbles/boxes
        - Professional layout with proper panel flow
        - Consistent color palette throughout the page
        
        OUTPUT: One complete comic page (2400x3600px) with all {num_panels} panels
        """
        
        return prompt
    
    def _get_layout_description(self, num_panels: int) -> str:
        """Get layout description for number of panels."""
        layouts = {
            1: "Single full-page panel",
            2: "Two panels stacked vertically (1x2 grid)",
            3: "Three panels stacked vertically (1x3 grid)", 
            4: "Four panels in 2x2 grid",
            5: "Five panels: 2 on top row, 3 on bottom row",
            6: "Six panels in 2x3 grid (2 columns, 3 rows)",
            7: "Seven panels: 3-3-1 layout",
            8: "Eight panels in 2x4 grid",
            9: "Nine panels in 3x3 grid"
        }
        return layouts.get(num_panels, f"{num_panels} panels in grid layout")
    
    def _build_panels_description(self, panels: List[Panel]) -> str:
        """Build detailed description of all panels."""
        descriptions = []
        
        for i, panel in enumerate(panels, 1):
            panel_desc = f"""
        PANEL {i}:
        {panel.raw_text}
        
        Visual requirements for Panel {i}:
        - Clear separation from other panels
        - All text elements inside this panel's boundaries
        - Consistent character appearances from previous panels
            """
            descriptions.append(panel_desc)
        
        return "\n".join(descriptions)
```

### 2. Updated Gemini Client (`src/api/gemini_client.py`)

```python
class GeminiClient:
    """Updated client for single-pass page generation."""
    
    async def generate_page_image(
        self,
        prompt: str,
        context_images: List[Image.Image] = None,
        style_config: Dict = None
    ) -> bytes:
        """Generate a complete comic page."""
        
        # Convert PIL images to format expected by Gemini
        contents = []
        
        # Add previous pages as context
        if context_images:
            for img in context_images:
                contents.append(img)  # PIL Image objects
        
        # Add the text prompt
        contents.append(prompt)
        
        # Add style instructions if provided
        if style_config:
            style_prompt = self._build_style_prompt(style_config)
            contents.append(style_prompt)
        
        # Call Gemini API
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=contents
        )
        
        # Extract generated image
        image_parts = [
            part.inline_data.data
            for part in response.candidates[0].content.parts
            if part.inline_data
        ]
        
        if image_parts:
            return image_parts[0]  # Return bytes
        
        raise Exception("No image generated")
```

### 3. Simplified Pipeline (`src/processor/pipeline.py`)

```python
class ProcessingPipeline:
    """Simplified pipeline for single-pass generation."""
    
    async def process_script(
        self,
        script_path: str,
        options: ProcessingOptions
    ) -> ProcessingResult:
        """Process script with single-pass page generation."""
        
        # Parse script
        script = self.parser.parse_script(script_path)
        
        # Validate
        validation = self.validator.validate_script(script)
        if not validation.is_valid:
            return ProcessingResult(success=False, ...)
        
        # Initialize page generator
        page_generator = PageGenerator(self.gemini_client)
        
        # Generate pages
        generated_pages = []
        previous_page_images = []
        
        for page in script.pages:
            # Generate complete page
            page_image_bytes = await page_generator.generate_page(
                page=page,
                previous_pages=previous_page_images[-2:],  # Last 2 pages for context
                style_context=self.style_config
            )
            
            # Convert to PIL Image
            page_image = Image.open(BytesIO(page_image_bytes))
            
            # Store for context
            previous_page_images.append(page_image)
            
            # Create GeneratedPage object
            generated_page = GeneratedPage(
                page=page,
                image_data=page_image_bytes,
                generation_time=...
            )
            generated_pages.append(generated_page)
        
        return ProcessingResult(
            success=True,
            generated_pages=generated_pages,
            ...
        )
```

### 4. Removed/Simplified Components

**Components to Remove:**
- `panel_generator.py` - No longer needed
- `reference_builder.py` - No longer needed
- `consistency.py` - Simplified or removed
- `compositor.py` - No longer needed
- `layout_config.py` - Simplified to just constants

**Components to Simplify:**
- Models: Remove `GeneratedPanel`, keep only `GeneratedPage`
- Pipeline: Remove panel-level processing

### 5. Updated Data Models

```python
@dataclass
class GeneratedPage:
    """A generated comic page."""
    page: Page  # Source page from script
    image_data: bytes  # Complete page as PNG
    generation_time: float
    metadata: Dict[str, Any]

# Remove GeneratedPanel entirely
```

### 6. Advantages of Single-Pass Generation

1. **Perfect Consistency**: All panels generated together ensures consistent style
2. **Better Flow**: Gemini understands panel relationships and can create better visual flow
3. **Simpler Architecture**: Eliminates composition, reference building, and panel management
4. **Faster Generation**: One API call per page instead of 4-9 calls
5. **No Layout Issues**: Gemini handles all layout, spacing, and borders
6. **Natural Text Placement**: Gemini can optimize text placement across the entire page

### 7. Migration Path

#### Phase 1: Create New Components
1. Create `page_generator.py` with single-pass logic
2. Update `gemini_client.py` to support page generation
3. Add page-level prompt building

#### Phase 2: Update Pipeline
1. Modify pipeline to use page generator
2. Remove panel-level processing
3. Update progress tracking

#### Phase 3: Clean Up
1. Remove unused panel components
2. Simplify data models
3. Update tests

### 8. Example Prompt for 4-Panel Page

```
Generate a complete comic book page with EXACTLY 4 panels.

PAGE SPECIFICATIONS:
- Dimensions: EXACTLY 2400x3600 pixels
- Layout: Four panels in 2x2 grid
- Margins: 15px around the page
- Panel gutters: 5px between panels
- All panels must be the same size
- Black panel borders (2px)

PANEL CONTENT:

PANEL 1:
Setting: A slightly messy kid's bedroom. KEITH (a boy of about 10, with curly hair and glasses) slumped over his desk, looking bored. Blank paper and pencils scattered. A sad stick figure drawing on the paper.
Caption: Keith had a million stories in his head... but getting them onto paper was impossible.
Keith (Thought Bubble): Ugh. My hands just can't draw what's in my brain!

PANEL 2:
Keith discovers a tablet with "COMIC BOOK CREATOR" on screen. His eyes widen with curiosity.
Caption: Then, he discovered a new tool.
Keith: Whoa... what's this?
SFX: Bloop!

PANEL 3:
Keith frantically drawing on the tablet. Motion lines show rapid movement. A vibrant comic panel appears on screen.
Caption: Suddenly, the stories started to flow...
SFX: TAP! TAP! SWIPE! DRAG! FWOOSH!

PANEL 4:
Keith proudly showing tablet to MOM. Screen shows finished comic "CAPTAIN KEITH". Mom looks amazed. Keith beaming.
Mom: Keith, this is amazing! You made a whole comic book!
Keith: It's like my brain has superpowers now!

CRITICAL REQUIREMENTS:
1. Generate the ENTIRE page as a single image
2. All 4 panels must be clearly separated with borders
3. Each panel must contain its specified content
4. All text must be INSIDE panel boundaries
5. Maintain consistent Keith appearance across all panels
6. The page should read naturally from top-left to bottom-right

OUTPUT: One complete comic page (2400x3600px) with all 4 panels
```

### 9. Debug Output Changes

For debugging, we would save:
- The complete prompt sent to Gemini
- Previous pages used as context
- The generated page
- Generation metadata (time, model response, etc.)

No need for panel-level debug output or reference sheets.

### 10. CLI Changes

The CLI remains mostly the same, but internal behavior changes:
- Progress bar shows pages instead of panels
- Generation is faster (one call per page)
- No --parallel option needed (already fast)

## Summary

This single-pass architecture dramatically simplifies the system while likely improving output quality. By letting Gemini handle the entire page composition, we eliminate complex layout logic, ensure perfect consistency, and reduce API calls by 75% or more.