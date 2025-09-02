# Creating Your Own Comic Scripts

This guide will help you write effective comic scripts for the Comic Book Creator system.

## Script Format Overview

Comic scripts use **plain text format** following industry-standard comic script conventions:

```
Title: Your Comic Title

PAGE ONE (4 Panels)

Panel 1
Visual description of what we see in the panel.

CHARACTER: What they say.

Panel 2
Another panel description here.

CHARACTER (Thought Bubble): Internal thoughts.

SFX: Sound effects like BOOM!

CAPTION: Narrative text or scene setting.
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
```
Close-up of Sarah's hands shaking as she reaches for the door handle. Sweat visible on her palm.
```

**Not Good:**
```
Sarah was nervous about what she might find.
```

### Include Technical Details

**Camera Angles:**
- "wide shot" - shows full scene
- "close-up" - focuses on face/detail
- "bird's eye view" - from above
- "low angle" - from below (makes subject look powerful)
- "dutch angle" - tilted (creates tension)

**Setting Details:**
- Time of day, weather, mood
- Lighting conditions
- Important props or background elements

## Character Writing

### Dialogue Best Practices

1. **Keep it concise** - Comics are visual medium
2. **Show personality** - Each character should sound unique  
3. **Match the moment** - Dialogue should fit the action
4. **Read aloud** - Good comic dialogue sounds natural

### Dialogue Types

```
CHARACTER: Standard speech bubble

CHARACTER (Thought Bubble): Internal thoughts

CHARACTER (whispering): Quiet speech - small bubble

CHARACTER (shouting): LOUD SPEECH - jagged bubble

SFX: CRASH! - Sound effects

CAPTION: Narrative text boxes
```

## Format Rules

### Page Headers
```
PAGE ONE (4 Panels)
PAGE TWO (6 Panels) 
PAGE THREE
```

### Panel Structure
```
Panel 1
[Panel description goes here]

[Dialogue and effects follow]

Panel 2
[Next panel description]
```

### Character Names
- Always UPPERCASE in dialogue
- Consistent spelling throughout
- Use parentheses for dialogue modifiers: `CHARACTER (whispering):`

### Sound Effects
```
SFX: BOOM!
SFX: crash...
SFX: WHOOSH!
```

### Captions
```
CAPTION: Narrative text
CAPTION (CHARACTER): Character narration
```

## Using the Reference System

The reference system works with the plain text format to ensure character and location consistency.

### Character References

1. **Create Character References First:**
```bash
python -m comic_creator reference create-character \
  --name "Captain Nova" \
  --description "Superhero with blue and gold costume, cape" \
  --poses "standing,flying,fighting"
```

2. **Add Characters Line to Script:**
```
Title: My Comic

CHARACTERS: Captain Nova, Shadowmaw

PAGE ONE
```

3. **Reference in Panels:**
```
Panel 1
CAPTAIN NOVA stands on the rooftop, cape flowing in the wind.
```

The system will automatically use the character reference to maintain consistent appearance.

### Location References

1. **Create Location References:**
```bash
python -m comic_creator reference create-location \
  --name "Hero Headquarters" \
  --description "High-tech underground base"
```

2. **Reference in Panel Descriptions:**
```
Panel 1
Interior of Hero Headquarters. Banks of computer monitors cast blue light across the room.
```

## Example Script Structure

```
Title: Example Comic

CHARACTERS: Hero, Villain

PAGE ONE (4 Panels)

Panel 1
Wide shot of the city at night. Hero stands on a rooftop, looking down at the streets below.

CAPTION: The city never sleeps. Neither does justice.

Panel 2
Close-up of Hero's determined face.

HERO: Time to patrol.

Panel 3
Hero leaps from building to building, cape streaming behind.

SFX: WHOOSH!

Panel 4
Hero lands near an alley where VILLAIN is threatening a civilian.

HERO: Stop right there!

VILLAIN: You're too late, hero!

