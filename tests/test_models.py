"""Tests for data models."""

import pytest
from datetime import datetime

from src.models import (
    Caption,
    CharacterReference,
    ComicScript,
    Dialogue,
    GeneratedPage,
    GeneratedPanel,
    Page,
    Panel,
    PanelType,
    ProcessingOptions,
    ProcessingResult,
    SoundEffect,
    StyleConfig,
    ValidationResult,
)


class TestDialogue:
    """Test cases for Dialogue model."""
    
    def test_valid_dialogue(self):
        """Test creating valid dialogue."""
        dialogue = Dialogue(character="Hero", text="I will save the day!")
        assert dialogue.character == "Hero"
        assert dialogue.text == "I will save the day!"
        assert dialogue.emotion is None
        
    def test_dialogue_with_emotion(self):
        """Test dialogue with emotion."""
        dialogue = Dialogue(character="Hero", text="No!", emotion="angry")
        assert dialogue.emotion == "angry"
        
    def test_invalid_dialogue(self):
        """Test dialogue validation."""
        with pytest.raises(ValueError, match="character"):
            Dialogue(character="", text="Hello")
        
        with pytest.raises(ValueError, match="text"):
            Dialogue(character="Hero", text="")


class TestCaption:
    """Test cases for Caption model."""
    
    def test_valid_caption(self):
        """Test creating valid caption."""
        caption = Caption(text="Meanwhile...")
        assert caption.text == "Meanwhile..."
        assert caption.position == "top"
        assert caption.style == "narration"
        
    def test_caption_with_position(self):
        """Test caption with custom position."""
        caption = Caption(text="The End", position="bottom")
        assert caption.position == "bottom"
        
    def test_invalid_caption(self):
        """Test caption validation."""
        with pytest.raises(ValueError, match="text"):
            Caption(text="")
        
        with pytest.raises(ValueError, match="position"):
            Caption(text="Test", position="invalid")


class TestSoundEffect:
    """Test cases for SoundEffect model."""
    
    def test_valid_sound_effect(self):
        """Test creating valid sound effect."""
        sfx = SoundEffect(text="BOOM!")
        assert sfx.text == "BOOM!"
        assert sfx.style == "bold"
        assert sfx.size == "large"
        
    def test_sound_effect_with_size(self):
        """Test sound effect with custom size."""
        sfx = SoundEffect(text="whoosh", size="small")
        assert sfx.size == "small"
        
    def test_invalid_sound_effect(self):
        """Test sound effect validation."""
        with pytest.raises(ValueError, match="text"):
            SoundEffect(text="")
        
        with pytest.raises(ValueError, match="size"):
            SoundEffect(text="BANG", size="gigantic")


class TestPanel:
    """Test cases for Panel model."""
    
    def test_valid_panel(self):
        """Test creating valid panel."""
        panel = Panel(number=1, description="Hero enters the scene")
        assert panel.number == 1
        assert panel.description == "Hero enters the scene"
        assert panel.panel_type == PanelType.MEDIUM
        assert panel.dialogue == []
        assert panel.captions == []
        assert panel.sound_effects == []
        
    def test_panel_type_conversion(self):
        """Test panel type string to enum conversion."""
        panel = Panel(number=1, description="Test", panel_type="wide")
        assert panel.panel_type == PanelType.WIDE
        
    def test_add_dialogue(self):
        """Test adding dialogue to panel."""
        panel = Panel(number=1, description="Test")
        panel.add_dialogue("Hero", "Hello!")
        
        assert len(panel.dialogue) == 1
        assert panel.dialogue[0].character == "Hero"
        assert "Hero" in panel.characters
        
    def test_add_caption(self):
        """Test adding caption to panel."""
        panel = Panel(number=1, description="Test")
        panel.add_caption("Meanwhile...")
        
        assert len(panel.captions) == 1
        assert panel.captions[0].text == "Meanwhile..."
        
    def test_add_sound_effect(self):
        """Test adding sound effect to panel."""
        panel = Panel(number=1, description="Test")
        panel.add_sound_effect("BOOM!")
        
        assert len(panel.sound_effects) == 1
        assert panel.sound_effects[0].text == "BOOM!"
        
    def test_invalid_panel(self):
        """Test panel validation."""
        with pytest.raises(ValueError, match="positive"):
            Panel(number=0, description="Test")
        
        with pytest.raises(ValueError, match="description"):
            Panel(number=1, description="")


