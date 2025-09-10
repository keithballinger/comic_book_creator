# Reference Experiments User Guide

## Overview

Reference Experiments is a feature that allows you to systematically test different variations of image generation prompts by creating multiple images with parameterized substitutions. This helps you understand how different prompt variations affect the generated images using Gemini's image generation models.

## Basic Usage

Create a reference experiment file (e.g., `experiment.yaml`) with the following YAML structure:

```yaml
# Reference experiment configuration
name: "Character Style Variations"
description: "Testing different anime styles and details"

# Prompt template with {variable} placeholders
prompt: |
  The image is {anime_percentage} anime style with {detail} detail.
  The character has {hair_color} hair.

# Variable definitions
variables:
  anime_percentage: ["5%", "25%", "90%"]
  detail: ["low", "medium", "ultra-high"]
  hair_color: ["blonde", "black", "red", "blue"]

# Optional settings
settings:
  quality: high  # low, medium, high
  seed: 42  # for reproducible random selection
```

### File Format

The YAML file structure includes:
1. **Metadata**: Optional `name` and `description` fields
2. **Prompt Template**: Multi-line string with `{variable}` placeholders
3. **Variables**: Dictionary mapping variable names to lists of values
4. **Settings**: Optional configuration overrides

### Command Line Usage

```bash
# Generate up to 10 random combinations (default)
python comic_creator.py ref-exp experiment.yaml

# Generate 5 specific combinations
python comic_creator.py ref-exp experiment.yaml --iterations 5

# Generate all possible combinations
python comic_creator.py ref-exp experiment.yaml --iterations all

# Specify output directory
python comic_creator.py ref-exp experiment.yaml --output output/experiments/

# Set random seed for reproducible results
python comic_creator.py ref-exp experiment.yaml --seed 42
```

## Output

The tool will:
1. Generate images for each combination using Gemini Flash 2.5 Image API
2. Save images with descriptive names in `output/reference_experiments/`
3. Update `reference_images.md` with:
   - The exact prompt used
   - The image filename
   - Timestamp of generation
   - Variable values used
   - Image generation metadata

## Example Output in reference_images.md

```markdown
## Reference Experiment: 2025-01-09_14-30-25

**Name**: Character Style Variations
**Source File**: experiments/character_style.yaml
**Total Combinations**: 12
**Generated**: 10 (random selection)

### Combination 1
- **Variables**: 
  - anime_percentage: 25%
  - detail: medium
  - hair_color: blonde
- **Prompt**: The image is 25% anime style with medium detail. The character has blonde hair.
- **Image**: `output/reference_experiments/exp_20250109_143025_001_25pct_medium_blonde.png`
- **Model**: gemini-2.5-flash-image-preview
- **Generated**: 2025-01-09 14:30:25

### Combination 2
- **Variables**: 
  - anime_percentage: 90%
  - detail: ultra-high
  - hair_color: red
- **Prompt**: The image is 90% anime style with ultra-high detail. The character has red hair.
- **Image**: `output/reference_experiments/exp_20250109_143027_002_90pct_ultrahigh_red.png`
- **Model**: gemini-2.5-flash-image-preview
- **Generated**: 2025-01-09 14:30:27
```

## Advanced Features

### Multiple Values in One Prompt

You can use the same variable multiple times:
```yaml
name: "Style Consistency Test"
prompt: "A {style} painting of a {style} landscape with {style} influences."
variables:
  style: ["impressionist", "cubist", "surrealist", "abstract"]
```

### Complex Substitutions

Variables can contain any string, including punctuation and spaces:
```yaml
name: "Scene and Lighting Variations"
prompt: |
  The scene takes place {setting}.
  The lighting is {lighting_style}.
variables:
  setting: 
    - "in a dark forest"
    - "under water"
    - "in outer space"
    - "on a mountain peak"
  lighting_style:
    - "dramatic with harsh shadows"
    - "soft and diffused"
    - "neon-lit cyberpunk"
    - "golden hour sunset"
```

### Nested Variables

You can create complex combinations with multiple variable layers:
```yaml
name: "Character Composition Test"
prompt: "Create a {composition} image of a {character_type} wearing {outfit}."
variables:
  composition: 
    - "close-up portrait"
    - "wide landscape shot"
    - "action scene"
  character_type:
    - "warrior"
    - "mage"
    - "robot"
  outfit:
    - "armor"
    - "robes"
    - "casual clothes"
```

### Advanced Settings

Configure experiment behavior with additional settings:
```yaml
name: "Advanced Experiment"
prompt: "Generate {subject} in {style} style"
variables:
  subject: ["character", "landscape", "object"]
  style: ["photorealistic", "cel-shaded anime", "watercolor painting"]

settings:
  quality: high
  iterations: 20  # Override command-line default
  parallel: 5  # Concurrent generations
  retry_on_failure: true
  save_metadata: true
  
# Image generation parameters
image_settings:
  width: 1024
  height: 1536
  model: "gemini-2.5-flash-image-preview"
```

## Configuration

You can configure reference experiments in your `comic_config.yaml`:

```yaml
reference_experiments:
  max_variables: 10
  max_values_per_variable: 100
  max_total_combinations: 10000
  default_iterations: 10
  output_directory: "output/reference_experiments"
  concurrent_generations: 3
  api_rate_limit: 10  # requests per minute
  image_quality: high  # high, medium, low
  save_metadata: true
```

## Tips for Effective Experiments

1. **Start Small**: Test with 2-3 variables with 2-3 values each before scaling up
2. **Use Descriptive Names**: Make variable names self-documenting
3. **Document Purpose**: Use the `name` and `description` fields in YAML
4. **Incremental Testing**: Use `--iterations 5` to test before running all combinations
5. **Organize by Theme**: Create separate YAML files for different experiment types
6. **Version Control**: Keep your YAML files in version control to track changes
7. **Use Seeds**: Use `--seed` for reproducible random selections or set in YAML settings

## Integration with Comic Generation

Reference experiments can be used to:
- Test character designs before generating full comics
- Find optimal style settings for your project
- Generate consistency references for characters
- Create style guides for different scenes
- Test panel composition variations

### Using Results in Comic Generation

Once you've found optimal settings through experiments, you can:
1. Update your comic configuration with the best style parameters
2. Use generated images as reference images for character consistency
3. Include successful prompts in your character reference descriptions

## Error Handling

The tool handles various error conditions:
- **API Rate Limiting**: Automatically retries with exponential backoff
- **Invalid Variables**: Reports which variables are undefined in the template
- **Generation Failures**: Logs failures and continues with remaining combinations
- **File System Errors**: Gracefully handles permission and space issues

## Limitations

- Maximum of 10 variables per experiment
- Each variable can have up to 100 values
- Total combinations limited to 10,000 when using `--iterations all`
- Variable names must be valid identifiers (letters, numbers, underscores)
- Image generation subject to Gemini API quotas and rate limits
- Large experiments may take significant time due to API rate limits