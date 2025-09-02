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
cd examples

# Generate each example
echo "📚 Generating Superpowers (original example)..."
$PYTHON_CMD -m comic_creator generate superpowers/superpowers.txt --output generated_examples/superpowers

echo "🦸 Generating Hero Rises (superhero)..."
$PYTHON_CMD -m comic_creator generate genres/superhero/hero_rises.txt --output generated_examples/hero_rises

echo "🕵️ Generating Dark City (noir)..."
$PYTHON_CMD -m comic_creator generate genres/noir/dark_city.txt --output generated_examples/dark_city

echo "🚀 Generating Space Station (sci-fi)..."
$PYTHON_CMD -m comic_creator generate genres/scifi/space_station.txt --output generated_examples/space_station

echo "☕ Generating Coffee Shop (slice of life)..."
$PYTHON_CMD -m comic_creator generate genres/slice_of_life/coffee_shop.txt --output generated_examples/coffee_shop

echo "⏱️ Generating One Page Wonder (single page)..."
$PYTHON_CMD -m comic_creator generate lengths/single_page/one_page_wonder.txt --output generated_examples/one_page_wonder

echo "🎯 Generating Consistent Hero (reference example)..."
$PYTHON_CMD -m comic_creator generate references/with_characters/consistent_hero.txt --output generated_examples/consistent_hero

echo ""
echo "✅ All examples generated!"
echo "📁 Check the examples/generated_examples/ directory for your comics"
echo ""
echo "Generated comics:"
cd generated_examples
for dir in */; do
    if [ -d "$dir" ]; then
        pages=$(find "$dir" -name "page_*.png" 2>/dev/null | wc -l | tr -d ' ')
        echo "  • ${dir%/} ($pages pages)"
    fi
done