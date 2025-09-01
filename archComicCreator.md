# Comic Book Creator - Technical Architecture Design

## Executive Summary

Comic Book Creator is a Python-based CLI application that transforms industry-standard comic book scripts into fully illustrated comics using Google's Gemini Flash 2.5 API. The system leverages both text generation (Gemini Flash 2.5) and image generation (Gemini Flash 2.5 Image Preview) capabilities to create consistent, high-quality comic panels with integrated text elements.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Script Input   │────▶│  Comic Creator   │────▶│  Output Files   │
│   (.txt/.fdx)   │     │    CLI Tool      │     │  (PNG/PDF/CBZ)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Gemini API Suite  │
                    ├─────────────────────┤
                    │ • Flash 2.5 (Text)  │
                    │ • Flash 2.5 Image   │
                    └─────────────────────┘
```

### Component Architecture

```
comic-book-creator/
├── src/
│   ├── __init__.py
│   ├── cli.py                  # CLI interface & commands
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── script_parser.py    # Parse comic scripts
│   │   └── validators.py       # Script validation
│   ├── generator/
│   │   ├── __init__.py
│   │   ├── panel_generator.py  # Panel image generation
│   │   ├── text_renderer.py    # Text/dialogue handling
│   │   └── consistency.py      # Style consistency manager
│   ├── api/
│   │   ├── __init__.py
│   │   ├── gemini_client.py    # Gemini API wrapper
│   │   └── rate_limiter.py     # API rate limiting
│   ├── processor/
│   │   ├── __init__.py
│   │   ├── pipeline.py         # Processing pipeline
│   │   ├── cache_manager.py    # Caching system
│   │   └── batch_processor.py  # Batch operations
│   ├── output/
│   │   ├── __init__.py
│   │   ├── compositor.py       # Page composition
│   │   ├── exporters.py        # Export formats
│   │   └── file_manager.py     # File I/O operations
│   └── ui/
│       ├── __init__.py
│       ├── progress.py         # Progress indicators
│       └── status_display.py   # Dynamic status UI
├── config/
│   ├── default.yaml
│   └── styles.yaml
├── tests/
├── requirements.txt
├── .env.example
├── Makefile
└── README.md
```

## Core Components

### 1. Script Parser Module

**Purpose**: Parse industry-standard comic book scripts into structured data

**Key Classes**:
```python
class ScriptParser:
    def parse_script(self, script_path: str) -> ComicScript
    def validate_format(self, script: str) -> ValidationResult
    
class ComicScript:
    pages: List[Page]
    metadata: Dict[str, Any]
    
class Page:
    number: int
    panels: List[Panel]
    
class Panel:
    number: int
    description: str
    dialogue: List[Dialogue]
    captions: List[Caption]
    sound_effects: List[SoundEffect]
```

**Script Format Support**:
- Standard comic script format (PAGE/PANEL structure)
- Final Draft XML (.fdx)
- Fountain format
- Custom JSON format

### 2. Gemini API Client

**Purpose**: Interface with Gemini Flash 2.5 APIs following exact patterns from examples

**Implementation** (based on provided examples):
```python
import os
from google.genai import GoogleGenAI
from dotenv import load_dotenv
import asyncio
from typing import AsyncGenerator, Dict, Any

class GeminiClient:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.ai = GoogleGenAI(api_key=self.api_key)
        self.text_model = 'gemini-2.5-flash'
        self.image_model = 'gemini-2.5-flash-image-preview'
        
    async def generate_panel_image(
        self, 
        prompt: str, 
        reference_images: List[bytes] = None,
        style_config: Dict[str, Any] = None
    ) -> bytes:
        """Generate comic panel image using Gemini Flash 2.5 Image"""
        config = {
            'responseModalities': ['IMAGE'],
            'thinkingConfig': {'thinkingBudget': -1}
        }
        
        contents = self._build_image_prompt(prompt, reference_images, style_config)
        
        response = await self.ai.models.generateContentStream({
            'model': self.image_model,
            'config': config,
            'contents': contents
        })
        
        # Stream and collect image data
        image_data = b''
        async for chunk in response:
            if chunk.image:
                image_data += chunk.image
        
        return image_data
    
    async def enhance_panel_description(
        self, 
        panel: Panel,
        character_refs: Dict[str, str]
    ) -> str:
        """Use text model to enhance panel descriptions"""
        config = {
            'thinkingConfig': {'thinkingBudget': -1}
        }
        
        prompt = self._build_enhancement_prompt(panel, character_refs)
        
        response = await self.ai.models.generateContentStream({
            'model': self.text_model,
            'config': config,
            'contents': [{'role': 'user', 'parts': [{'text': prompt}]}]
        })
        
        enhanced_description = ''
        async for chunk in response:
            enhanced_description += chunk.text
            
        return enhanced_description
