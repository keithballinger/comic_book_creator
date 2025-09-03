#!/bin/bash

# Simple script to generate all example comics
# Usage: ./generate_all.sh

set -e

# Find Python command (for macOS compatibility)
PYTHON_CMD=""
for cmd in python3 python python3.12 python3.11 python3.10 python3.9 python3.8; do
    if command -v $cmd &> /dev/null; then
        PYTHON_CMD=$cmd
        break
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Error: Python not found. Please install Python 3.8+"
    echo "On macOS: brew install python3"
    exit 1
fi

echo "🎨 Generating all example comics..."
echo "Using Python: $PYTHON_CMD"
echo ""

# Go to project root
cd "$(dirname "$0")/.."

# Create output directory
mkdir -p examples/generated_examples

# Generate each example (run from project root)
echo "📚 Generating Superpowers (original example)..."
$PYTHON_CMD -m comic_creator generate examples/superpowers/superpowers.txt --output examples/generated_examples/superpowers

echo "🦸 Generating Hero Rises (superhero)..."
$PYTHON_CMD -m comic_creator generate examples/genres/superhero/hero_rises.txt --output examples/generated_examples/hero_rises

echo "🕵️ Generating Dark City (noir)..."
$PYTHON_CMD -m comic_creator generate examples/genres/noir/dark_city.txt --output examples/generated_examples/dark_city

echo "🚀 Generating Space Station (sci-fi)..."
$PYTHON_CMD -m comic_creator generate examples/genres/scifi/space_station.txt --output examples/generated_examples/space_station

echo "☕ Generating Coffee Shop (slice of life)..."
$PYTHON_CMD -m comic_creator generate examples/genres/slice_of_life/coffee_shop.txt --output examples/generated_examples/coffee_shop

echo "⏱️ Generating One Page Wonder (single page)..."
$PYTHON_CMD -m comic_creator generate examples/lengths/single_page/one_page_wonder.txt --output examples/generated_examples/one_page_wonder

echo "🎯 Generating Consistent Hero (reference example)..."
$PYTHON_CMD -m comic_creator generate examples/references/with_characters/consistent_hero.txt --output examples/generated_examples/consistent_hero

echo "🐉 Generating Dragon Quest (fantasy)..."
$PYTHON_CMD -m comic_creator generate examples/genres/fantasy/dragon_quest.txt --output examples/generated_examples/dragon_quest

echo "👻 Generating Midnight Visitor (horror)..."
$PYTHON_CMD -m comic_creator generate examples/genres/horror/midnight_visitor.txt --output examples/generated_examples/midnight_visitor

echo "⏰ Generating Time Loop (full issue)..."
$PYTHON_CMD -m comic_creator generate examples/lengths/full_issue/time_loop.txt --output examples/generated_examples/time_loop

echo "🤖 Generating Robot Heart (short story)..."
$PYTHON_CMD -m comic_creator generate examples/lengths/short_story/robot_heart.txt --output examples/generated_examples/robot_heart

echo "📚 Generating Mystic Library (location reference)..."
$PYTHON_CMD -m comic_creator generate examples/references/with_locations/mystic_library.txt --output examples/generated_examples/mystic_library

echo "🎌 Generating Manga Transformation (style reference)..."
$PYTHON_CMD -m comic_creator generate examples/references/with_style/manga_transformation.txt --output examples/generated_examples/manga_transformation

echo ""
echo "✅ All examples generated!"
echo "📁 Check the examples/generated_examples/ directory for your comics"
echo ""
echo "Generated comics:"
cd examples/generated_examples
for dir in */; do
    if [ -d "$dir" ]; then
        pages=$(find "$dir" -name "page_*.png" 2>/dev/null | wc -l | tr -d ' ')
        echo "  • ${dir%/} ($pages pages)"
    fi
done