# Reference Image System - User Guide

## Overview
The Reference Image System allows you to create and manage consistent visual references for characters, locations, and objects in your comics. This ensures visual consistency across pages and helps maintain a professional, cohesive art style.

## Getting Started

### 1. Creating Character References
```bash
# Generate initial character reference
python comic_creator.py create-reference character "Alex the Adventurer" \
  --description "teenage hero with brown hair, brave expression, carrying backpack" \
  --poses "standing,pointing,surprised,determined" \
  --save-to references/characters/

# Use character in comic generation
python comic_creator.py generate script.txt \
  --character-refs references/characters/alex.json
```

### 2. Creating Location References
```bash
# Generate location reference
python comic_creator.py create-reference location "Enchanted Forest" \
  --description "mystical forest with tall trees, dappled sunlight, ancient stone altar" \
  --angles "wide-shot,close-up,aerial" \
  --lighting "dawn,midday,dusk" \
  --save-to references/locations/

# Use in generation
python comic_creator.py generate script.txt \
  --location-refs references/locations/enchanted_forest.json
```

### 3. Creating Object References
```bash
# Generate object reference  
python comic_creator.py create-reference object "Ancient Map" \
  --description "weathered parchment with mystical symbols, rolled and tied" \
  --views "closed,unrolled,detail" \
  --save-to references/objects/
```

## Advanced Usage

### Character Design Sheets
Create comprehensive character references with multiple expressions and poses:

```bash
python comic_creator.py create-character-sheet "Main Character" \
  --base-description "young adult hero in medieval clothing" \
  --expressions "happy,sad,angry,surprised,determined,worried" \
  --poses "standing,running,fighting,pointing,sitting" \
  --outfits "adventure-gear,formal,casual" \
  --save-to references/characters/main_character_sheet.json
```

### Style Guide Generation
Generate a visual style guide for consistency:

```bash
python comic_creator.py create-style-guide \
  --art-style "professional comic book art" \
  --color-palette "earthy-tones" \
  --line-style "clean,bold-outlines" \
  --lighting "dramatic,high-contrast" \
  --save-to references/style_guide.json
```

### Reference Management

#### List Available References
```bash
python comic_creator.py list-references
# Shows:
# Characters: alex, villain, mentor
# Locations: forest, castle, village
# Objects: sword, map, crystal
# Style Guides: fantasy_adventure
```

#### Update References
```bash
python comic_creator.py update-reference character alex \
  --add-pose "climbing" \
  --add-expression "focused"
```

#### Delete References
```bash
python comic_creator.py delete-reference character old_character
```

## Script Integration

### Using References in Scripts
Reference images are automatically used when character/location names match:

```
Title: The Adventure Continues

PAGE 1

Panel 1
Setting: Enchanted Forest (wide-shot, dawn lighting)
Alex: I must find the Ancient Map before sunset!
Caption: Our hero's quest continues...

Panel 2  
Setting: Enchanted Forest (close-up of stone altar)
Alex (determined): The legends spoke of this place.
```

### Manual Reference Override
Force specific reference usage:

```
Panel 1
Setting: Enchanted Forest @enchanted_forest_v2
Alex @alex_formal_outfit: Welcome to the royal court.
```

## Best Practices

### Character References
- Create references early in your project
- Include multiple poses and expressions
- Keep descriptions detailed but consistent
- Update references as your story evolves

### Location References  
- Generate establishing shots first
- Create detail views for important areas
- Consider different lighting conditions
- Include both interior and exterior views

### Object References
- Focus on story-important items
- Include multiple angles/states
- Consider how objects age/change
- Reference magical effects if applicable

### Style Consistency
- Create a project style guide first
- Use consistent art style descriptions
- Maintain color palette throughout
- Reference successful panels for future consistency

## Troubleshooting

### References Not Loading
```bash
# Check reference file exists
ls references/characters/alex.json

# Validate reference format
python comic_creator.py validate-reference references/characters/alex.json
```

### Inconsistent Results
- Ensure reference descriptions are detailed enough
- Check for conflicting style elements
- Consider regenerating outdated references
- Use style guide for consistency

### Storage Management
```bash
# Clean up unused references
python comic_creator.py cleanup-references --unused-only

# Archive old project references  
python comic_creator.py archive-references project_name
```

## Tips for Success

1. **Start Simple**: Begin with basic character and location references
2. **Iterate**: Refine references based on generation results
3. **Be Specific**: Detailed descriptions yield better consistency
4. **Plan Ahead**: Create references for all major story elements
5. **Maintain**: Regularly update references as your story evolves