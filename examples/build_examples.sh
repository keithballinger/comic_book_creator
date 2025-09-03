#!/bin/bash

# Comic Book Creator - Example Generation Script
# This script generates all example comics to showcase the system's capabilities

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
OUTPUT_DIR="generated_examples"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD=""  # Will be set by find_python()

echo -e "${BLUE}Comic Book Creator - Example Generation${NC}"
echo "============================================"
echo "This script will generate all example comics."
echo "Generated comics will be saved to: ${OUTPUT_DIR}/"
echo ""

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to generate a comic
generate_comic() {
    local script_file="$1"
    local output_name="$2"
    local description="$3"
    
    print_status "Generating: ${description}"
    echo "  Script: ${script_file}"
    echo "  Output: ${OUTPUT_DIR}/${output_name}"
    
    # Check if script file exists
    if [ ! -f "$script_file" ]; then
        print_error "Script file not found: $script_file"
        return 1
    fi
    
    # Build command
    local cmd="$PYTHON_CMD -m comic_creator generate \"$script_file\" --output \"${OUTPUT_DIR}/${output_name}\""
    
    # Note: References are used automatically if they exist in the reference storage
    # No need for a separate flag
    
    # Execute generation
    echo "  Command: $cmd"
    if eval "$cmd"; then
        print_status "✓ Generated successfully: ${output_name}"
    else
        print_error "✗ Failed to generate: ${output_name}"
        return 1
    fi
    echo ""
}

# Function to find Python command
find_python() {
    # Try different Python commands in order of preference
    for cmd in python3 python python3.12 python3.11 python3.10 python3.9 python3.8; do
        if command -v $cmd &> /dev/null; then
            PYTHON_CMD=$cmd
            return 0
        fi
    done
    return 1
}

# Function to check if comic creator is available
check_comic_creator() {
    print_status "Checking comic creator installation..."
    
    # Find Python command
    if ! find_python; then
        print_error "Python is not installed or not in PATH"
        print_status "Please install Python 3.8+ or check your PATH"
        print_status "On macOS, you can install Python with: brew install python3"
        exit 1
    fi
    
    print_status "Found Python: $PYTHON_CMD"
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
    print_status "Python version: $PYTHON_VERSION"
    
    # Check if we can run from project root
    cd "$PROJECT_ROOT"
    
    # Check if comic_creator.py exists
    if [ ! -f "comic_creator.py" ]; then
        print_error "comic_creator.py not found in project root: $PROJECT_ROOT"
        print_status "Make sure you're running this script from the examples directory"
        exit 1
    fi
    
    print_status "✓ Comic creator found"
}

# Function to setup output directory
setup_output() {
    print_status "Setting up output directory..."
    
    # Create output directory if it doesn't exist
    mkdir -p "$OUTPUT_DIR"
    
    # Clean up old examples if they exist
    if [ "$(ls -A "$OUTPUT_DIR" 2>/dev/null)" ]; then
        read -p "Output directory contains files. Clear it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "${OUTPUT_DIR:?}"/*
            print_status "✓ Output directory cleared"
        else
            print_warning "Keeping existing files (may cause conflicts)"
        fi
    fi
    
    print_status "✓ Output directory ready: $OUTPUT_DIR"
}

# Function to create reference examples (optional)
create_reference_examples() {
    print_status "Creating example character references..."
    
    # Note: These are optional and will only be used if --use-references is specified
    
    # Create Captain Nova character reference
    if ! $PYTHON_CMD -m comic_creator reference exists character "Captain Nova" 2>/dev/null; then
        print_status "Creating Captain Nova character reference..."
        $PYTHON_CMD -m comic_creator reference create-character \
            --name "Captain Nova" \
            --description "Superhero with energy powers, blue and gold costume, flowing cape, determined expression" \
            --poses "standing,flying,fighting" \
            --expressions "determined,heroic,concerned" || true
    else
        print_status "Captain Nova reference already exists"
    fi
    
    # Create Shadowmaw villain reference  
    if ! $PYTHON_CMD -m comic_creator reference exists character "Shadowmaw" 2>/dev/null; then
        print_status "Creating Shadowmaw character reference..."
        $PYTHON_CMD -m comic_creator reference create-character \
            --name "Shadowmaw" \
            --description "Dark villain with claws, shadow powers, menacing appearance, evil grin" \
            --poses "menacing,attacking,defeated" \
            --expressions "evil,angry,plotting" || true
    else
        print_status "Shadowmaw reference already exists"
    fi
    
    print_warning "Reference creation is optional - examples will work without them"
}

