"""Tests for reference experiment models."""

import pytest
from datetime import datetime
from src.refexp.models import (
    RefExperiment,
    Combination,
    GeneratedImage,
    ExperimentSession,
    RefExpValidationError
)


class TestRefExperiment:
    """Test RefExperiment model."""
    
    def test_valid_experiment(self):
        """Test creating a valid experiment."""
        exp = RefExperiment(
            name="Test Experiment",
            prompt_template="Create a {style} image of a {subject}",
            variables={
                "style": ["realistic", "cartoon"],
                "subject": ["cat", "dog"]
            },
            source_file="test.yaml"
        )
        
        assert exp.name == "Test Experiment"
        assert exp.get_total_combinations() == 4
        assert exp.validate_template() == []
    
    def test_undefined_variables(self):
        """Test detection of undefined variables."""
        exp = RefExperiment(
            name="Test",
            prompt_template="Create a {style} image of a {subject} with {color}",
            variables={
                "style": ["realistic"],
                "subject": ["cat"]
            },
            source_file="test.yaml"
        )
        
        undefined = exp.validate_template()
        assert "color" in undefined
    
    def test_invalid_experiment(self):
        """Test validation errors."""
        with pytest.raises(RefExpValidationError):
            RefExperiment(
                name="",  # Empty name
                prompt_template="test",
                variables={"var": ["val"]},
                source_file="test.yaml"
            )


class TestCombination:
    """Test Combination model."""
    
    def test_combination_creation(self):
        """Test creating a combination."""
        combo = Combination(
            id=1,
            prompt="Create a realistic image of a cat",
            variables={"style": "realistic", "subject": "cat"},
            hash=""
        )
        
        assert combo.id == 1
        assert combo.prompt == "Create a realistic image of a cat"
        assert combo.hash != ""  # Hash should be generated
    
    def test_filename_suffix(self):
        """Test filename suffix generation."""
        combo = Combination(
            id=1,
            prompt="test",
            variables={
                "style": "realistic",
                "subject": "cat with spaces",
                "color": "red/blue"
            },
            hash="test"
        )
        
        suffix = combo.get_filename_suffix()
        assert "realistic" in suffix
        assert "cat_with_spaces" in suffix
        assert "/" not in suffix  # Special chars should be replaced


class TestGeneratedImage:
    """Test GeneratedImage model."""
    
    def test_generated_image(self):
        """Test creating a generated image."""
        combo = Combination(
            id=1,
            prompt="test",
            variables={"var": "val"},
            hash="test"
        )
        
        image = GeneratedImage(
            combination=combo,
            image_data=b"fake_image_data",
            filepath="/path/to/image.png",
            timestamp=datetime.now(),
            experiment_name="Test Experiment"
        )
        
        assert image.combination == combo
        assert image.filepath == "/path/to/image.png"
        assert image.model_used == "gemini-2.5-flash-image-preview"
    
    def test_relative_path(self):
        """Test getting relative path."""
        combo = Combination(id=1, prompt="test", variables={}, hash="test")
        image = GeneratedImage(
            combination=combo,
            image_data=b"data",
            filepath="/project/output/image.png",
            timestamp=datetime.now()
        )
        
        rel_path = image.get_relative_path("/project")
        assert rel_path == "output/image.png"


class TestExperimentSession:
    """Test ExperimentSession model."""
    
    def test_session_creation(self):
        """Test creating an experiment session."""
        exp = RefExperiment(
            name="Test",
            prompt_template="test {var}",
            variables={"var": ["a", "b"]},
            source_file="test.yaml"
        )
        
        session = ExperimentSession(
            experiment=exp,
            generated_images=[],
            start_time=datetime.now()
        )
        
        assert session.experiment == exp
        assert session.total_combinations == 2
        assert session.session_id != ""
    
    def test_session_completion(self):
        """Test marking session as complete."""
        exp = RefExperiment(
            name="Test",
            prompt_template="test",
            variables={"var": ["a"]},
            source_file="test.yaml"
        )
        
        session = ExperimentSession(
            experiment=exp,
            generated_images=[],
            start_time=datetime.now()
        )
        
        session.mark_complete()
        assert session.end_time is not None
        assert session.get_duration() > 0
    
    def test_session_errors(self):
        """Test adding errors to session."""
        exp = RefExperiment(
            name="Test",
            prompt_template="test",
            variables={"var": ["a"]},
            source_file="test.yaml"
        )
        
        session = ExperimentSession(
            experiment=exp,
            generated_images=[],
            start_time=datetime.now()
        )
        
        session.add_error("Test error")
        assert session.failed_count == 1
        assert len(session.errors) == 1
        assert "Test error" in session.errors[0]