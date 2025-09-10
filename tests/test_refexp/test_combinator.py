"""Tests for combination generator."""

import pytest
from src.refexp.combinator import CombinationGenerator
from src.refexp.models import RefExperiment


class TestCombinationGenerator:
    """Test the combination generator."""
    
    def test_generate_all_combinations(self):
        """Test generating all possible combinations."""
        exp = RefExperiment(
            name="Test",
            prompt_template="Create a {style} {subject}",
            variables={
                "style": ["realistic", "cartoon"],
                "subject": ["cat", "dog", "bird"]
            },
            source_file="test.yaml"
        )
        
        generator = CombinationGenerator()
        combinations = generator.generate_all(exp)
        
        assert len(combinations) == 6  # 2 styles * 3 subjects
        
        # Check all combinations are unique
        prompts = [c.prompt for c in combinations]
        assert len(prompts) == len(set(prompts))
        
        # Check variable substitution
        assert "realistic cat" in prompts[0] or "realistic dog" in prompts[0]
    
    def test_generate_random_combinations(self):
        """Test generating random combinations."""
        exp = RefExperiment(
            name="Test",
            prompt_template="{var1} {var2}",
            variables={
                "var1": ["a", "b", "c"],
                "var2": ["1", "2", "3"]
            },
            source_file="test.yaml"
        )
        
        generator = CombinationGenerator()
        
        # Test with seed for reproducibility
        combos1 = generator.generate_random(exp, count=3, seed=42)
        combos2 = generator.generate_random(exp, count=3, seed=42)
        
        assert len(combos1) == 3
        assert len(combos2) == 3
        
        # Same seed should produce same results
        for c1, c2 in zip(combos1, combos2):
            assert c1.prompt == c2.prompt
    
    def test_generate_first_combinations(self):
        """Test generating first N combinations."""
        exp = RefExperiment(
            name="Test",
            prompt_template="{var}",
            variables={
                "var": ["a", "b", "c", "d", "e"]
            },
            source_file="test.yaml"
        )
        
        generator = CombinationGenerator()
        combinations = generator.generate_first(exp, count=3)
        
        assert len(combinations) == 3
        assert combinations[0].prompt == "a"
        assert combinations[1].prompt == "b"
        assert combinations[2].prompt == "c"
    
    def test_generate_with_limit(self):
        """Test generate_combinations with different limits."""
        exp = RefExperiment(
            name="Test",
            prompt_template="{var}",
            variables={
                "var": ["a", "b", "c"]
            },
            source_file="test.yaml"
        )
        
        generator = CombinationGenerator()
        
        # Test with string "all"
        all_combos = generator.generate_combinations(exp, limit="all")
        assert len(all_combos) == 3
        
        # Test with number
        some_combos = generator.generate_combinations(exp, limit=2)
        assert len(some_combos) == 2
        
        # Test with invalid string
        default_combos = generator.generate_combinations(exp, limit="invalid")
        assert len(default_combos) == 3  # Should use all since only 3 total
    
    def test_max_combinations_limit(self):
        """Test that max combinations limit is enforced."""
        exp = RefExperiment(
            name="Test",
            prompt_template="{var}",
            variables={
                "var": [str(i) for i in range(100000)]  # Way too many
            },
            source_file="test.yaml"
        )
        
        generator = CombinationGenerator(max_combinations=1000)
        
        with pytest.raises(ValueError) as exc:
            generator.generate_all(exp)
        assert "exceeds maximum" in str(exc.value)
    
    def test_variable_substitution(self):
        """Test proper variable substitution in templates."""
        exp = RefExperiment(
            name="Test",
            prompt_template="The {color} {animal} jumps over the {object}.",
            variables={
                "color": ["red"],
                "animal": ["fox"],
                "object": ["fence"]
            },
            source_file="test.yaml"
        )
        
        generator = CombinationGenerator()
        combinations = generator.generate_all(exp)
        
        assert len(combinations) == 1
        assert combinations[0].prompt == "The red fox jumps over the fence."
    
    def test_unique_combinations(self):
        """Test that random generation avoids duplicates."""
        exp = RefExperiment(
            name="Test",
            prompt_template="{var1} {var2}",
            variables={
                "var1": ["a", "b"],
                "var2": ["1", "2"]
            },
            source_file="test.yaml"
        )
        
        generator = CombinationGenerator()
        # Request all 4 combinations randomly
        combinations = generator.generate_random(exp, count=4)
        
        # Should get all 4 unique combinations
        assert len(combinations) == 4
        hashes = [c.hash for c in combinations]
        assert len(hashes) == len(set(hashes))  # All unique
    
    def test_settings_override(self):
        """Test that experiment settings are used."""
        exp = RefExperiment(
            name="Test",
            prompt_template="{var}",
            variables={"var": ["a", "b", "c"]},
            source_file="test.yaml",
            settings={"seed": 123, "iterations": 2}
        )
        
        generator = CombinationGenerator()
        combinations = generator.generate_combinations(exp)
        
        assert len(combinations) == 2  # Should use iterations from settings