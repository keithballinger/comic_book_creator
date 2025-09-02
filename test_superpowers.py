#!/usr/bin/env python
"""Test script to validate caption and thought bubble parsing."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.parser import ScriptParser

def test_parser():
    """Test that the parser correctly extracts captions and thought bubbles."""
    parser = ScriptParser()
    script = parser.parse_script("examples/superpowers/superpowers.txt")
    
    print(f"Title: {script.title}")
    print(f"Pages: {len(script.pages)}")
    
    for page in script.pages:
        print(f"\nPage {page.number}: {len(page.panels)} panels")
        
        for panel in page.panels:
            print(f"\n  Panel {panel.number}:")
            print(f"    Description: {panel.description[:100]}...")
            
            if panel.dialogue:
                print(f"    Dialogue:")
                for d in panel.dialogue:
                    emotion_str = f" ({d.emotion})" if d.emotion else ""
                    print(f"      - {d.character}{emotion_str}: {d.text}")
            
            if panel.captions:
                print(f"    Captions:")
                for c in panel.captions:
                    print(f"      - {c.text}")
            
            if panel.sound_effects:
                print(f"    Sound Effects:")
                for sfx in panel.sound_effects:
                    print(f"      - {sfx.text}")

if __name__ == "__main__":
    test_parser()