# Main generation function
generate_all_examples() {
    print_status "Starting example generation..."
    echo ""
    
    # Original example
    print_status "=== Original Example ==="
    generate_comic \
        "$SCRIPT_DIR/superpowers/superpowers.txt" \
        "superpowers" \
        "Original Superpowers Example - Kid discovers comic creation tool"
    
    # Genre examples
    print_status "=== Genre Examples ==="
    
    generate_comic \
        "$SCRIPT_DIR/genres/superhero/hero_rises.txt" \
        "superhero_hero_rises" \
        "Superhero Origin Story - Hero gets powers from cosmic meteor"
    
    generate_comic \
        "$SCRIPT_DIR/genres/noir/dark_city.txt" \
        "noir_dark_city" \
        "Noir Detective Story - Detective investigates in shadowy city"
    
    generate_comic \
        "$SCRIPT_DIR/genres/scifi/space_station.txt" \
        "scifi_space_station" \
        "Sci-Fi First Contact - Aliens arrive at space station"
    
    generate_comic \
        "$SCRIPT_DIR/genres/slice_of_life/coffee_shop.txt" \
        "slice_of_life_coffee_shop" \
        "Slice of Life - Quiet birthday moment in coffee shop"
    
    # Length examples
    print_status "=== Length Examples ==="
    
    generate_comic \
        "$SCRIPT_DIR/lengths/single_page/one_page_wonder.txt" \
        "single_page_last_second" \
        "Single Page Story - New Year's reconciliation in 9 panels"
    
    # Additional genre examples
    print_status "=== Additional Genre Examples ==="
    
    generate_comic \
        "$SCRIPT_DIR/genres/fantasy/dragon_quest.txt" \
        "fantasy_dragon_quest" \
        "Fantasy Adventure - Dragon and village partnership"
    
    generate_comic \
        "$SCRIPT_DIR/genres/horror/midnight_visitor.txt" \
        "horror_midnight_visitor" \
        "Psychological Horror - Ghost story with a twist"
    
    # Length variations
    print_status "=== Length Variation Examples ==="
    
    generate_comic \
        "$SCRIPT_DIR/lengths/full_issue/time_loop.txt" \
        "full_issue_time_loop" \
        "Full Issue (22 pages) - Quantum time loop adventure"
    
    generate_comic \
        "$SCRIPT_DIR/lengths/short_story/robot_heart.txt" \
        "short_story_robot_heart" \
        "Short Story (8 pages) - Robot gains emotions"
    
    # Reference examples (these work better with references but will work without)
    print_status "=== Reference Examples ==="
    
    generate_comic \
        "$SCRIPT_DIR/references/with_characters/consistent_hero.txt" \
        "reference_consistent_hero" \
        "Character Consistency Example"
    
    generate_comic \
        "$SCRIPT_DIR/references/with_locations/mystic_library.txt" \
        "reference_mystic_library" \
        "Location Consistency - Magical library between dimensions"
    
    generate_comic \
        "$SCRIPT_DIR/references/with_style/manga_transformation.txt" \
        "reference_manga_style" \
        "Style Guide Example - Manga/anime aesthetic"
    
    # Note: The system automatically uses references if they exist
    # No separate generation with/without references needed
}

# Function to display results
show_results() {
    print_status "Generation complete!"
    echo ""
    echo "Generated comics are in: ${OUTPUT_DIR}/"
    echo ""
    
    if [ -d "$OUTPUT_DIR" ] && [ "$(ls -A "$OUTPUT_DIR" 2>/dev/null)" ]; then
        echo "Generated examples:"
        for dir in "$OUTPUT_DIR"/*/; do
            if [ -d "$dir" ]; then
                local name=$(basename "$dir")
                local pages=$(find "$dir" -name "page_*.png" 2>/dev/null | wc -l)
                echo "  • $name ($pages pages)"
            fi
        done
        echo ""
        echo "You can view the comics by opening the PNG files in each directory."
        echo "Each comic has individual panel images and composed page images."
    else
        print_warning "No examples were generated successfully"
    fi
}

# Function to display usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help              Show this help message"
    echo "  -o, --output DIR        Set output directory (default: generated_examples)"
    echo "  -r, --create-references Create example character references first"
    echo "  -c, --clean             Clean output directory before generating"
    echo "  --example NAME          Generate only specific example"
    echo ""
    echo "Examples:"
    echo "  $0                      # Generate all examples"
    echo "  $0 -r                   # Create references first, then generate all"
    echo "  $0 -o my_comics         # Generate to custom directory"
    echo "  $0 --example superhero  # Generate only superhero example"
    echo ""
}

# Parse command line arguments
CREATE_REFERENCES=false
CLEAN_OUTPUT=false
SPECIFIC_EXAMPLE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -r|--create-references)
            CREATE_REFERENCES=true
            shift
            ;;
        -c|--clean)
            CLEAN_OUTPUT=true
            shift
            ;;
        --example)
            SPECIFIC_EXAMPLE="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_status "Starting Comic Book Creator Example Generation"
    echo ""
    
    # Check system requirements
    check_comic_creator
    
    # Setup output directory
    setup_output
    
    # Create references if requested
    if [ "$CREATE_REFERENCES" = "true" ]; then
        create_reference_examples
        echo ""
    fi
    
    # Generate examples
    if [ -n "$SPECIFIC_EXAMPLE" ]; then
        print_status "Generating specific example: $SPECIFIC_EXAMPLE"
        # This would need specific logic for each example
        print_error "Specific example generation not implemented yet"
        exit 1
    else
        generate_all_examples
    fi
    
    # Show results
    show_results
}

# Run main function
main "$@"