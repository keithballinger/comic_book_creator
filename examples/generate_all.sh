#!/bin/bash

# Simple script to generate all example comics
# Usage: ./generate_all.sh

set -e

echo "🎨 Generating all example comics..."
echo ""

# Create output directory
mkdir -p generated_examples
cd generated_examples

# Generate each example
echo "📚 Generating Superpowers (original example)..."
python -m comic_creator generate ../superpowers/superpowers.txt --output superpowers

echo "🦸 Generating Hero Rises (superhero)..."
python -m comic_creator generate ../genres/superhero/hero_rises.txt --output hero_rises

echo "🕵️ Generating Dark City (noir)..."
python -m comic_creator generate ../genres/noir/dark_city.txt --output dark_city

echo "🚀 Generating Space Station (sci-fi)..."
python -m comic_creator generate ../genres/scifi/space_station.txt --output space_station

echo "☕ Generating Coffee Shop (slice of life)..."
python -m comic_creator generate ../genres/slice_of_life/coffee_shop.txt --output coffee_shop

echo "⏱️ Generating One Page Wonder (single page)..."
python -m comic_creator generate ../lengths/single_page/one_page_wonder.txt --output one_page_wonder

echo "🎯 Generating Consistent Hero (reference example)..."
python -m comic_creator generate ../references/with_characters/consistent_hero.txt --output consistent_hero

echo ""
echo "✅ All examples generated!"
echo "📁 Check the generated_examples/ directory for your comics"
echo ""
echo "Generated comics:"
for dir in */; do
    if [ -d "$dir" ]; then
        pages=$(find "$dir" -name "page_*.png" 2>/dev/null | wc -l | tr -d ' ')
        echo "  • ${dir%/} ($pages pages)"
    fi
done