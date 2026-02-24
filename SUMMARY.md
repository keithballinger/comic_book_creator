# Repository Summary

**Comic Book Creator** is a Python CLI that turns plain-text comic scripts into
fully illustrated comic books — no drawing skills required. You write the
screenplay; Google's Gemini generates the art.

## What It Does

Hand the tool a script written in a lightweight, industry-flavoured format
(`PAGE 1 → PANEL 1 → description + dialogue + SFX`) and it will:

1. **Parse & validate** the script into structured data models.
2. **Generate every panel** as an AI image via the Gemini API, with rate
   limiting and parallel-generation support.
3. **Keep characters looking like themselves** across panels through a
   reference-image system (character sheets, location refs, style guides) and a
   dedicated consistency manager.
4. **Compose pages** by laying out panels into professional comic-page grids
   with configurable layouts.
5. **Export** the result as PNG, PDF, or CBZ.

## Tech Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3 (async throughout) |
| Image generation | Google Gemini API (`google-genai`) |
| Image processing | Pillow / NumPy |
| CLI framework | Click + Rich (progress bars, tables, colour) |
| Config | YAML via PyYAML |
| Testing | pytest (async, mocking, coverage) |
| Linting / Formatting | Ruff, Black, isort, mypy |

## Architecture at a Glance

```
Script text
  │
  ▼
ScriptParser ──▶ ComicScript model
  │
  ▼
ProcessingPipeline
  ├─ ReferenceManager  (character / location / object / style-guide sheets)
  ├─ PanelGenerator    (Gemini calls, rate limiting, consistency)
  └─ PageCompositor    (layout engine, exports)
        │
        ▼
   PNG / PDF / CBZ output
```

The codebase also ships a **reference-experiments** subsystem (`refexp`) that
lets you parameterise prompts with style variables (e.g. "60 % noir, 40 % Van
Gogh") and batch-generate comparison grids — essentially an A/B testing rig for
artistic direction.

## In One Sentence

It is a screenwriter-to-comic-book compiler powered by generative AI: you
supply the words, it supplies the pictures, and a surprisingly thoughtful
consistency engine makes sure your hero doesn't change face between panels.
