# Reference Experiments Examples

This directory contains example YAML files for the reference experiments feature of Comic Book Creator.

## Available Examples

### 1. character_styles.yaml
Tests different art styles and emotional expressions for character portraits.
- **Variables**: 5 (style, character_type, emotion, direction, background)
- **Total Combinations**: 720
- **Recommended Use**: Finding the right character design style

### 2. scene_lighting.yaml
Experiments with lighting conditions and atmospheric effects.
- **Variables**: 5 (scene_type, lighting, time_of_day, weather, mood)
- **Total Combinations**: 1280
- **Recommended Use**: Understanding lighting impact on mood

### 3. composition_tests.yaml
Explores camera angles and panel compositions.
- **Variables**: 6 (action, camera_angle, composition_type, focus_element, panel_style, text_element)
- **Total Combinations**: 3000
- **Recommended Use**: Testing panel layouts and framing

### 4. simple_test.yaml
A minimal example for quick testing.
- **Variables**: 3 (style, subject, color)
- **Total Combinations**: 27
- **Recommended Use**: Quick tests and debugging

## Usage

Run an experiment with default settings (10 random combinations):
```bash
python comic_creator.py ref-exp examples/reference_experiments/character_styles.yaml
```

Generate all combinations (use with caution for large sets):
```bash
python comic_creator.py ref-exp examples/reference_experiments/simple_test.yaml --iterations all
```

Generate specific number of combinations:
```bash
python comic_creator.py ref-exp examples/reference_experiments/scene_lighting.yaml --iterations 20
```

Set a seed for reproducible results:
```bash
python comic_creator.py ref-exp examples/reference_experiments/character_styles.yaml --seed 42
```

## Creating Your Own Experiments

Copy one of these examples and modify it for your needs:

```yaml
name: "Your Experiment Name"
description: "What this experiment tests"

prompt: |
  Your prompt template with {variable1} and {variable2}.
  Can be multiple lines.

variables:
  variable1: ["option1", "option2", "option3"]
  variable2: ["choice1", "choice2"]

settings:
  quality: high
  iterations: 10
  seed: 42  # Optional, for reproducibility

image_settings:
  width: 1024
  height: 1024
  model: "gemini-2.5-flash-image-preview"
```

## Tips

1. **Start Small**: Test with few variables and values first
2. **Use Seeds**: Set a seed for reproducible random selections
3. **Monitor Costs**: Each image generation uses API quota
4. **Organize Results**: Results are saved in timestamped session folders
5. **Check reference_images.md**: All experiments are logged here

## Variable Limits

- Maximum variables per experiment: 10
- Maximum values per variable: 100
- Maximum total combinations: 10,000

## Output Structure

Generated images are saved to:
```
output/reference_experiments/
└── session_YYYYMMDD_HHMMSS/
    ├── exp_timestamp_001_variable_values.png
    ├── exp_timestamp_002_variable_values.png
    └── ...
```

Results are also logged in `reference_images.md` at the project root.