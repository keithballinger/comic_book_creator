# Creating Your Own Comic Scripts

This guide will help you write effective comic scripts for the Comic Book Creator system.

## Script Format Overview

Comic scripts use YAML format with a specific structure:

```yaml
title: "Your Comic Title"
author: "Your Name"
genre: "superhero/noir/scifi/fantasy/etc"
style: "art style description"
style_guide: "Optional: Reference to style guide"

pages:
  - number: 1
    layout: "layout_type"
    panels:
      - number: 1
        size: large/medium/small/splash
        description: "Visual description"
        characters: ["Character Name"]
        location: "Location Name"
        dialogue:
          - character: "Character Name"
            text: "What they say"
            type: speech/thought/whisper/shout/narration/caption
```

## Planning Your Comic

### 1. Story Structure

**Single Page** (1 page)
- Simple concept or moment
- 6-9 panels typically
- Clear beginning, middle, end

**Short Story** (4-8 pages)
- Complete narrative arc
- 4-6 panels per page average
- One main conflict/revelation

**Full Issue** (20-24 pages)
- Complex story with subplots
- Multiple character introductions
- Cliffhanger ending

### 2. Pacing Guidelines

**Panel Count per Page:**
- Action scenes: 3-5 panels (larger panels)
- Dialogue scenes: 5-7 panels (smaller panels)
- Establishing shots: 1-3 panels (large/splash)

**Page Turn Rules:**
- Odd pages end with hooks/cliffhangers
- Even pages reveal/resolve
- Page 1 is always right-side (splash recommended)

## Writing Effective Panel Descriptions

### Be Visual, Not Literary

**Good:**
```yaml
description: "Close-up of Sarah's hands shaking as she reaches for the door handle. Sweat visible on her palm."
```

**Not Good:**
```yaml
description: "Sarah was nervous about what she might find."
```

### Include Technical Details

**Camera Angles:**
- "wide shot" - shows full scene
- "close-up" - focuses on face/detail
- "bird's eye view" - from above
- "low angle" - from below (makes subject look powerful)
- "dutch angle" - tilted (creates tension)

**Lighting:**
- "dramatic lighting" - high contrast
- "soft lighting" - gentle, even
- "backlighting" - lit from behind
- "moonlight" - cool, blue tones
- "neon lighting" - colorful city glow

**Mood Keywords:**
- tense, peaceful, ominous, hopeful, chaotic, serene, mysterious, epic

## Character Writing

### Dialogue Best Practices

1. **Keep it concise** - Comics are visual medium
2. **Show personality** - Each character should sound unique  
3. **Match the moment** - Dialogue should fit the action
4. **Read aloud** - Good comic dialogue sounds natural

### Dialogue Types

```yaml
dialogue:
  - character: "Hero"
    text: "This ends now!"
    type: speech           # Standard dialogue bubble
    emotion: "determined"   # Affects character expression

  - character: "Hero"
    text: "What have I done?"
    type: thought          # Thought bubble

  - character: "Villain"  
    text: "You fool!"
    type: shout           # Jagged bubble, bold text

  - character: "Hero"
    text: "Stay close..."
    type: whisper         # Dotted bubble, smaller text

  - character: ""
    text: "CRASH!"
    type: sfx             # Sound effect

  - character: "Narrator"
    text: "Meanwhile, across town..."
    type: narration       # Narrative box

  - character: "Hero"
    text: "I should have known."
    type: caption         # Character narrative box
```

## Panel Sizes and Layouts

### Panel Size Guide

**Splash** - Full page
- Major reveals
- Establishing shots  
- Climactic moments
- Issue openers

**Large** - 1/2 to 2/3 page
- Important action
- Character introductions
- Emotional beats

**Medium** - 1/3 to 1/2 page  
- Standard dialogue
- Mid-action shots
- Character reactions

**Small** - 1/4 page or less
- Quick cuts
- Close-ups
- Time passing
- Reaction shots

### Common Layouts

**Six Panel Grid**
```yaml
layout: "six_panel_grid"
# Good for: dialogue scenes, steady pacing
```

**Action Layout**  
```yaml
layout: "action_layout"
# Good for: fight scenes, dynamic moments
```

**Splash Opener**
```yaml  
layout: "splash_opener"
# Good for: issue #1s, major reveals
```

## Using the Reference System

### Character Consistency

