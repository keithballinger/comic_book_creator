"""Tests for script parser module."""

import pytest
from pathlib import Path

from src.parser import ScriptParser, ScriptValidator
from src.models import ComicScript, PanelType


class TestScriptParser:
    """Test cases for ScriptParser class."""
    
    def test_parse_simple_script(self):
        """Test parsing a simple script."""
        script_content = """
Title: Test Comic

PAGE ONE (3 PANELS)

Panel 1
Wide shot of city.
CAPTION: The beginning.

Panel 2
Close-up of hero.
HERO (balloon): I will save the day!

Panel 3
Action scene.
SFX: BOOM!
"""
        parser = ScriptParser()
        script = parser.parse_content(script_content)
        
        assert script.title == "Test Comic"
        assert len(script.pages) == 1
        assert len(script.pages[0].panels) == 3
        
        # Check Panel 1
        panel1 = script.pages[0].panels[0]
        assert panel1.number == 1
        assert "Wide shot of city" in panel1.description
        assert len(panel1.captions) == 1
        assert panel1.captions[0].text == "The beginning."
        
        # Check Panel 2
        panel2 = script.pages[0].panels[1]
        assert panel2.number == 2
        assert "Close-up of hero" in panel2.description
        assert len(panel2.dialogue) == 1
        assert panel2.dialogue[0].character == "HERO"
        assert panel2.dialogue[0].text == "I will save the day!"
        
        # Check Panel 3
        panel3 = script.pages[0].panels[2]
        assert panel3.number == 3
        assert len(panel3.sound_effects) == 1
        assert panel3.sound_effects[0].text == "BOOM!"
    
    def test_parse_multi_page_script(self):
        """Test parsing script with multiple pages."""
        script_content = """
PAGE ONE

Panel 1
First page, first panel.

Panel 2
First page, second panel.

PAGE TWO

Panel 1
Second page, first panel.
"""
        parser = ScriptParser()
        script = parser.parse_content(script_content)
        
        assert len(script.pages) == 2
        assert len(script.pages[0].panels) == 2
        assert len(script.pages[1].panels) == 1
    
    def test_parse_dialogue_types(self):
        """Test parsing different dialogue types."""
        script_content = """
PAGE ONE

Panel 1
Test panel.
CHARACTER (balloon): Normal speech.
CHARACTER (thought): Inner thoughts.
CHARACTER (whisper): Quiet words.
CHARACTER (shout): LOUD WORDS!
"""
        parser = ScriptParser()
        script = parser.parse_content(script_content)
        
        panel = script.pages[0].panels[0]
        assert len(panel.dialogue) == 4
        
        # Check different dialogue types
        assert panel.dialogue[0].text == "Normal speech."
        assert panel.dialogue[1].text == "Inner thoughts."
        assert panel.dialogue[1].emotion == "thoughtful"
        assert panel.dialogue[2].text == "Quiet words."
        assert panel.dialogue[3].text == "LOUD WORDS!"
    
    def test_parse_multiple_captions(self):
        """Test parsing multiple captions."""
        script_content = """
PAGE ONE

Panel 1
Test panel.
CAPTION: First caption.
CAPTION (NARRATION): Second caption.
CAPTION (LOCATION): Third caption.
"""
        parser = ScriptParser()
        script = parser.parse_content(script_content)
        
        panel = script.pages[0].panels[0]
        assert len(panel.captions) == 3
        assert panel.captions[0].text == "First caption."
        assert panel.captions[1].text == "Second caption."
        assert panel.captions[2].text == "Third caption."
    
    def test_parse_file_not_found(self):
        """Test parsing non-existent file."""
        parser = ScriptParser()
        with pytest.raises(FileNotFoundError):
            parser.parse_script("nonexistent.txt")
    
    def test_empty_script(self):
        """Test parsing empty script."""
        parser = ScriptParser()
        script = parser.parse_content("")
        
        assert script.title == ""
        assert len(script.pages) == 0


