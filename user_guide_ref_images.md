# Reference Experiments User Guide

## Overview

Reference Experiments is a feature that allows you to systematically test different variations of image generation prompts by creating multiple images with parameterized substitutions. This helps you understand how different prompt variations affect the generated images.

## Basic Usage

Create a reference experiment file (e.g., `experiment.ref`) with the following structure:

```
The image is {anime_percentage} anime style with {detail} detail.
The character has {hair_color} hair.

---
{anime_percentage} = [5%, 25%, 90%]
{detail} = [low, medium, ultra-high]
{hair_color} = [blonde, black, red, blue]
```

### File Format

1. **Prompt Section**: The top section contains your prompt template with placeholders in curly braces `{placeholder_name}`
2. **Separator**: Three dashes `---` separate the prompt from the variables
3. **Variables Section**: Define each placeholder with an array of string values to substitute

### Command Line Usage

```bash
# Generate up to 10 random combinations (default)
comic_book_creator ref-exp experiment.ref

# Generate 5 specific combinations
comic_book_creator ref-exp experiment.ref --iterations 5

# Generate all possible combinations
comic_book_creator ref-exp experiment.ref --iterations all
```

## Output

The tool will:
1. Generate images for each combination
2. Save images with descriptive names in `output/reference_experiments/`
3. Update `reference_images.md` with:
   - The exact prompt used
   - The image filename
   - Timestamp of generation
   - Variable values used

## Example Output in reference_images.md

```markdown
## Reference Experiment: 2025-01-09_14-30-25

### Combination 1
- **Variables**: anime_percentage=25%, detail=medium, hair_color=blonde
- **Prompt**: The image is 25% anime style with medium detail. The character has blonde hair.
- **Image**: `output/reference_experiments/exp_001_25pct_medium_blonde.png`
- **Generated**: 2025-01-09 14:30:25

### Combination 2
- **Variables**: anime_percentage=90%, detail=ultra-high, hair_color=red
- **Prompt**: The image is 90% anime style with ultra-high detail. The character has red hair.
- **Image**: `output/reference_experiments/exp_002_90pct_ultrahigh_red.png`
- **Generated**: 2025-01-09 14:30:27
```

## Advanced Features

### Multiple Values in One Prompt

You can use the same variable multiple times:
```
A {style} painting of a {style} landscape with {style} influences.

---
{style} = [impressionist, cubist, surrealist]
```

### Complex Substitutions

Variables can contain any string, including punctuation and spaces:
```
The scene takes place {setting}.

---
{setting} = [in a dark forest, under water, in outer space, on a mountain peak]
```

### Naming Convention

Generated images follow this pattern:
`exp_{number}_{sanitized_variable_values}.png`

Where sanitized values replace spaces with underscores and remove special characters.

## Tips for Effective Experiments

1. **Start Small**: Test with 2-3 variables with 2-3 values each before scaling up
2. **Use Descriptive Names**: Make variable names self-documenting
3. **Document Purpose**: Add comments in your .ref file using `#` at the start of a line
4. **Incremental Testing**: Use `--iterations 5` to test before running all combinations
5. **Organize by Theme**: Create separate .ref files for different experiment types

## Limitations

- Maximum of 10 variables per experiment
- Each variable can have up to 100 values
- Total combinations are limited to 10,000 when using `--iterations all`
- Variable names must be valid identifiers (letters, numbers, underscores)