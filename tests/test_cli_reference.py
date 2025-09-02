"""Unit tests for reference CLI commands."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from click.testing import CliRunner
import tempfile
import shutil
from pathlib import Path

from src.cli_reference import (
    reference,
    create_character,
    create_location,
    create_object,
    create_style,
    list as list_cmd,
    update,
    delete,
    cleanup
)
from src.references.models import (
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide
)


class TestReferenceCLI:
    """Test reference CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create CLI test runner."""
        return CliRunner()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory."""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)
    
    def test_reference_group_help(self, runner):
        """Test reference group help."""
        result = runner.invoke(reference, ['--help'])
        assert result.exit_code == 0
        assert 'Manage reference images' in result.output
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_create_character_no_generation(self, mock_storage, mock_manager, runner, temp_dir):
        """Test creating character without generation."""
        # Setup mocks
        mock_char = CharacterReference(
            name="TestHero",
            description="A test hero",
            poses=["standing"],
            expressions=["neutral"]
        )
        mock_manager.return_value.create_reference.return_value = mock_char
        
        # Run command
        result = runner.invoke(create_character, [
            '--name', 'TestHero',
            '--description', 'A test hero',
            '--output', temp_dir,
            '--no-generate'
        ])
        
        # Verify
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert 'Creating Character Reference' in result.output
        assert 'TestHero' in result.output
        mock_manager.return_value.create_reference.assert_called_once()
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    @patch('src.cli_reference.GeminiClient')
    @patch('src.cli_reference.ConfigLoader')
    def test_create_character_with_generation(
        self, mock_config, mock_gemini, mock_storage, mock_manager, runner, temp_dir
    ):
        """Test creating character with image generation."""
        # Setup mocks
        mock_config.return_value.get.return_value = 'test-api-key'
        mock_char = CharacterReference(
            name="TestHero",
            description="A test hero",
            poses=["standing", "running"],
            expressions=["happy", "sad"],
            images={"standing_happy": "img1.png", "running_sad": "img2.png"}
        )
        mock_manager.return_value.create_reference.return_value = mock_char
        mock_manager.return_value.generate_character = AsyncMock(return_value=mock_char)
        
        # Run command
        result = runner.invoke(create_character, [
            '--name', 'TestHero',
            '--description', 'A test hero',
            '--poses', 'standing',
            '--poses', 'running',
            '--expressions', 'happy',
            '--expressions', 'sad',
            '--output', temp_dir,
            '--generate'
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Generated 2 images' in result.output
        mock_manager.return_value.generate_character.assert_called_once()
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_create_location(self, mock_storage, mock_manager, runner, temp_dir):
        """Test creating location reference."""
        # Setup mocks
        mock_location = LocationReference(
            name="TestForest",
            description="A mystical forest",
            location_type="exterior",
            angles=["wide-shot"],
            lighting_conditions=["daylight"]
        )
        mock_manager.return_value.create_reference.return_value = mock_location
        
        # Run command
        result = runner.invoke(create_location, [
            '--name', 'TestForest',
            '--description', 'A mystical forest',
            '--type', 'exterior',
            '--output', temp_dir,
            '--no-generate'
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Creating Location Reference' in result.output
        assert 'TestForest' in result.output
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_create_object(self, mock_storage, mock_manager, runner, temp_dir):
        """Test creating object reference."""
        # Setup mocks
        mock_object = ObjectReference(
            name="TestSword",
            description="A magic sword",
            views=["front"],
            states=["normal"]
        )
        mock_object.category = "weapon"  # Add category as attribute
        mock_manager.return_value.create_reference.return_value = mock_object
        
        # Run command
        result = runner.invoke(create_object, [
            '--name', 'TestSword',
            '--description', 'A magic sword',
            '--category', 'weapon',
            '--output', temp_dir,
            '--no-generate'
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Creating Object Reference' in result.output
        assert 'TestSword' in result.output
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_create_style(self, mock_storage, mock_manager, runner, temp_dir):
        """Test creating style guide."""
        # Setup mocks
        mock_style = StyleGuide(
            name="TestStyle",
            description="A test style",
            art_style="comic-book",
            color_palette=["#FF0000", "#00FF00"],
            line_style="bold"
        )
        mock_manager.return_value.create_reference.return_value = mock_style
        
        # Run command - colors need quotes in shell but not in CliRunner
        result = runner.invoke(create_style, [
            '--name', 'TestStyle',
            '--description', 'A test style',
            '--art-style', 'comic-book',
            '--colors', '#FF0000',
            '--colors', '#00FF00',
            '--line-style', 'bold',
            '--output', temp_dir
        ])
        
        # Verify
        if result.exit_code != 0:
            print(f"Exit code: {result.exit_code}")
            print(f"Output: {result.output}")
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert 'Creating Style Guide' in result.output
        assert 'TestStyle' in result.output
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_list_references(self, mock_storage, mock_manager, runner, temp_dir):
        """Test listing references."""
        # Setup mocks
        mock_manager.return_value.list_references.return_value = {
            'character': ['Hero1', 'Hero2'],
            'location': ['Forest'],
            'object': [],
            'styleguide': ['ComicStyle']
        }
        
        # Mock individual references
        mock_char = CharacterReference(name="Hero1", description="A hero")
        mock_manager.return_value.get_reference.return_value = mock_char
        
        # Run command
        result = runner.invoke(list_cmd, [
            '--storage', temp_dir
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Character References' in result.output or 'Hero1' in result.output
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_list_references_empty(self, mock_storage, mock_manager, runner, temp_dir):
        """Test listing when no references exist."""
        # Setup mocks
        mock_manager.return_value.list_references.return_value = {
            'character': [],
            'location': [],
            'object': [],
            'styleguide': []
        }
        
        # Run command
        result = runner.invoke(list_cmd, [
            '--storage', temp_dir
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'No references found' in result.output
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_update_reference(self, mock_storage, mock_manager, runner, temp_dir):
        """Test updating a reference."""
        # Setup mocks
        mock_char = CharacterReference(
            name="Hero",
            description="Original description",
            tags=["tag1"]
        )
        mock_manager.return_value.get_reference.return_value = mock_char
        mock_manager.return_value.update_reference.return_value = mock_char
        
        # Run command
        result = runner.invoke(update, [
            'character',
            'Hero',
            '--description', 'New description',
            '--add-tag', 'tag2',
            '--storage', temp_dir
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Updated character: Hero' in result.output
        mock_manager.return_value.update_reference.assert_called_once()
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_update_reference_not_found(self, mock_storage, mock_manager, runner, temp_dir):
        """Test updating non-existent reference."""
        # Setup mocks
        mock_manager.return_value.get_reference.return_value = None
        
        # Run command
        result = runner.invoke(update, [
            'character',
            'NonExistent',
            '--description', 'New description',
            '--storage', temp_dir
        ])
        
        # Verify
        assert result.exit_code != 0
        assert 'Reference not found' in result.output
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_delete_reference_with_force(self, mock_storage, mock_manager, runner, temp_dir):
        """Test deleting a reference with force flag."""
        # Setup mocks
        mock_char = CharacterReference(name="Hero", description="A hero")
        mock_manager.return_value.get_reference.return_value = mock_char
        
        # Run command
        result = runner.invoke(delete, [
            'character',
            'Hero',
            '--storage', temp_dir,
            '--force'
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Deleted character: Hero' in result.output
        mock_manager.return_value.delete_reference.assert_called_once_with('character', 'Hero')
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    @patch('src.cli_reference.Confirm')
    def test_delete_reference_with_confirmation(
        self, mock_confirm, mock_storage, mock_manager, runner, temp_dir
    ):
        """Test deleting a reference with confirmation."""
        # Setup mocks
        mock_char = CharacterReference(name="Hero", description="A hero")
        mock_manager.return_value.get_reference.return_value = mock_char
        mock_confirm.ask.return_value = True
        
        # Run command
        result = runner.invoke(delete, [
            'character',
            'Hero',
            '--storage', temp_dir
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Deleted character: Hero' in result.output
        mock_confirm.ask.assert_called_once()
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    @patch('src.cli_reference.Confirm')
    def test_delete_reference_cancelled(
        self, mock_confirm, mock_storage, mock_manager, runner, temp_dir
    ):
        """Test cancelling reference deletion."""
        # Setup mocks
        mock_char = CharacterReference(name="Hero", description="A hero")
        mock_manager.return_value.get_reference.return_value = mock_char
        mock_confirm.ask.return_value = False
        
        # Run command
        result = runner.invoke(delete, [
            'character',
            'Hero',
            '--storage', temp_dir
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Deletion cancelled' in result.output
        mock_manager.return_value.delete_reference.assert_not_called()
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_cleanup_references(self, mock_storage, mock_manager, runner, temp_dir):
        """Test cleaning up unused references."""
        # Setup mocks
        mock_manager.return_value.cleanup_unused_references.return_value = [
            ('character', 'OldHero'),
            ('location', 'OldForest')
        ]
        
        # Run command
        result = runner.invoke(cleanup, [
            '--storage', temp_dir,
            '--days', '30'
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'Deleted 2 unused references' in result.output
        mock_manager.return_value.cleanup_unused_references.assert_called_once_with(days_unused=30)
    
    @patch('src.cli_reference.ReferenceManager')
    @patch('src.cli_reference.ReferenceStorage')
    def test_cleanup_references_dry_run(self, mock_storage, mock_manager, runner, temp_dir):
        """Test cleanup dry run."""
        # Setup mocks
        import datetime
        old_date = datetime.datetime.now() - datetime.timedelta(days=40)
        
        mock_manager.return_value.list_references.return_value = {
            'character': ['OldHero'],
            'location': ['OldForest']
        }
        
        mock_char = CharacterReference(name="OldHero", description="Old hero")
        mock_char.updated_at = old_date
        mock_location = LocationReference(name="OldForest", description="Old forest")
        mock_location.updated_at = old_date
        
        mock_manager.return_value.get_reference.side_effect = [mock_char, mock_location]
        
        # Run command
        result = runner.invoke(cleanup, [
            '--storage', temp_dir,
            '--days', '30',
            '--dry-run'
        ])
        
        # Verify
        assert result.exit_code == 0
        assert 'would be deleted' in result.output
        mock_manager.return_value.cleanup_unused_references.assert_not_called()
    
    def test_create_character_with_all_options(self, runner):
        """Test create character with all options."""
        with patch('src.cli_reference.ReferenceManager') as mock_manager:
            with patch('src.cli_reference.ReferenceStorage'):
                # Setup mock
                mock_char = CharacterReference(
                    name="Hero",
                    description="A hero",
                    poses=["standing", "running"],
                    expressions=["happy", "sad"],
                    age_range="young adult",
                    physical_traits=["tall", "strong"]
                )
                mock_manager.return_value.create_reference.return_value = mock_char
                
                # Run command with all options
                result = runner.invoke(create_character, [
                    '--name', 'Hero',
                    '--description', 'A hero',
                    '--poses', 'standing',
                    '--poses', 'running',
                    '--expressions', 'happy',
                    '--expressions', 'sad',
                    '--age', 'young adult',
                    '--traits', 'tall',
                    '--traits', 'strong',
                    '--no-generate'
                ])
                
                # Verify
                assert result.exit_code == 0
                call_args = mock_manager.return_value.create_reference.call_args
                assert call_args.kwargs['age_range'] == 'young adult'
                assert 'tall' in call_args.kwargs['physical_traits']
                assert 'strong' in call_args.kwargs['physical_traits']