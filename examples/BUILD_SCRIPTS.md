# Example Build Scripts

This directory includes two scripts to automatically generate all example comics.

## Quick Generation

### `generate_all.sh` - Simple & Fast

The simplest way to generate all examples:

```bash
cd examples
./generate_all.sh
```

**What it does:**
- Generates all example comics to `generated_examples/` folder
- Simple output with progress indicators
- No extra features or options
- Perfect for quick testing

**Examples generated:**
- `superpowers/` - Original example (4 pages)
- `hero_rises/` - Superhero origin story (3 pages)  
- `dark_city/` - Noir detective story (2 pages)
- `space_station/` - Sci-fi first contact (2 pages)
- `coffee_shop/` - Slice of life moment (1 page)
- `one_page_wonder/` - Complete story in 9 panels (1 page)
- `consistent_hero/` - Character consistency demo (1 page)

## Advanced Generation

### `build_examples.sh` - Full Featured

More advanced script with options and error handling:

```bash
cd examples

# Basic usage
./build_examples.sh

# Create character references first
./build_examples.sh --create-references

# Custom output directory
./build_examples.sh --output my_comics

# Clean output directory first
./build_examples.sh --clean

# Get help
./build_examples.sh --help
```

**Features:**
- Colored output and status messages
- Error checking and recovery
- Optional reference creation
- Custom output directories
- Progress tracking
- Detailed results summary

**Options:**
- `-h, --help` - Show help message
- `-o, --output DIR` - Set output directory
- `-r, --create-references` - Create example character references
- `-c, --clean` - Clean output directory first

## What Gets Generated

Both scripts create the same comic examples, just with different levels of feedback:

```
generated_examples/
├── superpowers/           # Original kid + tablet story
│   ├── page_001_complete.png
│   ├── page_001/
│   │   └── panel_*.png
├── hero_rises/            # Superhero gets cosmic powers  
│   ├── page_001_complete.png
│   ├── page_002_complete.png
│   └── ...
├── dark_city/             # Noir detective mystery
├── space_station/         # Alien first contact
├── coffee_shop/           # Birthday in coffee shop
├── one_page_wonder/       # New Year's phone call
└── consistent_hero/       # Reference system demo
```

Each comic folder contains:
- `page_XXX_complete.png` - Full composed pages
- `page_XXX/` - Individual panel images
- `metadata.json` - Generation info

## Requirements

Both scripts require:
- Python 3.8+ installed
- Comic Creator system working
- Being run from the `examples/` directory
- Valid Gemini API key configured

## Usage Tips

**First time users:**
```bash
./generate_all.sh
```

**Developers/advanced users:**
```bash  
./build_examples.sh --create-references --clean
```

**Custom workflow:**
```bash
# Generate to specific folder
./build_examples.sh --output ~/Desktop/my_comics

# Just superhero examples
python -m comic_creator generate genres/superhero/hero_rises.txt --output my_hero_comic
```

## Troubleshooting

**Permission denied:**
```bash
chmod +x generate_all.sh build_examples.sh
```

**Comic creator not found:**
- Make sure you're in the project root directory
- Check that `comic_creator.py` exists
- Verify Python can import the modules

**Generation fails:**
- Check your Gemini API key is configured
- Ensure you have internet connection
- Try generating individual examples first

**Reference examples:**
- Reference examples work without references (just less consistent)
- Use `--create-references` to create character references first
- Reference creation is optional and may fail without breaking generation

## Output Structure

Generated comics include:
- **Individual panels** - Each panel as separate PNG
- **Composed pages** - Full pages with panels arranged
- **Metadata** - JSON with generation info and timing
- **Debug info** - Prompts and generation details (in debug/ folder)

Perfect for:
- Testing the system
- Showcasing different genres
- Learning comic script format
- Demonstrating reference consistency
- Creating sample content