# Comic Book Creator Examples

This directory contains example scripts demonstrating various genres, lengths, and features of the comic book creator.

## Directory Structure

```
examples/
├── genres/           # Different comic genres
│   ├── superhero/   # Classic superhero action
│   ├── noir/        # Detective noir style
│   ├── scifi/       # Science fiction
│   └── slice_of_life/ # Everyday stories
├── lengths/         # Different comic lengths
│   ├── single_page/ # One-page stories
│   └── short_story/ # 4-8 page stories
├── references/      # Using the reference system
│   └── with_characters/ # Character consistency
└── superpowers/     # Original example
```

## Quick Start

### Running Examples

**Generate All Examples:**
```bash
# Simple: Generate all examples at once
./examples/generate_all.sh

# Advanced: Full featured generation with options
./examples/build_examples.sh --create-references
```

**Generate Individual Examples:**
```bash
# Run a simple superhero example
python -m comic_creator generate examples/genres/superhero/hero_rises.txt

# Generate with references for consistency
python -m comic_creator generate examples/references/with_characters/consistent_hero.txt --use-references

# Generate the original superpowers example  
python -m comic_creator generate examples/superpowers/superpowers.txt
```

### Script Format

All examples use **plain text format** following comic script conventions:

```
Title: Example Comic

PAGE ONE (4 Panels)

Panel 1
Visual description of what happens in this panel.

CHARACTER: What they say.

Panel 2
Another panel description.

CHARACTER (Thought Bubble): Internal thoughts.

SFX: BOOM!

CAPTION: Narrative text.
```

## Examples by Category

### Genres

1. **Superhero** (`hero_rises.txt`)
   - Classic hero origin story
   - Action-packed transformation
   - Dynamic poses and effects
   - Heroic dialogue and moments

2. **Noir** (`dark_city.txt`)
   - Detective story with atmosphere
   - Shadow-heavy descriptions
   - Internal monologue via captions
   - Mysterious and moody

3. **Sci-Fi** (`space_station.txt`)
   - First contact scenario
   - Futuristic technology
   - Alien characters
   - Cosmic scope and wonder

4. **Slice of Life** (`coffee_shop.txt`)
   - Quiet character moment
   - Everyday setting
   - Human connection
   - Emotional subtlety

### Lengths

1. **Single Page** (`one_page_wonder.txt`)
   - Complete story in 9 panels
   - Tight, economical storytelling
   - Strong emotional beat
   - Clear beginning/middle/end

2. **Short Story** (`the_interview.txt`)
   - 4-page thriller with twist
   - Character development
   - Building suspense
   - Satisfying resolution

### Reference Usage

1. **Character Consistency** (`consistent_hero.txt`)
   - Shows same character across panels
   - Demonstrates reference integration
   - Maintains visual consistency

## Script Format Details

### Page Headers
```
PAGE ONE (4 Panels)
PAGE TWO (6 Panels)
PAGE THREE
```

### Character Names
- Always UPPERCASE in dialogue
- Use parentheses for modifiers: `CHARACTER (whispering):`
- Thought bubbles: `CHARACTER (Thought Bubble):`

### Visual Descriptions
- Be specific and visual
- Include camera angles (close-up, wide shot)
- Mention mood and atmosphere
- Describe important details

### Sound Effects
```
SFX: BOOM!
SFX: crash...
SFX: WHOOSH!
```

### Captions
```
CAPTION: Narrative text
CAPTION: Meanwhile, across town...
```

## Using with the Reference System

### Character References
1. Create character references first:
```bash
python -m comic_creator reference create-character \
  --name "Captain Nova" \
  --description "Superhero in blue and gold costume"
```

2. Add characters line to script:
```
CHARACTERS: Captain Nova, Villain Name
```

3. Reference in descriptions:
```
Panel 1
CAPTAIN NOVA stands heroically on the rooftop.
```

### Tips for Better Results

1. **Visual Descriptions**: Focus on what we see, not what characters think
2. **Panel Variety**: Mix close-ups, wide shots, and medium shots
3. **Page Turns**: End odd pages with cliffhangers
4. **Dialogue**: Keep it concise and character-specific
5. **Pacing**: Use panel size to control story rhythm

## Common Patterns

### Action Sequence
```
Panel 1
Hero spots danger - close-up of alert eyes.

Panel 2  
Wide shot of Hero leaping into action.

Panel 3
SPLASH - Epic battle scene with villain.

SFX: CRASH! BOOM!
```

### Emotional Beat
```
Panel 1
Character receives bad news - medium shot showing shock.

Panel 2
Close-up of character's emotional reaction.

Panel 3
Wide shot showing character's isolation or environment.
```

### Dialogue Scene
```
Panel 1
CHARACTER A: We need to talk.

Panel 2
CHARACTER B: I was afraid you'd say that.

Panel 3
Over-the-shoulder shot showing both characters.

CHARACTER A: It's about what happened yesterday...
```

## Modifying Examples

To create your own comics:

1. **Copy an Example**: Start with the closest genre/length
2. **Change the Title**: Make it your own
3. **Modify Characters**: Replace with your characters
4. **Adjust Plot**: Change the story to yours
5. **Update Descriptions**: Make panels match your vision
6. **Test Generate**: See how it looks
7. **Refine**: Adjust based on results

## Advanced Features

### Reference Integration
- Character consistency across panels
- Location consistency from different angles
- Style guide application

### Special Panel Types
- **Splash Page**: Single full-page panel for impact
- **Close-up**: Focus on face or important detail
- **Wide Shot**: Establish setting or show scope
- **Bird's Eye**: Overhead view for orientation

### Storytelling Techniques
- **Show Don't Tell**: Use visuals over exposition
- **Page Turns**: Use for reveals and cliffhangers  
- **Panel Size**: Larger for important moments
- **Silent Panels**: No dialogue, pure visual

## Getting Help

If you need assistance:

1. **Start Simple**: Use the single-page examples first
2. **Copy and Modify**: Don't start from scratch
3. **Test Often**: Generate panels frequently to see results
4. **Read the Guide**: Check `CREATING_YOUR_OWN.md` for detailed help
5. **Study Comics**: Look at professional comics for inspiration

## File Extensions

All script files use `.txt` extension and plain text format. The system parses the text to understand:
- Page and panel structure
- Character dialogue and actions  
- Visual descriptions
- Sound effects and captions

Remember: The goal is to write clear, visual descriptions that can be turned into comic book panels. Focus on what the reader will see!