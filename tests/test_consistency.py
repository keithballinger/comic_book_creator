"""Tests for consistency manager."""

import pytest
import json
from pathlib import Path
import tempfile
import shutil

from src.generator import ConsistencyManager
from src.models import (
    CharacterReference,
    GeneratedPanel,
    Panel,
    StyleConfig,
)


class TestConsistencyManager:
    """Test cases for ConsistencyManager class."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_cache_dir):
        """Create a consistency manager with temp cache."""
        return ConsistencyManager(cache_dir=temp_cache_dir)
    
    def test_init(self, manager, temp_cache_dir):
        """Test consistency manager initialization."""
        assert manager.character_refs == {}
        assert manager.style_config is None
        assert manager.panel_history == []
        assert Path(temp_cache_dir).exists()
    
    def test_load_style(self, manager, temp_cache_dir):
        """Test loading style configuration."""
        style = StyleConfig(
            name="test_style",
            art_style="comic book",
            color_palette="vibrant",
            line_weight="medium",
            shading="cel-shaded"
        )
        
        manager.load_style(style)
        
        assert manager.style_config == style
        
        # Check cache file
        style_cache = Path(temp_cache_dir) / "style_config.json"
        assert style_cache.exists()
        
        with open(style_cache) as f:
            cached_style = json.load(f)
            assert cached_style['name'] == "test_style"
            assert cached_style['art_style'] == "comic book"
    
    def test_register_character(self, manager, temp_cache_dir):
        """Test registering character reference."""
        char_ref = CharacterReference(
            name="Hero",
            appearance_description="Tall, blue costume, cape",
            personality_traits=["brave", "noble"]
        )
        
        manager.register_character(char_ref)
        
        assert "Hero" in manager.character_refs
        assert manager.character_refs["Hero"] == char_ref
        
        # Check cache file
        char_cache = Path(temp_cache_dir) / "character_Hero.json"
        assert char_cache.exists()
        
        with open(char_cache) as f:
            cached_char = json.load(f)
            assert cached_char['name'] == "Hero"
            assert "blue costume" in cached_char['appearance_description']
    
    def test_build_consistent_prompt_basic(self, manager):
        """Test building consistent prompt without style."""
        prompt = manager.build_consistent_prompt("Hero stands on rooftop")
        
        assert "Hero stands on rooftop" in prompt
    
    def test_build_consistent_prompt_with_style(self, manager):
        """Test building consistent prompt with style."""
        style = StyleConfig(
            name="manga",
            art_style="manga",
            color_palette="black and white",
            line_weight="thin",
            shading="screen-tone"
        )
        manager.load_style(style)
        
        prompt = manager.build_consistent_prompt("Action scene")
        
        assert "manga style" in prompt
        assert "black and white" in prompt
        assert "thin" in prompt
        assert "screen-tone" in prompt
        assert "Action scene" in prompt
    
    def test_build_consistent_prompt_with_characters(self, manager):
        """Test building prompt with character consistency."""
        # Register character
        char_ref = CharacterReference(
            name="Hero",
            appearance_description="Blue costume with red cape"
        )
        manager.register_character(char_ref)
        
        # Build prompt mentioning the character
        prompt = manager.build_consistent_prompt("Hero flies through the sky")
        
        assert "Hero" in prompt
        assert "Blue costume with red cape" in prompt
    
    def test_build_consistent_prompt_with_visual_elements(self, manager):
        """Test building prompt with visual elements."""
        manager.update_visual_element('lighting', 'dramatic shadows')
        manager.update_visual_element('weather', 'stormy')
        manager.update_visual_element('time_of_day', 'night')
        
        prompt = manager.build_consistent_prompt("Scene description")
        
        assert "dramatic shadows" in prompt
        assert "stormy" in prompt
        assert "night" in prompt
    
    def test_get_reference_images_empty(self, manager):
        """Test getting reference images with no data."""
        refs = manager.get_reference_images()
        assert refs == []
    
    def test_get_reference_images_with_character(self, manager):
        """Test getting reference images with character."""
        char_ref = CharacterReference(
            name="Hero",
            appearance_description="Test",
            reference_image=b"fake_image_data"
        )
        manager.register_character(char_ref)
        
        refs = manager.get_reference_images(characters=["Hero"])
        
        assert len(refs) == 1
        assert refs[0] == b"fake_image_data"
    
    def test_get_reference_images_with_previous_panels(self, manager):
        """Test getting reference images from previous panels."""
        # Create panels with characters
        panel1 = Panel(number=1, description="Hero appears")
        panel1.characters = ["Hero"]
        gen_panel1 = GeneratedPanel(
            panel=panel1,
            image_data=b"panel1_image",
            generation_time=1.0
        )
        
        panel2 = Panel(number=2, description="Villain appears")
        panel2.characters = ["Villain"]
        gen_panel2 = GeneratedPanel(
            panel=panel2,
            image_data=b"panel2_image",
            generation_time=1.0
        )
        
        refs = manager.get_reference_images(
            previous_panels=[gen_panel1, gen_panel2],
            characters=["Hero"]
        )
        
        assert len(refs) == 1
        assert refs[0] == b"panel1_image"
    
    def test_register_panel(self, manager, temp_cache_dir):
        """Test registering generated panel."""
        panel = Panel(number=1, description="Test panel")
        gen_panel = GeneratedPanel(
            panel=panel,
            image_data=b"test_image",
            generation_time=2.5
        )
        
        manager.register_panel(gen_panel)
        
        assert len(manager.panel_history) == 1
        assert manager.panel_history[0] == gen_panel
        
        # Check cache file
        panel_cache = Path(temp_cache_dir) / "panel_1.json"
        assert panel_cache.exists()
    
    def test_update_visual_element(self, manager):
        """Test updating visual elements."""
        manager.update_visual_element('lighting', 'bright')
        assert manager.visual_elements['lighting'] == 'bright'
        
        manager.update_visual_element('weather', 'sunny')
        assert manager.visual_elements['weather'] == 'sunny'
    
    def test_get_style_hash(self, manager):
        """Test getting style hash."""
        # Default hash
        assert manager.get_style_hash() == "default"
        
        # With style
        style = StyleConfig(
            name="test",
            art_style="comic",
            color_palette="vibrant",
            line_weight="medium",
            shading="cel"
        )
        manager.load_style(style)
        
        hash1 = manager.get_style_hash()
        assert hash1 != "default"
        assert len(hash1) == 32  # MD5 hash length
        
        # Same style should give same hash
        hash2 = manager.get_style_hash()
        assert hash1 == hash2
    
    def test_save_and_load_session(self, manager, temp_cache_dir):
        """Test saving and loading consistency session."""
        # Set up session data
        char_ref = CharacterReference(
            name="Hero",
            appearance_description="Blue costume",
            personality_traits=["brave"]
        )
        manager.register_character(char_ref)
        manager.update_visual_element('lighting', 'dramatic')
        manager.update_visual_element('weather', 'clear')
        
        # Save session
        manager.save_session("test_session")
        
        session_file = Path(temp_cache_dir) / "session_test_session.json"
        assert session_file.exists()
        
        # Create new manager and load session
        new_manager = ConsistencyManager(cache_dir=temp_cache_dir)
        assert new_manager.load_session("test_session")
        
        # Verify loaded data
        assert "Hero" in new_manager.character_refs
        assert new_manager.character_refs["Hero"].appearance_description == "Blue costume"
        assert new_manager.visual_elements['lighting'] == 'dramatic'
        assert new_manager.visual_elements['weather'] == 'clear'
    
    def test_load_nonexistent_session(self, manager):
        """Test loading non-existent session."""
        assert not manager.load_session("nonexistent")
    
    def test_extract_characters(self, manager):
        """Test extracting character names from description."""
        # Register characters
        manager.register_character(CharacterReference("Batman", "Dark knight"))
        manager.register_character(CharacterReference("Robin", "Boy wonder"))
        
        # Test extraction
        chars = manager._extract_characters("Batman and Robin fight crime")
        assert "Batman" in chars
        assert "Robin" in chars
        
        chars = manager._extract_characters("The Joker appears")
        assert chars == []  # Joker not registered
    
    def test_extract_visual_elements_time(self, manager):
        """Test extracting time of day from panel."""
        panel1 = Panel(number=1, description="Morning sunrise over the city")
        gen_panel1 = GeneratedPanel(panel=panel1, image_data=b"", generation_time=1.0)
        
        manager._extract_visual_elements(gen_panel1)
        assert manager.visual_elements['time_of_day'] == 'morning'
        
        panel2 = Panel(number=2, description="Night falls on Gotham")
        gen_panel2 = GeneratedPanel(panel=panel2, image_data=b"", generation_time=1.0)
        
        manager._extract_visual_elements(gen_panel2)
        assert manager.visual_elements['time_of_day'] == 'night'
    
    def test_extract_visual_elements_weather(self, manager):
        """Test extracting weather from panel."""
        panel1 = Panel(number=1, description="Heavy rain pours down")
        gen_panel1 = GeneratedPanel(panel=panel1, image_data=b"", generation_time=1.0)
        
        manager._extract_visual_elements(gen_panel1)
        assert manager.visual_elements['weather'] == 'rainy'
        
        panel2 = Panel(number=2, description="Snow covers the landscape")
        gen_panel2 = GeneratedPanel(panel=panel2, image_data=b"", generation_time=1.0)
        
        manager._extract_visual_elements(gen_panel2)
        assert manager.visual_elements['weather'] == 'snowy'
    
    def test_get_relevant_panels(self, manager):
        """Test getting relevant panels for characters."""
        # Create panels with different characters
        panel1 = Panel(number=1, description="Hero")
        panel1.characters = ["Hero", "Sidekick"]
        gen_panel1 = GeneratedPanel(panel=panel1, image_data=b"", generation_time=1.0)
        
        panel2 = Panel(number=2, description="Villain")
        panel2.characters = ["Villain"]
        gen_panel2 = GeneratedPanel(panel=panel2, image_data=b"", generation_time=1.0)
        
        panel3 = Panel(number=3, description="Hero returns")
        panel3.characters = ["Hero"]
        gen_panel3 = GeneratedPanel(panel=panel3, image_data=b"", generation_time=1.0)
        
        previous = [gen_panel1, gen_panel2, gen_panel3]
        
        # Get panels with Hero
        relevant = manager._get_relevant_panels(previous, ["Hero"])
        assert len(relevant) == 2
        assert gen_panel1 in relevant
        assert gen_panel3 in relevant
        
        # Get panels with Villain
        relevant = manager._get_relevant_panels(previous, ["Villain"])
        assert len(relevant) == 1
        assert gen_panel2 in relevant