```

### 3. Panel Generator

**Purpose**: Orchestrate panel image generation with consistency management

**Key Features**:
```python
class PanelGenerator:
    def __init__(self, gemini_client: GeminiClient):
        self.client = gemini_client
        self.consistency_manager = ConsistencyManager()
        self.cache = CacheManager()
        
    async def generate_panel(
        self,
        panel: Panel,
        page_context: Page,
        previous_panels: List[GeneratedPanel] = None
    ) -> GeneratedPanel:
        """Generate a single panel with consistency"""
        
        # Check cache first
        cache_key = self._generate_cache_key(panel)
        if cached := self.cache.get(cache_key):
            return cached
            
        # Enhance description with context
        enhanced_desc = await self.client.enhance_panel_description(
            panel, 
            self.consistency_manager.character_refs
        )
        
        # Build prompt with style consistency
        prompt = self.consistency_manager.build_consistent_prompt(
            enhanced_desc,
            previous_panels
        )
        
        # Get reference images for consistency
        ref_images = self.consistency_manager.get_reference_images(
            previous_panels,
            panel.characters
        )
        
        # Generate image
        image_data = await self.client.generate_panel_image(
            prompt,
            ref_images,
            self.consistency_manager.style_config
        )
        
        # Add text overlays
        final_image = await self.add_text_elements(
            image_data,
            panel.dialogue,
            panel.captions,
            panel.sound_effects
        )
        
        generated_panel = GeneratedPanel(
            panel=panel,
            image_data=final_image,
            metadata=self._extract_metadata(panel)
        )
        
        # Update consistency manager
        self.consistency_manager.register_panel(generated_panel)
        
        # Cache result
        self.cache.set(cache_key, generated_panel)
        
        return generated_panel
```

### 4. Consistency Manager

**Purpose**: Maintain visual and stylistic consistency across panels

**Implementation**:
```python
class ConsistencyManager:
    def __init__(self):
        self.character_refs: Dict[str, CharacterReference] = {}
        self.style_config: StyleConfig = None
        self.panel_history: List[GeneratedPanel] = []
        self.style_embeddings: Dict[str, np.ndarray] = {}
        
    def build_consistent_prompt(
        self,
        base_description: str,
        previous_panels: List[GeneratedPanel]
    ) -> str:
        """Build prompt with consistency instructions"""
        
        prompt_parts = [
            f"Create a comic book panel in {self.style_config.art_style} style.",
            f"Color palette: {self.style_config.color_palette}",
            f"Line weight: {self.style_config.line_weight}",
            "",
            "Panel description:",
            base_description,
            ""
        ]
        
        # Add character consistency instructions
        for char_name in self._extract_characters(base_description):
            if char_ref := self.character_refs.get(char_name):
                prompt_parts.append(
                    f"{char_name}: {char_ref.appearance_description}"
                )
        
        # Add style consistency from previous panels
        if previous_panels:
            prompt_parts.append(
                "\nMaintain consistent art style with previous panels."
            )
            
        return "\n".join(prompt_parts)
    
    def get_reference_images(
        self,
        previous_panels: List[GeneratedPanel],
        characters: List[str]
    ) -> List[bytes]:
        """Get reference images for consistency"""
        
        ref_images = []
        
        # Add character reference sheets
        for char in characters:
            if char_ref := self.character_refs.get(char):
                if char_ref.reference_image:
                    ref_images.append(char_ref.reference_image)
        
        # Add recent panels with same characters
        for panel in previous_panels[-3:]:  # Last 3 panels
            if any(c in panel.characters for c in characters):
                ref_images.append(panel.image_data)
                
        return ref_images
