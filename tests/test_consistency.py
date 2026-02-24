"""Tests for consistency manager."""

import pytest
from pathlib import Path

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
    def manager(self):
        """Create a consistency manager."""
        return ConsistencyManager()

    def test_init(self, manager):
        """Test consistency manager initialization."""
        assert manager.character_refs == {}
        assert manager.style_config is None
        assert manager.panel_history == []

    def test_set_style(self, manager):
        """Test setting style configuration."""
        style = StyleConfig(
            name="test_style",
            art_style="comic book",
            color_palette="vibrant",
            line_weight="medium",
            shading="cel-shaded"
        )

        manager.set_style(style)

        assert manager.style_config == style

    def test_register_character(self, manager):
        """Test registering character reference."""
        char_ref = CharacterReference(
            name="Hero",
            appearance_description="Tall, blue costume, cape",
            personality_traits=["brave", "noble"]
        )

        manager.register_character(char_ref)

        assert "Hero" in manager.character_refs
        assert manager.character_refs["Hero"] == char_ref

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
        manager.set_style(style)

        prompt = manager.build_consistent_prompt("Action scene")

        assert "manga" in prompt
        assert "black and white" in prompt
        assert "thin" in prompt
        assert "screen-tone" in prompt
        assert "Action scene" in prompt

    def test_build_consistent_prompt_with_previous_panels(self, manager):
        """Test building prompt with previous panel context."""
        # Create a previous panel with metadata
        panel = Panel(number=1, description="Hero appears")
        gen_panel = GeneratedPanel(
            panel=panel,
            image_data=b"test_image",
            generation_time=1.0,
            metadata={'prompt': 'Hero stands on a rooftop looking over the city'}
        )

        prompt = manager.build_consistent_prompt(
            "Hero flies through the sky",
            previous_panels=[gen_panel]
        )

        assert "Hero flies through the sky" in prompt
        assert "Previous panel context" in prompt

    def test_get_reference_images_empty(self, manager):
        """Test getting reference images with no data."""
        refs = manager.get_reference_images()
        assert refs == []

    def test_get_reference_images_with_previous_panels(self, manager):
        """Test getting reference images from previous panels."""
        panel1 = Panel(number=1, description="Hero appears")
        gen_panel1 = GeneratedPanel(
            panel=panel1,
            image_data=b"panel1_image",
            generation_time=1.0
        )

        panel2 = Panel(number=2, description="Villain appears")
        gen_panel2 = GeneratedPanel(
            panel=panel2,
            image_data=b"panel2_image",
            generation_time=1.0
        )

        refs = manager.get_reference_images(
            previous_panels=[gen_panel1, gen_panel2]
        )

        # Should return image data from recent panels
        assert len(refs) == 2
        assert b"panel1_image" in refs
        assert b"panel2_image" in refs

    def test_get_reference_images_limits_to_three(self, manager):
        """Test that reference images are limited to 3 most recent."""
        panels = []
        for i in range(5):
            panel = Panel(number=i+1, description=f"Panel {i+1}")
            gen_panel = GeneratedPanel(
                panel=panel,
                image_data=f"panel_{i+1}_image".encode(),
                generation_time=1.0
            )
            panels.append(gen_panel)

        refs = manager.get_reference_images(previous_panels=panels)

        # Should only return the last 3
        assert len(refs) == 3

    def test_register_panel(self, manager):
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

    def test_register_panel_tracks_characters(self, manager):
        """Test that registering panels tracks characters."""
        panel = Panel(number=1, description="Hero appears")
        panel.characters = ["Hero", "Sidekick"]
        gen_panel = GeneratedPanel(
            panel=panel,
            image_data=b"test_image",
            generation_time=1.0
        )

        manager.register_panel(gen_panel)

        assert 'characters' in manager.visual_elements
        assert "Hero" in manager.visual_elements['characters']
        assert "Sidekick" in manager.visual_elements['characters']

    def test_get_character_context(self, manager):
        """Test getting character context."""
        char_ref = CharacterReference(
            name="Hero",
            appearance_description="Blue costume with red cape"
        )
        manager.register_character(char_ref)

        context = manager.get_character_context("Hero")
        assert context == "Blue costume with red cape"

        # Non-existent character
        assert manager.get_character_context("Unknown") is None

    def test_reset(self, manager):
        """Test resetting consistency manager."""
        # Add some data
        char_ref = CharacterReference(
            name="Hero",
            appearance_description="Blue costume"
        )
        manager.register_character(char_ref)

        style = StyleConfig(
            name="test",
            art_style="comic",
            color_palette="vibrant",
            line_weight="medium",
            shading="cel"
        )
        manager.set_style(style)

        panel = Panel(number=1, description="Test")
        gen_panel = GeneratedPanel(panel=panel, image_data=b"", generation_time=1.0)
        manager.register_panel(gen_panel)

        # Reset
        manager.reset()

        assert manager.character_refs == {}
        assert manager.style_config is None
        assert manager.panel_history == []
        assert manager.style_embeddings == {}

    def test_multiple_characters(self, manager):
        """Test registering multiple characters."""
        chars = [
            CharacterReference(name="Batman", appearance_description="Dark knight"),
            CharacterReference(name="Robin", appearance_description="Boy wonder"),
            CharacterReference(name="Joker", appearance_description="Clown villain"),
        ]

        for char in chars:
            manager.register_character(char)

        assert len(manager.character_refs) == 3
        assert manager.get_character_context("Batman") == "Dark knight"
        assert manager.get_character_context("Robin") == "Boy wonder"
        assert manager.get_character_context("Joker") == "Clown villain"
