# Reference System Examples

This directory demonstrates how to use the reference system for consistent character appearances, locations, and art styles across your comics.

## Setting Up References

Before using these examples, you'll need to create the referenced characters, locations, and style guides:

### Character References

```bash
# Create Captain Nova character
python -m comic_creator reference create-character \
  --name "Captain Nova" \
  --description "Superhero with energy powers, blue and gold costume, cape" \
  --poses "standing,flying,fighting" \
  --expressions "determined,heroic,concerned"

# Create Shadowmaw villain  
python -m comic_creator reference create-character \
  --name "Shadowmaw" \
  --description "Dark villain with claws, shadow powers, menacing appearance" \
  --poses "menacing,attacking,defeated" \
  --expressions "evil,angry,plotting"

# Create Detective Blake
python -m comic_creator reference create-character \
  --name "Detective Blake" \
  --description "Noir detective, trench coat, fedora, world-weary expression" \
  --poses "walking,investigating,contemplative" \
  --expressions "determined,suspicious,weary"
```

### Location References

```bash
# Create Hero Headquarters
python -m comic_creator reference create-location \
  --name "Hero Headquarters" \
  --description "High-tech underground base with computer consoles and monitors" \
  --type "interior" \
  --angles "wide_interior,computer_console,entrance" \
  --lighting "dramatic_overhead,screen_glow"

# Create City Street
python -m comic_creator reference create-location \
  --name "City Street" \
  --description "Urban street with storefronts, streetlights, typical city atmosphere" \
  --type "exterior" \
  --angles "street_level,aerial_view" \
  --lighting "streetlights,neon_signs"

# Create Dive Bar (noir setting)
python -m comic_creator reference create-location \
  --name "Dive Bar" \
  --description "Smoky bar with dim lighting, worn stools, noir atmosphere" \
  --type "interior" \
  --angles "bar_view,corner_booth" \
  --lighting "dim,venetian_blind_shadows"
```

### Style Guide References

```bash
# Create Film Noir Classic style guide
python -m comic_creator reference create-style \
  --name "Film Noir Classic" \
  --description "High contrast black and white with selective color, dramatic shadows" \
  --art-style "noir-photography" \
  --colors "#000000,#FFFFFF,#808080,#FF0000" \
  --mood "dramatic,mysterious,high-contrast"
```

## Using the Examples

Once you've created the references, you can use the example scripts:

```bash
# Generate comic with character consistency
python -m comic_creator generate examples/references/with_characters/consistent_hero.yaml --use-references

# Generate with location consistency  
python -m comic_creator generate examples/references/with_locations/location_consistency.yaml --use-references

# Generate with style guide
python -m comic_creator generate examples/references/with_style/style_guide_example.yaml --use-references
```

## How References Work

### Character References
- Ensure the same character looks identical across all panels
- Maintain consistent costume, proportions, and facial features
- Allow for different poses and expressions while keeping core appearance
- Reference images guide the AI generation

### Location References  
- Keep architectural details consistent across different angles
- Maintain spatial relationships between elements
- Allow for different lighting and weather while keeping structure
- Ensure believable world-building

### Style Guide References
- Apply consistent art style across entire comic
- Control color palette, lighting approach, and visual mood
- Override generic style descriptions with specific artistic choices
- Ensure visual coherence throughout the story

## Benefits of Using References

1. **Visual Consistency**: Characters and locations look the same throughout
2. **Professional Quality**: Maintains believable world-building
3. **Time Saving**: No need to describe appearance details repeatedly
4. **Style Control**: Consistent artistic approach across all panels
5. **Character Recognition**: Readers can easily follow characters through scenes

## Tips for Effective Reference Usage

1. **Be Specific**: Detailed reference descriptions lead to better consistency
2. **Use Multiple Poses**: Create references with various poses for flexibility
3. **Plan Ahead**: Create references before writing scripts that use them
4. **Test Generation**: Generate a few panels to verify reference quality
5. **Iterate**: Update references based on generation results

## Troubleshooting

### Character doesn't look consistent
- Check that character name in script matches reference exactly
- Ensure reference has enough detail in description
- Try generating reference images first to establish appearance

### Location changes between panels
- Verify location name matches reference exactly  
- Add more architectural details to location reference
- Use specific angle descriptions

### Style not applied
- Check style guide name is exact match
- Ensure style guide has detailed specifications
- Style guides override script-level style descriptions