```

### 5. Text Renderer

**Purpose**: Handle text overlay and speech bubble generation

**Implementation**:
```python
class TextRenderer:
    def __init__(self):
        self.bubble_styles = self._load_bubble_styles()
        self.font_manager = FontManager()
        
    async def render_text_elements(
        self,
        base_image: bytes,
        dialogue: List[Dialogue],
        captions: List[Caption],
        sound_effects: List[SoundEffect]
    ) -> bytes:
        """Add text elements to panel image"""
        
        # Convert to PIL Image
        img = Image.open(io.BytesIO(base_image))
        draw = ImageDraw.Draw(img)
        
        # Render dialogue bubbles
        for d in dialogue:
            bubble_pos = self._calculate_bubble_position(img, d)
            self._draw_speech_bubble(draw, bubble_pos, d.text, d.character)
            
        # Render captions
        for c in captions:
            self._draw_caption_box(draw, c.text, c.position)
            
        # Render sound effects
        for se in sound_effects:
            self._draw_sound_effect(draw, se.text, se.position, se.style)
            
        # Convert back to bytes
        output = io.BytesIO()
        img.save(output, format='PNG')
        return output.getvalue()
```

### 6. Processing Pipeline

**Purpose**: Orchestrate the entire comic generation workflow

**Implementation**:
```python
class ProcessingPipeline:
    def __init__(self, config: Config):
        self.config = config
        self.parser = ScriptParser()
        self.generator = PanelGenerator(GeminiClient())
        self.compositor = PageCompositor()
        self.progress_ui = ProgressUI()
        
    async def process_script(
        self,
        script_path: str,
        output_dir: str,
        options: ProcessingOptions
    ) -> ProcessingResult:
        """Main processing pipeline"""
        
        # Parse script
        with self.progress_ui.task("Parsing script"):
            comic_script = self.parser.parse_script(script_path)
            
        # Initialize consistency manager with style
        self.generator.consistency_manager.load_style(
            self.config.style_config
        )
        
        # Process pages
        generated_pages = []
        total_panels = sum(len(p.panels) for p in comic_script.pages)
        
        with self.progress_ui.progress_bar(total_panels) as pbar:
            for page in comic_script.pages:
                if not self._should_process_page(page, options):
                    continue
                    
                # Generate panels for page
                generated_panels = []
                for panel in page.panels:
                    pbar.set_description(f"Page {page.number}, Panel {panel.number}")
                    
                    generated_panel = await self.generator.generate_panel(
                        panel,
                        page,
                        generated_panels
                    )
                    
                    generated_panels.append(generated_panel)
                    pbar.update(1)
                    
                    # Save intermediate results
                    await self._save_panel(generated_panel, output_dir)
                
                # Compose page
                page_image = self.compositor.compose_page(
                    generated_panels,
                    page.layout
                )
                
                generated_pages.append(GeneratedPage(
                    page=page,
                    panels=generated_panels,
                    composed_image=page_image
                ))
        
        # Export final outputs
        with self.progress_ui.task("Exporting files"):
            export_results = await self._export_outputs(
                generated_pages,
                output_dir,
                options.export_formats
            )
            
        return ProcessingResult(
            pages=generated_pages,
            export_paths=export_results
        )
```

### 7. Dynamic Status UI

**Purpose**: Provide real-time feedback during long-running operations

**Implementation**:
```python
import rich
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.table import Table
from rich.layout import Layout