class TestPage:
    """Test cases for Page model."""
    
    def test_valid_page(self):
        """Test creating valid page."""
        page = Page(number=1)
        assert page.number == 1
        assert page.panels == []
        assert page.layout == "standard"
        
    def test_add_panel(self):
        """Test adding panel to page."""
        page = Page(number=1)
        panel = Panel(number=1, description="Test")
        page.add_panel(panel)
        
        assert len(page.panels) == 1
        assert page.get_panel(1) == panel
        
    def test_get_nonexistent_panel(self):
        """Test getting non-existent panel."""
        page = Page(number=1)
        assert page.get_panel(99) is None
        
    def test_invalid_page(self):
        """Test page validation."""
        with pytest.raises(ValueError, match="positive"):
            Page(number=0)
        
        with pytest.raises(ValueError, match="layout"):
            Page(number=1, layout="invalid")


class TestComicScript:
    """Test cases for ComicScript model."""
    
    def test_valid_script(self):
        """Test creating valid script."""
        script = ComicScript(title="Test Comic")
        assert script.title == "Test Comic"
        assert script.pages == []
        assert script.metadata["total_pages"] == 0
        assert script.metadata["total_panels"] == 0
        
    def test_add_page(self):
        """Test adding page to script."""
        script = ComicScript(title="Test")
        page = Page(number=1)
        panel = Panel(number=1, description="Test")
        panel.add_dialogue("Hero", "Hello")
        page.add_panel(panel)
        script.add_page(page)
        
        assert len(script.pages) == 1
        assert script.get_page(1) == page
        assert script.metadata["total_pages"] == 1
        assert script.metadata["total_panels"] == 1
        assert "Hero" in script.metadata["characters"]
        
    def test_validate_empty_script(self):
        """Test validating empty script."""
        script = ComicScript()
        errors = script.validate()
        
        assert "title" in str(errors)
        assert "at least one page" in str(errors)
        
    def test_validate_valid_script(self):
        """Test validating valid script."""
        script = ComicScript(title="Test")
        page = Page(number=1)
        page.add_panel(Panel(number=1, description="Test"))
        script.add_page(page)
        
        errors = script.validate()
        assert errors == []


class TestCharacterReference:
    """Test cases for CharacterReference model."""
    
    def test_valid_character(self):
        """Test creating valid character reference."""
        char = CharacterReference(
            name="Hero",
            appearance_description="Tall, muscular, blue costume"
        )
        assert char.name == "Hero"
        assert "blue costume" in char.appearance_description
        
    def test_character_with_traits(self):
        """Test character with personality traits."""
        char = CharacterReference(
            name="Hero",
            appearance_description="Test",
            personality_traits=["brave", "kind"]
        )
        prompt = char.get_consistency_prompt()
        assert "brave" in prompt
        assert "kind" in prompt
        
    def test_invalid_character(self):
        """Test character validation."""
        with pytest.raises(ValueError, match="name"):
            CharacterReference(name="", appearance_description="Test")
        
        with pytest.raises(ValueError, match="appearance"):
            CharacterReference(name="Hero", appearance_description="")


class TestGeneratedPanel:
    """Test cases for GeneratedPanel model."""
    
    def test_valid_generated_panel(self):
        """Test creating valid generated panel."""
        panel = Panel(number=1, description="Test")
        gen_panel = GeneratedPanel(
            panel=panel,
            image_data=b"fake_image_data",
            generation_time=2.5
        )
        
        assert gen_panel.panel == panel
        assert gen_panel.image_data == b"fake_image_data"
        assert gen_panel.generation_time == 2.5
        assert "generated_at" in gen_panel.metadata
        
    def test_cache_key(self):
        """Test cache key generation."""
        panel = Panel(number=1, description="Test")
        gen_panel = GeneratedPanel(panel, b"data", 1.0)
        
        key = gen_panel.get_cache_key()
        assert isinstance(key, str)
        assert len(key) == 64  # SHA256 hex digest length