1. **Create Character References First:**
```bash
python -m comic_creator reference create-character \
  --name "Your Hero" \
  --description "Detailed appearance description" \
  --poses "standing,running,fighting" \
  --expressions "happy,angry,sad"
```

2. **Reference in Script:**
```yaml
characters: ["Your Hero"]  # Must match reference name exactly
```

### Location Consistency

1. **Create Location References:**
```bash
python -m comic_creator reference create-location \
  --name "Hero Base" \
  --description "High-tech underground facility" \
  --angles "wide,console_view,entrance"
```

2. **Reference in Script:**
```yaml
location: "Hero Base"  # Must match reference name
```

### Style Guides

1. **Create Style Guide:**
```bash
python -m comic_creator reference create-style \
  --name "My Style" \
  --art-style "realistic" \
  --colors "#FF0000,#0000FF,#FFFFFF"
```

2. **Reference in Script:**
```yaml
style_guide: "My Style"  # Applies to entire comic
```

## Genre-Specific Tips

### Superhero
- Dynamic poses and action
- Bold colors and effects
- Clear good vs evil
- Inspiring dialogue
- Lots of "BOOM!" and "POW!"

### Noir
- High contrast lighting
- Urban settings
- Internal monologue
- Moral ambiguity  
- Atmospheric mood

### Sci-Fi
- Technical descriptions
- Futuristic elements
- World-building details
- Scientific concepts
- Alien/tech terminology

### Fantasy
- Magical elements
- Medieval/ancient settings
- Mythical creatures
- Heroic quests
- Poetic language

### Horror
- Building tension
- Shadow and darkness
- Sudden reveals
- Psychological elements
- Atmospheric dread

## Common Mistakes to Avoid

### Too Much Dialogue
```yaml
# BAD - Wall of text
dialogue:
  - character: "Hero"
    text: "I was just thinking about how we met three years ago when you saved my life and I realized that I needed to tell you how much that meant to me and how it changed everything about how I see the world and my place in it."
    type: speech

# GOOD - Broken up
panels:
  - description: "Hero's thoughtful expression"
    dialogue:
      - character: "Hero"
        text: "Do you remember when we first met?"
        type: speech
  - description: "Flashback panel showing the rescue"  
    dialogue:
      - character: "Hero"
        text: "You saved my life that day."
        type: speech
  - description: "Back to present, Hero looks grateful"
    dialogue:
      - character: "Hero"  
        text: "It changed everything."
        type: speech
```

### Unclear Panel Descriptions
```yaml
# BAD - Vague
description: "Something exciting happens"

# GOOD - Specific  
description: "The villain's laser beam cuts through the steel door, sparks flying as Hero dives for cover behind an overturned car"
```

### Ignoring Page Turns
```yaml  
# BAD - Reveal on same page as setup
- number: 3  # Odd page
  panels:
    - description: "Hero opens the mysterious door"
    - description: "Inside is the villain's secret lair!" # Should be on page 4!

# GOOD - Cliffhanger on odd page
- number: 3  # Odd page  
  panels:
    - description: "Hero's hand reaches for the mysterious door handle"
    - description: "The door creaks open, revealing..."
- number: 4  # Even page
  panels:  
    - description: "The villain's secret lair!"
```

## Testing Your Script

### Before Generation
1. Read aloud to check dialogue flow
2. Verify character names match references exactly
3. Check location names match references
4. Ensure panel descriptions are visual
5. Confirm page count fits intended format

### After Generation
1. Check character consistency across panels
2. Verify locations look consistent
3. Assess overall visual flow
4. Note any needed reference improvements
5. Adjust script based on results

## Example Workflow

1. **Plan** - Outline story beats
2. **Create References** - Characters, locations, style
3. **Write Script** - Following format guidelines
4. **Test Generate** - Generate first few pages
5. **Refine** - Adjust script and references
6. **Full Generate** - Create complete comic
7. **Review** - Check consistency and quality

## Resources

- See `examples/genres/` for genre-specific examples
- See `examples/references/` for reference system usage
- See `examples/lengths/` for different story lengths
- Check the main documentation for CLI commands
- Refer to existing comics for pacing inspiration

## Getting Help

If you're stuck:
1. Start with the single-page examples
2. Copy and modify existing examples  
3. Focus on one element at a time (story, then characters, then dialogue)
4. Test generate frequently to see results
5. Use the reference system for consistency

Remember: Great comics are made through iteration. Start simple and build up complexity as you learn the system!