class ProgressUI:
    def __init__(self):
        self.console = Console()
        self.live = None
        
    def start_generation(self, total_pages: int, total_panels: int):
        """Initialize dynamic status display"""
        
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="progress", size=10),
            Layout(name="status", size=5),
            Layout(name="log")
        )
        
        # Header
        header = Table.grid()
        header.add_column(justify="center")
        header.add_row("[bold blue]Comic Book Creator[/bold blue]")
        header.add_row(f"Generating {total_panels} panels across {total_pages} pages")
        layout["header"].update(header)
        
        # Progress bars
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})")
        )
        
        self.page_task = self.progress.add_task(
            "[cyan]Pages", total=total_pages
        )
        self.panel_task = self.progress.add_task(
            "[green]Panels", total=total_panels
        )
        
        layout["progress"].update(self.progress)
        
        # Status table
        self.status_table = Table()
        self.status_table.add_column("Metric", style="cyan")
        self.status_table.add_column("Value", style="green")
        self.status_table.add_row("Current Page", "0")
        self.status_table.add_row("Current Panel", "0")
        self.status_table.add_row("API Calls", "0")
        self.status_table.add_row("Cache Hits", "0")
        self.status_table.add_row("Estimated Time", "Calculating...")
        layout["status"].update(self.status_table)
        
        # Log panel
        self.log_text = Text()
        layout["log"].update(self.log_text)
        
        self.live = Live(layout, refresh_per_second=4, console=self.console)
        self.live.start()
        
    def update_progress(self, page: int, panel: int, status: str):
        """Update progress display"""
        self.progress.update(self.page_task, completed=page)
        self.progress.update(self.panel_task, completed=panel)
        self.add_log(f"[{datetime.now().strftime('%H:%M:%S')}] {status}")
        
    def add_log(self, message: str):
        """Add message to log panel"""
        self.log_text.append(f"\n{message}")
        if len(self.log_text.plain.split('\n')) > 10:
            lines = self.log_text.plain.split('\n')
            self.log_text = Text('\n'.join(lines[-10:]))
```

## Data Models

### Core Data Structures

```python
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

class PanelType(Enum):
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE_UP = "close_up"
    SPLASH = "splash"

@dataclass
class Dialogue:
    character: str
    text: str
    emotion: Optional[str] = None
    
@dataclass
class Caption:
    text: str
    position: str = "top"
    style: str = "narration"
    
@dataclass
class SoundEffect:
    text: str
    style: str = "bold"
    size: str = "large"
    position: Optional[Dict[str, float]] = None

@dataclass
class Panel:
    number: int
    description: str
    panel_type: PanelType
    dialogue: List[Dialogue]
    captions: List[Caption]
    sound_effects: List[SoundEffect]
    characters: List[str]
    
@dataclass
class Page:
    number: int
    panels: List[Panel]
    layout: str = "standard"  # standard, splash, double-spread
    
@dataclass
class GeneratedPanel:
    panel: Panel
    image_data: bytes
    generation_time: float
    metadata: Dict[str, Any]
    
@dataclass
class CharacterReference:
    name: str
    appearance_description: str
    reference_image: Optional[bytes] = None
    personality_traits: List[str] = None