class TestProcessingOptions:
    """Test cases for ProcessingOptions model."""
    
    def test_default_options(self):
        """Test default processing options."""
        options = ProcessingOptions()
        assert options.page_range is None
        assert options.quality == "high"
        assert options.export_formats == ["png"]
        assert options.cache_enabled is True
        
    def test_page_range_filter(self):
        """Test page range filtering."""
        options = ProcessingOptions(page_range=[1, 3, 5])
        assert options.should_process_page(1) is True
        assert options.should_process_page(2) is False
        assert options.should_process_page(3) is True
        
    def test_invalid_quality(self):
        """Test invalid quality setting."""
        with pytest.raises(ValueError, match="Quality"):
            ProcessingOptions(quality="ultra")
        
    def test_invalid_format(self):
        """Test invalid export format."""
        with pytest.raises(ValueError, match="Export format"):
            ProcessingOptions(export_formats=["invalid"])


class TestStyleConfig:
    """Test cases for StyleConfig model."""
    
    def test_valid_style(self):
        """Test creating valid style config."""
        style = StyleConfig(
            name="Modern",
            art_style="modern comic book",
            color_palette="vibrant",
            line_weight="medium",
            shading="cel-shaded"
        )
        
        prompt = style.get_style_prompt()
        assert "modern comic book" in prompt
        assert "vibrant" in prompt
        
    def test_style_with_custom_prompts(self):
        """Test style with custom prompts."""
        style = StyleConfig(
            name="Test",
            art_style="test",
            color_palette="test",
            line_weight="test",
            shading="test",
            custom_prompts={"lighting": "dramatic"}
        )
        
        prompt = style.get_style_prompt()
        assert "lighting: dramatic" in prompt
        
    def test_invalid_style(self):
        """Test style validation."""
        with pytest.raises(ValueError, match="name"):
            StyleConfig(
                name="",
                art_style="test",
                color_palette="test",
                line_weight="test",
                shading="test"
            )


class TestValidationResult:
    """Test cases for ValidationResult model."""
    
    def test_valid_result(self):
        """Test valid validation result."""
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        
    def test_add_error(self):
        """Test adding error to result."""
        result = ValidationResult(is_valid=True)
        result.add_error("Test error")
        
        assert result.is_valid is False
        assert "Test error" in result.errors
        
    def test_add_warning(self):
        """Test adding warning to result."""
        result = ValidationResult(is_valid=True)
        result.add_warning("Test warning")
        
        assert result.is_valid is True
        assert "Test warning" in result.warnings
        
    def test_get_message(self):
        """Test getting formatted message."""
        result = ValidationResult(is_valid=True)
        assert "✓" in result.get_message()
        
        result.add_error("Error 1")
        assert "✗" in result.get_message()
        assert "Error 1" in result.get_message()


class TestRedCometModels:
    """Test models with red_comet.txt structure."""
    
    def test_red_comet_page_structure(self):
        """Test creating structure matching red_comet.txt."""
        script = ComicScript(title="The Red Comet")
        
        # Page 1 with 6 panels
        page1 = Page(number=1)
        for i in range(1, 7):
            panel = Panel(number=i, description=f"Panel {i} description")
            if i == 1:
                panel.add_caption("The year 2089...")
            page1.add_panel(panel)
        
        # Page 2 with 6 panels
        page2 = Page(number=2)
        for i in range(1, 7):
            panel = Panel(number=i, description=f"Panel {i} description")
            if i == 1:
                panel.add_dialogue("MAYA", "We're approaching the comet now")
            page2.add_panel(panel)
        
        script.add_page(page1)
        script.add_page(page2)
        
        # Validate structure
        assert script.metadata["total_pages"] == 2
        assert script.metadata["total_panels"] == 12
        assert "MAYA" in script.metadata["characters"]
        
        errors = script.validate()
        assert errors == []