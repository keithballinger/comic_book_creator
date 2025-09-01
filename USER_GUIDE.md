# Comic Book Creator - User Guide

## Overview

Comic Book Creator is an automated tool that transforms comic book scripts written in industry-standard format into fully illustrated comic pages using Google's Gemini Flash 2.5 image generation model.

## Key Features

- **Script-to-Visual**: Automatically parses industry-standard comic scripts
- **Consistent Art Style**: Maintains character and setting consistency across panels
- **Text Integration**: Leverages Gemini Flash 2.5's superior text rendering capabilities
- **Reference Image Support**: Uses previously generated panels as references for consistency
- **Batch Processing**: Generate entire issues or selected pages/panels

## Prerequisites

- Google Cloud account with Gemini API access
- API key for Gemini Flash 2.5
- Python 3.8+ or Go 1.19+ (depending on implementation)
- 8GB+ RAM recommended for processing large comics

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/comic-book-creator
cd comic-book-creator

# Install dependencies
make install

# Set up API credentials
export GEMINI_API_KEY="your-api-key-here"
```

## Script Format Requirements

The tool expects scripts in standard comic book format:

```
PAGE 1

PANEL 1
Wide establishing shot of Neo-Tokyo at sunset. Towering skyscrapers with neon signs.

CAPTION: The year 2089...

PANEL 2
Medium shot of MAYA (25, cyberpunk attire, blue hair) walking through crowded street.

MAYA: Another day in paradise.

SOUND EFFECT: WHOOSH!
```

### Required Elements:
- **PAGE [number]**: Marks new page
- **PANEL [number]**: Marks new panel
- **Panel descriptions**: Visual description after panel declaration
- **Character names**: In CAPS before dialogue
- **CAPTION**: For narrative text boxes
- **SOUND EFFECT**: For onomatopoeia

## Basic Usage

### Generate Full Comic
```bash
comic-creator generate --script my-comic.txt --output ./output/
```

### Generate Specific Pages
```bash
comic-creator generate --script my-comic.txt --pages 1-5 --output ./output/
```

### Generate Single Panel
```bash
comic-creator generate --script my-comic.txt --page 3 --panel 2 --output ./output/
```

## Configuration

Create a `config.yaml` file:

```yaml
style:
  art_style: "modern manga"
  color_palette: "vibrant"
  line_weight: "medium"
  
consistency:
  use_reference_images: true
  reference_weight: 0.7
  
text:
  font_style: "comic sans"
  bubble_style: "classic"
  
output:
  format: "png"
  resolution: "2400x3600"
  dpi: 300
```

## Advanced Features

### Character Reference Sheets

Create a character reference file (`characters.json`):

```json
{
  "MAYA": {
    "appearance": "25 years old, blue spiky hair, cyberpunk outfit with neon accents",
    "reference_image": "refs/maya_ref.png"
  },
  "ZANE": {
    "appearance": "30 years old, scarred face, military tactical gear",
    "reference_image": "refs/zane_ref.png"
  }
}
```

### Style Consistency

The tool maintains consistency by:
1. Using the first panel as a style reference
2. Passing previous panels as context to Gemini
3. Applying consistent prompting patterns
4. Caching character appearances

### Text Rendering

Gemini Flash 2.5 excels at text rendering. The tool:
- Automatically positions speech bubbles
- Renders clear, readable text
- Maintains proper reading order (left-to-right, top-to-bottom)
- Handles sound effects with appropriate styling

## Workflow Tips

### 1. Pre-Production
- Write complete script first
- Create character reference sheets
- Define consistent style guidelines

### 2. Generation
- Start with page 1 to establish style
- Review and approve before continuing
- Use approved panels as references

### 3. Post-Processing
- Tool outputs individual panels and composed pages
- Edit in your preferred software if needed
- Export in various formats (CBZ, PDF, PNG sequences)

## Command Reference

```bash
# Generate with custom style
comic-creator generate --script comic.txt --style "noir detective" 

# High quality mode (slower, better results)
comic-creator generate --script comic.txt --quality high

# Regenerate specific panel
comic-creator regenerate --page 2 --panel 3 --variation 2

# Export to CBZ format
comic-creator export --format cbz --input ./output/ --output my-comic.cbz

# List available styles
comic-creator styles list

# Validate script format
comic-creator validate --script comic.txt
```

## Troubleshooting

### Inconsistent Art Style
- Increase `reference_weight` in config
- Use more detailed character descriptions
- Generate in smaller batches

### Poor Text Rendering
- Ensure script uses proper formatting
- Reduce text length in individual bubbles
- Use `--text-priority` flag

### API Rate Limits
- Use `--delay` flag between requests
- Enable caching with `--cache`
- Process in batches during off-peak hours

### Memory Issues
- Process fewer pages at once
- Reduce output resolution
- Enable disk caching

## Best Practices

1. **Script Writing**
   - Be specific in panel descriptions
   - Include camera angles (close-up, wide shot, etc.)
   - Describe emotions and expressions

2. **Consistency**
   - Generate character sheets first
   - Approve initial pages before bulk generation
   - Keep reference folder organized

3. **Quality Control**
   - Review each page before proceeding
   - Use variation generation for unsatisfactory panels
   - Maintain style guide document

## Example Project Structure

```
my-comic/
├── script.txt           # Your comic script
├── config.yaml         # Configuration
├── characters.json     # Character definitions
├── refs/              # Reference images
│   ├── maya_ref.png
│   └── zane_ref.png
├── output/            # Generated content
│   ├── pages/
│   ├── panels/
│   └── final/
└── style-guide.md     # Visual style documentation
```

## Performance Optimization

- **Batch Size**: Process 5-10 pages at a time
- **Caching**: Enable to avoid regenerating approved panels
- **Parallel Processing**: Use `--parallel 4` for faster generation
- **Resolution**: Start with lower res for drafts, increase for finals

## Support & Community

- GitHub Issues: Report bugs and request features
- Discord: Join our community for tips and showcases
- Documentation: Full API docs at `/docs`

## License & Attribution

This tool is provided under MIT License. Generated images are subject to Gemini's terms of service and your usage rights.

---

*Happy Creating! Transform your stories into visual narratives with the power of AI.*