class TestScriptValidator:
    """Test cases for ScriptValidator class."""
    
    def test_validate_valid_format(self):
        """Test validating a valid script format."""
        script_content = """
PAGE ONE

Panel 1
Test description.

Panel 2
Another panel.
"""
        result = ScriptValidator.validate_format(script_content)
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_empty_script(self):
        """Test validating empty script."""
        result = ScriptValidator.validate_format("")
        assert not result.is_valid
        assert "empty" in str(result.errors).lower()
    
    def test_validate_no_pages(self):
        """Test validating script with no pages."""
        script_content = """
Panel 1
Test description.
"""
        result = ScriptValidator.validate_format(script_content)
        assert not result.is_valid
        assert "PAGE" in str(result.errors)
    
    def test_validate_no_panels(self):
        """Test validating script with no panels."""
        script_content = """
PAGE ONE
Some text here.
"""
        result = ScriptValidator.validate_format(script_content)
        assert not result.is_valid
        assert "Panel" in str(result.errors)
    
    def test_validate_dense_script_warning(self):
        """Test warning for too many panels per page."""
        script_content = "PAGE ONE\n"
        for i in range(1, 11):
            script_content += f"Panel {i}\nDescription.\n"
            
        result = ScriptValidator.validate_format(script_content)
        assert result.is_valid
        assert len(result.warnings) > 0
        assert "dense" in str(result.warnings).lower()
    
    def test_validate_parsed_script(self):
        """Test validating a parsed script object."""
        script = ComicScript(title="Test")
        from src.models import Page, Panel
        
        page = Page(number=1)
        panel = Panel(number=1, description="Test panel description")
        page.add_panel(panel)
        script.add_page(page)
        
        result = ScriptValidator.validate_script(script)
        assert result.is_valid
    
    def test_validate_script_missing_description(self):
        """Test warning for missing panel description."""
        script = ComicScript(title="Test")
        from src.models import Page, Panel
        
        page = Page(number=1)
        panel = Panel(number=1, description="Short")  # Too short
        page.add_panel(panel)
        script.add_page(page)
        
        result = ScriptValidator.validate_script(script)
        assert result.is_valid  # Still valid, just has warnings
        assert len(result.warnings) > 0
        assert "too short" in str(result.warnings).lower()


class TestRedCometParsing:
    """Test parsing the red_comet.txt example file."""
    
    def test_parse_red_comet_structure(self):
        """Test parsing red_comet.txt structure."""
        parser = ScriptParser()
        script = parser.parse_script("red_comet.txt")
        
        # Check title
        assert script.title == "Red Comet of the Belt"
        
        # Check pages
        assert len(script.pages) == 2
        
        # Check Page 1
        page1 = script.pages[0]
        assert page1.number == 1
        assert len(page1.panels) == 6
        
        # Check Page 2
        page2 = script.pages[1]
        assert page2.number == 2
        assert len(page2.panels) == 6
        
        # Total panels
        assert script.metadata["total_panels"] == 12
    
    def test_parse_red_comet_panel1(self):
        """Test parsing specific panel from red_comet.txt."""
        parser = ScriptParser()
        script = parser.parse_script("red_comet.txt")
        
        panel1 = script.pages[0].panels[0]
        
        # Check description
        assert "sleek, crimson Soviet starfighter" in panel1.description
        assert "asteroids" in panel1.description
        
        # Check captions
        assert len(panel1.captions) == 2
        assert "23rd Century" in panel1.captions[0].text
        assert "Alexei Volkov" in panel1.captions[1].text
    
    def test_parse_red_comet_dialogue(self):
        """Test parsing dialogue from red_comet.txt."""
        parser = ScriptParser()
        script = parser.parse_script("red_comet.txt")
        
        # Panel 2 has thought dialogue
        panel2 = script.pages[0].panels[1]
        assert len(panel2.dialogue) == 1
        assert panel2.dialogue[0].character == "VOLKOV"
        assert "Too quiet" in panel2.dialogue[0].text
        assert panel2.dialogue[0].emotion == "thoughtful"
        
        # Panel 3 has balloon dialogue
        panel3 = script.pages[0].panels[2]
        assert len(panel3.dialogue) == 1
        assert panel3.dialogue[0].character == "VOLKOV"
        assert "Чёрт" in panel3.dialogue[0].text or "Damn" in panel3.dialogue[0].text
    
    def test_parse_red_comet_sfx(self):
        """Test parsing sound effects from red_comet.txt."""
        parser = ScriptParser()
        script = parser.parse_script("red_comet.txt")
        
        # Panel 6 of Page 1 has SFX
        panel6 = script.pages[0].panels[5]
        assert len(panel6.sound_effects) == 1
        assert "KRA-KOOM" in panel6.sound_effects[0].text
        
        # Page 2 has multiple SFX
        page2_panel1 = script.pages[1].panels[0]
        assert len(page2_panel1.sound_effects) == 1
        assert "VROOOOM" in page2_panel1.sound_effects[0].text
    
    def test_validate_red_comet(self):
        """Test validating red_comet.txt."""
        # First validate the file
        result = ScriptValidator.validate_file("red_comet.txt")
        assert result.is_valid
        
        # Parse and validate the script
        parser = ScriptParser()
        script = parser.parse_script("red_comet.txt")
        
        result = ScriptValidator.validate_script(script)
        assert result.is_valid
        
        # Check that all characters are tracked
        assert "VOLKOV" in script.metadata["characters"]