PAGE TWO (3 Panels)

Panel 1
SPLASH PAGE - Epic battle between Hero and Villain with energy blasts and debris flying.

SFX: CRASH! BOOM! ZAP!

Panel 2
Hero stands victorious, Villain defeated on the ground.

HERO: Justice prevails.

Panel 3
Hero helps up the grateful civilian as police arrive in the background.

CIVILIAN: Thank you!

CAPTION: Another night, another victory for good.
```

## Genre-Specific Tips

### Superhero
- Dynamic action descriptions
- Bold sound effects: "BOOM!", "POW!", "ZAP!"
- Heroic poses and dramatic moments
- Clear good vs evil conflicts

### Noir
- Atmospheric descriptions with shadow and light
- Internal monologue via captions
- Urban, gritty settings
- Morally ambiguous characters

### Sci-Fi
- Technical descriptions of futuristic elements
- World-building through visual details
- Alien or advanced technology
- Scientific concepts explained visually

### Slice of Life
- Realistic, everyday settings
- Character emotions and relationships
- Quiet, intimate moments
- Natural dialogue

## Common Mistakes to Avoid

### Too Much Dialogue
**Bad:**
```
Panel 1
HERO: I was just thinking about how we met three years ago when you saved my life and I realized that I needed to tell you how much that meant to me and how it changed everything.
```

**Good:**
```
Panel 1
HERO: Do you remember when we first met?

Panel 2
Flashback panel - Hero being rescued.

Panel 3
Back to present. Hero looks grateful.

HERO: You changed my life that day.
```

### Unclear Descriptions
**Bad:**
```
Panel 1
Something exciting happens.
```

**Good:**
```
Panel 1
The villain's laser beam cuts through the steel door, sparks flying as Hero dives for cover behind an overturned car.
```

### Page Turn Problems
**Bad:**
```
PAGE ONE (odd page)
Panel 4
Hero opens the door and sees the villain's secret lair! # Reveal on wrong page

PAGE TWO (even page)
Panel 1
Hero fights the villain.
```

**Good:**
```
PAGE ONE (odd page)  
Panel 4
Hero's hand reaches for the mysterious door handle. # Cliffhanger

PAGE TWO (even page)
Panel 1
The door opens to reveal the villain's secret lair! # Reveal
```

## Testing Your Script

### Before Generation
1. Read script aloud to check flow
2. Verify character names are consistent
3. Check page/panel numbering
4. Ensure descriptions are visual
5. Confirm dialogue fits comic format

### Test Generation
```bash
python -m comic_creator generate examples/your_script.txt
```

### After Generation
1. Check if characters look consistent
2. Verify scenes match your vision
3. Note any needed description improvements
4. Test with reference system if needed

## Example Workflow

1. **Plan** - Outline your story beats
2. **Write** - Create script in plain text format
3. **Test** - Generate a few pages to see results
4. **Create References** - If you need character consistency
5. **Refine** - Adjust descriptions based on output
6. **Generate** - Create full comic

## Resources

- See `examples/genres/` for different genre examples
- See `examples/lengths/` for different story lengths
- See `examples/references/` for reference system usage
- Look at existing comics for pacing inspiration
- Study the included "Superpowers" example

## Quick Reference

### Basic Format
```
Title: Comic Title

PAGE ONE (Panel Count)

Panel 1
[Description]

CHARACTER: Dialogue

SFX: Sound

CAPTION: Narration
```

### Special Elements
- **Splash Page**: Single full-page panel
- **Thought Bubble**: `CHARACTER (Thought Bubble):`
- **Whisper**: `CHARACTER (whispering):`
- **Shout**: `CHARACTER (shouting):`
- **Flashback**: Mention in description
- **Close-up**: Specify in description
- **Wide shot**: Specify in description

Remember: Start simple! Copy an existing example and modify it to tell your story. The system is designed to turn your written descriptions into visual comic panels.