# Comic Book Creator - System Architecture

## Overview

The Comic Book Creator is a Python-based application that transforms text-based comic scripts into fully illustrated comic books using Google's Gemini AI for image generation. The system processes structured scripts, generates panels with consistent art styles and characters, and assembles them into complete comic pages.

## Core Architecture Principles

1. **AI-Native Generation**: All visual content including artwork, text bubbles, captions, and sound effects are generated directly by Gemini AI
2. **Progressive Context Building**: Each panel builds upon previous panels using reference sheets for consistency
3. **Strict Layout Control**: Uniform panel sizing with minimal whitespace (98% page utilization)
4. **Single-Source Text**: Text is embedded in generated images, not overlaid post-generation

## System Components

### 1. Script Parser (`src/parser/`)

#### ScriptParser (`script_parser.py`)
- **Purpose**: Converts plain text scripts into structured data models
- **Input Format**: Text files with specific markers (PAGE, Panel, Caption:, etc.)
- **Process**:
  1. Reads script file line by line
  2. Identifies structural markers (PAGE, Panel numbers)
  3. Extracts dialogue (character names with colons)
  4. Captures captions (Caption: prefix)
  5. Identifies sound effects (SFX: prefix)
  6. Preserves raw text for each panel
- **Output**: `ComicScript` object containing hierarchical Page → Panel structure

#### ScriptValidator (`validator.py`)
- Validates script structure integrity
- Ensures panels have content
- Checks for required elements
- Returns `ValidationResult` with errors/warnings

### 2. Data Models (`src/models/`)

#### Core Script Models (`script.py`)
```python
ComicScript
├── title: str
├── pages: List[Page]
└── metadata: Dict

Page
├── number: int
├── panels: List[Panel]
└── layout: Optional[str]

Panel
├── number: int
├── description: str
├── raw_text: str  # Original script text
├── characters: List[str]
├── dialogue: List[Dialogue]
├── captions: List[Caption]
└── sound_effects: List[SoundEffect]
```

#### Generation Models (`generation.py`)
```python
GeneratedPanel
├── panel: Panel  # Source panel
├── image_data: bytes  # PNG image data
├── generation_time: float
└── metadata: Dict  # Prompts, settings, etc.

GeneratedPage
├── page: Page
├── panels: List[GeneratedPanel]
└── generation_time: float

ProcessingOptions
├── page_range: Optional[Tuple[int, int]]
├── style_preset: Optional[str]
├── quality: str
├── parallel_generation: bool
└── export_formats: List[str]
```

### 3. AI Integration (`src/api/`)

#### GeminiClient (`gemini_client.py`)
- **Purpose**: Interface with Google's Gemini AI API
- **Key Methods**:
  - `generate_panel_image()`: Generates a single panel image
  - `enhance_panel_description()`: Enriches panel descriptions
  - `generate_character_reference()`: Creates character consistency references

- **Image Generation Process**:
  1. Receives panel description and reference images
  2. Builds multimodal prompt with:
     - Base64-encoded reference images
     - Strict dimensional requirements
     - Style consistency instructions
     - Text placement rules
  3. Sends to Gemini 2.5 Flash Image Preview model
  4. Returns generated image as bytes

- **Prompt Structure**:
  ```
  ⚠️ CRITICAL: Generate EXACTLY ONE SINGLE PANEL
  Panel dimensions: {width}x{height} pixels
  
  IMPORTANT TEXT PLACEMENT RULES:
  - ALL text elements MUST be INSIDE panel boundaries
  - Captions: Yellow/white boxes at top/bottom INSIDE panel
  - Speech bubbles: White ovals with tails, INSIDE panel
  - Thought bubbles: Cloud-shaped, INSIDE panel
  - Sound effects: Stylized text integrated into artwork
  
  [Panel content description]
  
  OUTPUT: ONE high-quality comic book panel with exact dimensions
  ```

#### RateLimiter (`rate_limiter.py`)
- Implements exponential backoff for API calls
- Handles rate limiting (30 calls/minute default)
- Retries on transient failures

### 4. Panel Generation (`src/generator/`)

#### PanelGenerator (`panel_generator.py`)
- **Core Responsibility**: Orchestrates panel image generation with consistency
- **Key Features**:
  - Progressive reference sheet building
  - Exact dimension enforcement
  - Debug output capability

- **Generation Flow**:
  1. **Initialize Reference Builder**: Creates reference sheets for consistency
  2. **For Each Panel**:
     a. Calculate exact panel position (1182x1782 pixels for 4-panel layout)
     b. Build comprehensive reference sheet showing:
        - Page with completed panels
        - Character reference strip
        - Location references
        - Red rectangle marking target panel area
     c. Generate strict prompt with exact dimensions
     d. Call Gemini API with reference sheet
     e. Resize/crop result to exact dimensions (maintaining aspect ratio)
     f. Add panel to page canvas
     g. Update reference builder with new panel
  3. **Return**: List of `GeneratedPanel` objects

#### ConsistencyManager (`consistency.py`)
- Maintains character/style consistency across panels
- Stores character references
- Builds prompts with consistency instructions
- Tracks style configurations

#### ReferenceSheetBuilder (`reference_builder.py`)
- **Purpose**: Creates visual context for each panel generation
- **Reference Sheet Components**:
  1. **Page-in-progress**: Shows already completed panels
  2. **Character strip**: Reference images of characters
  3. **Location strip**: Background/setting references
  4. **Target indicator**: Red rectangle showing where next panel goes
- **Dimensions**: Full reference sheet is 2400x4800px (page + 3 reference strips)

### 5. Layout System (`src/output/`)