```

## API Integration Details

### Gemini Flash 2.5 Text Model

Used for:
- Enhancing panel descriptions
- Generating consistent character descriptions
- Script analysis and validation

Configuration:
```python
text_config = {
    'thinkingConfig': {
        'thinkingBudget': -1  # Unlimited thinking time
    },
    'temperature': 0.7,
    'max_output_tokens': 2048
}
```

### Gemini Flash 2.5 Image Model

Used for:
- Panel image generation
- Character reference sheet creation
- Style consistency samples

Configuration:
```python
image_config = {
    'responseModalities': ['IMAGE'],
    'thinkingConfig': {
        'thinkingBudget': -1
    },
    'image_size': '1024x1536',  # Comic panel aspect ratio
    'image_quality': 'high'
}
```

## Performance Optimizations

### 1. Caching Strategy

```python
class CacheManager:
    def __init__(self, cache_dir: str = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.memory_cache = LRUCache(maxsize=100)
        self.disk_cache = DiskCache(self.cache_dir)
        
    def get_cache_key(self, panel: Panel, style_hash: str) -> str:
        """Generate deterministic cache key"""
        content = f"{panel.description}{style_hash}"
        return hashlib.sha256(content.encode()).hexdigest()
```

### 2. Batch Processing

```python
class BatchProcessor:
    def __init__(self, max_concurrent: int = 4):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = RateLimiter(calls_per_minute=60)
        
    async def process_batch(
        self, 
        panels: List[Panel]
    ) -> List[GeneratedPanel]:
        """Process multiple panels concurrently"""
        tasks = []
        for panel in panels:
            task = self._process_with_limit(panel)
            tasks.append(task)
            
        return await asyncio.gather(*tasks)
```

### 3. Progressive Loading

- Generate low-resolution drafts first
- Upgrade to high-resolution on approval
- Stream results as they complete

## Error Handling

```python
class ComicCreatorError(Exception):
    """Base exception for Comic Creator"""
    pass

class ScriptParsingError(ComicCreatorError):
    """Error parsing comic script"""
    pass

class APIError(ComicCreatorError):
    """Gemini API error"""
    pass

class ConsistencyError(ComicCreatorError):
    """Style consistency error"""
    pass

async def with_retry(
    func, 
    max_retries: int = 3,
    backoff_factor: float = 2.0
):
    """Retry wrapper for API calls"""
    for attempt in range(max_retries):
        try:
            return await func()
        except APIError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = backoff_factor ** attempt
            await asyncio.sleep(wait_time)
```

## Configuration Management

### Environment Variables (.env)

```bash
# API Configuration
GEMINI_API_KEY=your-api-key-here

# Performance Settings
MAX_CONCURRENT_REQUESTS=4
CACHE_ENABLED=true
CACHE_DIR=.cache

# Output Settings
DEFAULT_OUTPUT_DIR=./output
DEFAULT_IMAGE_FORMAT=png
DEFAULT_DPI=300

# Development
DEBUG=false
LOG_LEVEL=INFO
```

### Configuration Files

```yaml
# config/default.yaml
style:
  art_style: "modern comic book"
  color_palette: "vibrant"
  line_weight: "medium"
  shading: "cel-shaded"

generation:
  panel_size: [1024, 1536]
  quality: "high"
  consistency_weight: 0.7

text:
  font_family: "Comic Sans MS"
  bubble_style: "classic"
  caption_style: "box"
  
output:
  formats: ["png", "pdf", "cbz"]
  page_size: [2400, 3600]
  dpi: 300

performance:
  cache_enabled: true
  max_workers: 4
  batch_size: 10
```

## CLI Interface

```python
import click
from pathlib import Path

@click.group()
@click.option('--config', default='config/default.yaml')
@click.option('--verbose', is_flag=True)
@click.pass_context
def cli(ctx, config, verbose):
    """Comic Book Creator CLI"""
    ctx.ensure_object(dict)
    ctx.obj['CONFIG'] = load_config(config)
    ctx.obj['VERBOSE'] = verbose

@cli.command()
@click.argument('script', type=click.Path(exists=True))
@click.option('--output', '-o', default='./output')
@click.option('--pages', help='Page range (e.g., 1-5)')
@click.option('--style', help='Art style preset')
@click.option('--quality', type=click.Choice(['draft', 'standard', 'high']))
@click.option('--format', multiple=True, default=['png'])
@click.pass_context
async def generate(ctx, script, output, pages, style, quality, format):
    """Generate comic from script"""
    config = ctx.obj['CONFIG']
    
    # Initialize pipeline
    pipeline = ProcessingPipeline(config)
    
    # Process options
    options = ProcessingOptions(
        page_range=parse_page_range(pages),
        style_override=style,
        quality=quality or config.generation.quality,
        export_formats=format
    )
    
    # Run generation with progress UI
    ui = ProgressUI()
    ui.start_generation(
        total_pages=count_pages(script),
        total_panels=count_panels(script)
    )
    
    try:
        result = await pipeline.process_script(
            script_path=script,
            output_dir=output,
            options=options
        )
        
        ui.complete(f"Generated {len(result.pages)} pages")
        
    except Exception as e:
        ui.error(f"Generation failed: {e}")
        raise
        
@cli.command()
@click.argument('script', type=click.Path(exists=True))
def validate(script):
    """Validate script format"""
    parser = ScriptParser()
    result = parser.validate_format(Path(script).read_text())
    
    if result.is_valid:
        click.echo("✓ Script is valid")
    else:
        click.echo("✗ Script validation failed:")
        for error in result.errors:
            click.echo(f"  - {error}")
            
@cli.command()
def styles():
    """List available art styles"""
    styles = load_styles()
    table = Table(title="Available Art Styles")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    
    for name, desc in styles.items():
        table.add_row(name, desc)
        
    console = Console()
    console.print(table)
```

## Testing Strategy

### Unit Tests

```python
# tests/test_parser.py
import pytest
from src.parser import ScriptParser

def test_parse_standard_format():
    script = """
    PAGE 1
    
    PANEL 1
    Wide shot of city.
    
    CAPTION: The year 2089...
    """
    parser = ScriptParser()
    result = parser.parse_script(script)
    
    assert len(result.pages) == 1
    assert len(result.pages[0].panels) == 1
    assert result.pages[0].panels[0].captions[0].text == "The year 2089..."

# tests/test_consistency.py
async def test_consistency_manager():
    manager = ConsistencyManager()
    manager.load_style(test_style_config)
    
    prompt = manager.build_consistent_prompt(
        "Character walks down street",
        previous_panels=[]
    )
    
    assert "modern comic book" in prompt
    assert "vibrant" in prompt
```

### Integration Tests

```python
# tests/test_integration.py
@pytest.mark.asyncio
async def test_full_pipeline():
    pipeline = ProcessingPipeline(test_config)
    
    result = await pipeline.process_script(
        "tests/fixtures/sample_script.txt",
        "tests/output",
        ProcessingOptions(page_range=[1])
    )
    
    assert len(result.pages) == 1
    assert result.pages[0].composed_image is not None
```

## Deployment Considerations

### Virtual Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate
source venv/bin/activate  # Unix/macOS
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Requirements

```txt
# requirements.txt
google-genai>=1.0.0
python-dotenv>=1.0.0
click>=8.1.0
rich>=13.0.0
Pillow>=10.0.0
pyyaml>=6.0
aiofiles>=23.0.0
numpy>=1.24.0
asyncio>=3.11.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### Makefile

```makefile
.PHONY: install test build clean run

install:
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt

test:
	. venv/bin/activate && pytest tests/ -v --cov=src

build:
	. venv/bin/activate && python -m build

run:
	. venv/bin/activate && python -m src.cli

clean:
	rm -rf venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .cache
	find . -type d -name "*.egg-info" -exec rm -rf {} +

lint:
	. venv/bin/activate && ruff check src/
	. venv/bin/activate && mypy src/

format:
	. venv/bin/activate && black src/ tests/
	. venv/bin/activate && isort src/ tests/
```

## Security Considerations

1. **API Key Management**
   - Store in `.env` file (never commit)
   - Use environment variables
   - Implement key rotation

2. **Input Validation**
   - Sanitize script inputs
   - Validate file paths
   - Limit file sizes

3. **Rate Limiting**
   - Implement exponential backoff
   - Track API usage
   - Queue management

4. **Data Privacy**
   - Local caching only
   - No telemetry without consent
   - Secure temporary file handling

## Future Enhancements

1. **Advanced Features**
   - Multi-language support
   - Voice-to-script conversion
   - Animation frame generation
   - 3D panel depth maps

2. **Optimization**
   - GPU acceleration for image processing
   - Distributed processing support
   - Smart pre-caching

3. **Integration**
   - Adobe Creative Suite plugins
   - Web-based interface
   - Cloud deployment options
   - Version control integration

## Conclusion

This architecture provides a robust, scalable foundation for the Comic Book Creator tool. The modular design allows for easy extension and maintenance, while the focus on consistency and quality ensures professional-grade output. The integration with Gemini Flash 2.5's advanced capabilities enables both high-quality image generation and sophisticated text rendering, making it a comprehensive solution for comic book creation.