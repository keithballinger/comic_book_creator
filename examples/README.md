# Comic Book Creator Examples

This directory contains example scripts demonstrating various genres, lengths, and features of the comic book creator.

## Directory Structure

```
examples/
├── genres/           # Different comic genres
│   ├── superhero/   # Classic superhero action
│   ├── noir/        # Detective noir style
│   ├── scifi/       # Science fiction
│   ├── fantasy/     # Fantasy adventure
│   ├── slice_of_life/ # Everyday stories
│   └── horror/      # Horror/thriller
├── lengths/         # Different comic lengths
│   ├── single_page/ # One-page stories
│   ├── short_story/ # 4-8 page stories
│   └── full_issue/  # 22-24 page standard issue
├── references/      # Using the reference system
│   ├── with_characters/ # Character consistency
│   ├── with_locations/  # Location consistency
│   └── with_style/      # Style guide usage
└── techniques/      # Special techniques
    ├── action_sequences/
    ├── emotional_moments/
    └── visual_storytelling/
```

## Quick Start

### Running an Example

```bash
# Run a simple superhero example
python -m comic_creator generate examples/genres/superhero/hero_rises.yaml

# Generate with references for consistency
python -m comic_creator generate examples/references/with_characters/consistent_hero.yaml --use-references

# Generate a full issue
python -m comic_creator generate examples/lengths/full_issue/issue_001.yaml --quality high
```

### Example Formats

All examples are provided in YAML format for easy reading and editing. They follow this structure:

```yaml
title: "Example Comic"
author: "Your Name"
genre: "superhero"
style: "modern comic book art"

pages:
  - number: 1
    panels:
      - number: 1
        size: large
        description: "Detailed panel description"
        dialogue:
          - character: "Hero"
            text: "This is dialogue"
            type: speech
```

## Examples by Category

### Genres

1. **Superhero** (`hero_rises.yaml`)
   - Classic hero vs villain
   - Action-packed panels
   - Dynamic poses and effects

2. **Noir** (`dark_city.yaml`)
   - Moody atmosphere
   - Internal monologue
   - Shadow-heavy visuals

3. **Sci-Fi** (`space_station.yaml`)
   - Futuristic settings
   - Technical descriptions
   - Alien characters

4. **Fantasy** (`dragon_quest.yaml`)
   - Magical elements
   - Medieval settings
   - Creature designs

5. **Slice of Life** (`coffee_shop.yaml`)
   - Character interactions
   - Everyday settings
   - Emotional beats

6. **Horror** (`abandoned_house.yaml`)
   - Suspense building
   - Atmospheric descriptions
   - Jump scares

### Lengths

1. **Single Page** - Complete stories in one page
2. **Short Story** - 4-8 page narratives
3. **Full Issue** - Standard 22-24 page comics

### Reference Usage

Examples showing how to use the reference system for consistency:
- Character references across multiple panels
- Location consistency throughout a scene
- Style guide application

## Tips for Using Examples

1. **Start Simple**: Begin with single-page examples to understand the format
2. **Modify Gradually**: Take an example and change small parts
3. **Mix and Match**: Combine elements from different examples
4. **Use References**: See the reference examples for consistent characters
5. **Experiment**: Try different panel sizes and layouts

## Creating Your Own

Use these examples as templates for your own comics. Copy an example that's close to what you want and modify it to tell your story.

### Key Elements to Consider

- **Panel Size**: Use larger panels for important moments
- **Page Turns**: End odd-numbered pages with hooks
- **Dialogue Placement**: Keep dialogue concise
- **Visual Descriptions**: Be specific about mood and atmosphere
- **Character Emotions**: Include emotional states in descriptions

## Common Patterns

### Action Sequence
```yaml
panels:
  - size: small
    description: "Close-up of eyes widening"
  - size: small  
    description: "Hand reaching for weapon"
  - size: large
    description: "Full body leap into action"
```

### Emotional Beat
```yaml
panels:
  - size: medium
    description: "Character's shocked expression"
  - size: small
    description: "Single tear rolling down cheek"
  - size: medium
    description: "Embrace between characters"
```

### Establishing Shot
```yaml
panels:
  - size: large
    description: "Wide cityscape at sunset"
  - size: medium
    description: "Street level view of neighborhood"
  - size: small
    description: "Apartment window lit from within"
```