# Comic Book Creator

Transform comic book scripts into fully illustrated comics using AI-powered image generation.

## Features

- **Script Parsing**: Parse industry-standard comic book scripts with panels, dialogue, captions, and sound effects
- **AI Panel Generation**: Generate consistent comic panels using Google's Gemini API
- **Visual Consistency**: Maintain character appearances and art style across panels
- **Text Rendering**: Overlay dialogue balloons, captions, and sound effects on panels
- **Page Composition**: Automatically arrange panels into professional comic page layouts
- **Multiple Styles**: Support for various art styles (comic, manga, graphic novel, etc.)
- **CLI Interface**: Rich command-line interface with progress tracking

## Installation

```bash
# Clone the repository
git clone https://github.com/keithballinger/comic_book_creator.git
cd comic_book_creator

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up your Gemini API key
export GEMINI_API_KEY="your-api-key-here"
# Or create a .env file with: GEMINI_API_KEY=your-api-key-here
```

## Quick Start

1. **Validate a script**:
```bash
python comic_creator.py validate red_comet.txt
```

2. **Generate a comic**:
```bash
python comic_creator.py generate example/superpowers/superpowers.txt -o output/superpowers/
```

3. **Initialize a new project**:
```bash
python comic_creator.py init
```

4. **List available styles**:
```bash
python comic_creator.py styles
```

## Script Format

Comic scripts should follow this format:

```
PAGE 1

PANEL 1
Description of the panel scene.
CHARACTER: Dialogue goes here.
CAPTION: Narration text.
SFX: BOOM!

PANEL 2
Another panel description.
CHARACTER (emotion): More dialogue.
```

## CLI Commands

### generate
Generate a comic from a script file.

```bash
python comic_creator.py generate script.txt [OPTIONS]

Options:
  -o, --output PATH           Output directory
  -c, --config PATH           Configuration file
  -s, --style [comic|manga|graphic_novel|cartoon]  Art style preset
  -q, --quality [draft|standard|high]  Output quality
  -p, --pages TEXT            Page range (e.g., 1-3)
  --parallel/--sequential     Parallel panel generation
  --no-text                   Skip text rendering
  -f, --format [png|pdf|cbz]  Export formats
  -v, --verbose               Verbose output
```

### validate
Check if a script file is valid.

```bash
python comic_creator.py validate script.txt
```

### init
Initialize a new comic project with sample files.

```bash
python comic_creator.py init
```

### styles
List all available art styles.

```bash
python comic_creator.py styles
```

## Configuration

Create a `comic_config.yaml` file to customize settings:

```yaml
project:
  name: my-comic
  author: Your Name

generation:
  style: comic
  quality: standard
  panel_width: 800
  panel_height: 600
  dpi: 300

api:
  rate_limit: 30

output:
  formats:
    - png
    - pdf
  directory: output
```

## Architecture

The system consists of several key components:

- **Parser**: Converts script text into structured data models
- **Panel Generator**: Creates individual panel images using Gemini API
- **Consistency Manager**: Maintains visual coherence across panels
- **Text Renderer**: Overlays dialogue and effects on panels
- **Page Compositor**: Arranges panels into page layouts
- **Processing Pipeline**: Orchestrates the entire generation workflow
- **CLI Interface**: User-friendly command-line interface

## Testing

Run the test suite:

```bash
make test
```

Run with coverage:

```bash
pytest tests/ --cov=src --cov-report=html
```

## Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run linter
ruff check src/

# Format code
black src/ tests/

# Type checking
mypy src/
```

## Project Structure

```
comic_book_creator/
├── src/
│   ├── api/          # Gemini API integration
│   ├── config/       # Configuration management
│   ├── generator/    # Panel generation and consistency
│   ├── models/       # Data models
│   ├── output/       # Text rendering and composition
│   ├── parser/       # Script parsing
│   ├── processor/    # Processing pipeline
│   └── cli.py        # CLI interface
├── tests/            # Test suite
├── examples/         # Example scripts
└── comic_creator.py  # Main entry point
```

## License

Apache License 2.0 - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with Google's Gemini API for AI image generation
- Uses Pillow for image processing
- Rich library for beautiful CLI output