#### Layout Configuration (`layout_config.py`)
- **Page Dimensions**: 2400x3600 pixels
- **Margins**: 15px (minimal, 98% page utilization)
- **Panel Gutters**: 5px between panels
- **Panel Layouts**:
  - 1 panel: 1x1 grid
  - 2 panels: 1x2 grid
  - 4 panels: 2x2 grid (each panel 1182x1782px)
  - 6 panels: 2x3 grid
  - 9 panels: 3x3 grid

- **Key Function**: `calculate_panel_position(panel_index, total_panels)`
  - Returns exact (x1, y1, x2, y2) coordinates
  - Ensures all panels are EXACTLY the same size
  - No special layouts - strict uniform grid

#### PageCompositor (`compositor.py`)
- **Purpose**: Assembles individual panels into complete pages
- **Process**:
  1. Creates blank page canvas (2400x3600px)
  2. Calculates panel positions using layout_config
  3. Places each panel at exact coordinates
  4. Adds panel borders (2px black)
  5. Optionally adds page numbers
- **Output**: Complete page as PIL Image

### 6. Processing Pipeline (`src/processor/pipeline.py`)

The central orchestrator that coordinates the entire generation process:

```python
ProcessingPipeline
├── parse_script()
├── validate_script()
├── initialize_generator()
├── extract_characters()
├── for each page:
│   ├── generate_page_with_references()
│   └── compose_page()
└── save_results()
```

**Detailed Flow**:
1. **Script Processing**:
   - Parse script file → `ComicScript` object
   - Validate structure → `ValidationResult`
   - Extract unique character names

2. **Generator Initialization**:
   - Create GeminiClient with API key
   - Initialize ConsistencyManager
   - Set up RateLimiter
   - Configure debug output directory

3. **Page Generation**:
   - For each page in script:
     - Call `generate_page_with_references()`
     - Progressive panel generation with context
     - Each panel sees all previous panels

4. **Output Generation**:
   - Save individual panel images
   - Compose complete pages
   - Export in requested formats (PNG, CBZ, PDF)

### 7. CLI Interface (`src/cli.py`)

Command-line interface using Click framework:

```bash
comic_creator generate <script.txt> [options]
  --output DIR        Output directory
  --style STYLE       Art style preset
  --quality QUALITY   Output quality (draft/standard/high)
  --pages RANGE       Page range (e.g., "1-3")
  --parallel          Enable parallel generation
  --format FORMAT     Export format (png/cbz/pdf)
```

### 8. Configuration (`src/config/`)

#### ConfigLoader (`config_loader.py`)
- Loads configuration from:
  1. Default settings
  2. config.yaml file
  3. Environment variables
  4. Command-line overrides

- **Key Settings**:
  - API credentials
  - Model selection
  - Output settings
  - Rate limits
  - Debug options

## Data Flow

```
1. Script Input (.txt)
       ↓
2. Parser → ComicScript
       ↓
3. Validator → ValidationResult
       ↓
4. Pipeline Initialization
       ↓
5. For Each Page:
   a. Reference Builder → Reference Sheet
   b. Panel Generator → Gemini API → Panel Image
   c. Dimension Enforcement → Exact Size Panel
   d. Canvas Assembly → Page in Progress
       ↓
6. Page Compositor → Complete Page
       ↓
7. Export → PNG/CBZ/PDF
```

## Key Design Decisions

### 1. Single-Source Text Generation
- **Decision**: All text (captions, dialogue, SFX) is generated by Gemini as part of the artwork
- **Rationale**: Ensures visual consistency and proper integration with art
- **Implementation**: Removed TextRenderer class entirely; prompts include strict text placement rules

### 2. Progressive Reference Sheets
- **Decision**: Each panel sees the page-in-progress plus reference strips
- **Rationale**: Maintains consistency across panels
- **Implementation**: ReferenceSheetBuilder creates comprehensive visual context

### 3. Strict Dimension Enforcement
- **Decision**: All panels are exactly the same size (1182x1782px for 4-panel)
- **Rationale**: Professional uniform layout
- **Implementation**: Resize with aspect ratio preservation, then crop/pad to exact size

### 4. Minimal Whitespace
- **Decision**: 15px margins, 5px gutters (98% page utilization)
- **Rationale**: Maximize visual impact
- **Implementation**: Centralized layout_config module

### 5. Debug Output
- **Decision**: Optional saving of all intermediate artifacts
- **Rationale**: Essential for troubleshooting generation issues
- **Implementation**: Saves reference sheets, prompts, and progressive page states

## Error Handling

1. **API Failures**: Exponential backoff with retry
2. **Invalid Scripts**: Validation with clear error messages
3. **Generation Failures**: Placeholder panels with error metadata
4. **File I/O**: Graceful degradation with logging

## Performance Characteristics

- **Generation Time**: ~15 seconds per panel (API-limited)
- **Memory Usage**: ~500MB for typical 10-page comic
- **API Calls**: 1 per panel + character references
- **Rate Limits**: 30 panels/minute (configurable)

## Future Considerations

1. **Caching**: Could cache generated panels (currently disabled)
2. **Parallel Generation**: Supported but may affect consistency
3. **Style Transfer**: Style configuration system is extensible
4. **Multiple Models**: Architecture supports different AI providers

## Directory Structure

```
comic_book_creator/
├── src/
│   ├── api/           # AI service integration
│   ├── config/        # Configuration management
│   ├── generator/     # Panel generation logic
│   ├── models/        # Data models
│   ├── output/        # Layout and composition
│   ├── parser/        # Script parsing
│   ├── processor/     # Main pipeline
│   └── cli.py         # Command-line interface
├── examples/          # Sample scripts
├── output/           # Generated comics
└── tests/            # Test suite
```

## Testing Strategy

- Unit tests for each component
- Integration tests for full pipeline
- Mock Gemini API for deterministic testing
- Visual regression tests for layout consistency