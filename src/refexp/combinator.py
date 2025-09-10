"""Combination generator for reference experiments."""

import itertools
import random
from typing import List, Optional
import logging

from .models import RefExperiment, Combination

logger = logging.getLogger(__name__)


class CombinationGenerator:
    """Generate prompt combinations from experiment templates."""
    
    def __init__(self, max_combinations: int = 10000):
        """Initialize combination generator.
        
        Args:
            max_combinations: Maximum allowed combinations for safety
        """
        self.max_combinations = max_combinations
    
    def generate_combinations(
        self,
        experiment: RefExperiment,
        limit: Optional[int] = None,
        seed: Optional[int] = None,
        mode: str = 'random'
    ) -> List[Combination]:
        """Generate combinations from experiment.
        
        Args:
            experiment: RefExperiment object
            limit: Maximum number of combinations to generate
            seed: Random seed for reproducible results
            mode: 'all', 'random', or 'first'
            
        Returns:
            List of Combination objects
        """
        # Check for seed in experiment settings
        if seed is None and 'seed' in experiment.settings:
            seed = experiment.settings['seed']
        
        # Check for iterations in experiment settings
        if limit is None and 'iterations' in experiment.settings:
            limit = experiment.settings['iterations']
        
        # Determine mode
        if limit == 'all' or mode == 'all':
            return self.generate_all(experiment)
        
        # Convert limit to int
        if isinstance(limit, str):
            try:
                limit = int(limit)
            except ValueError:
                logger.warning(f"Invalid limit '{limit}', using default 10")
                limit = 10
        
        limit = limit or 10
        
        if mode == 'random':
            return self.generate_random(experiment, limit, seed)
        elif mode == 'first':
            return self.generate_first(experiment, limit)
        else:
            return self.generate_random(experiment, limit, seed)
    
    def generate_all(self, experiment: RefExperiment) -> List[Combination]:
        """Generate all possible combinations.
        
        Args:
            experiment: RefExperiment object
            
        Returns:
            List of all possible combinations
        """
        total = experiment.get_total_combinations()
        
        if total > self.max_combinations:
            raise ValueError(
                f"Total combinations ({total}) exceeds maximum allowed ({self.max_combinations}). "
                f"Use random sampling instead."
            )
        
        logger.info(f"Generating all {total} combinations")
        
        # Get all variable names and their values
        var_names = list(experiment.variables.keys())
        var_values = [experiment.variables[name] for name in var_names]
        
        # Generate cartesian product
        combinations = []
        for i, values in enumerate(itertools.product(*var_values)):
            # Create variable mapping
            var_map = dict(zip(var_names, values))
            
            # Generate prompt
            prompt = self._substitute_variables(experiment.prompt_template, var_map)
            
            # Create combination
            combo = Combination(
                id=i + 1,
                prompt=prompt,
                variables=var_map,
                hash=""  # Will be generated in __post_init__
            )
            combinations.append(combo)
        
        logger.info(f"Generated {len(combinations)} combinations")
        return combinations
    
    def generate_random(
        self,
        experiment: RefExperiment,
        count: int,
        seed: Optional[int] = None
    ) -> List[Combination]:
        """Generate random combinations.
        
        Args:
            experiment: RefExperiment object
            count: Number of combinations to generate
            seed: Random seed for reproducibility
            
        Returns:
            List of random combinations
        """
        if seed is not None:
            random.seed(seed)
            logger.info(f"Using random seed: {seed}")
        
        total = experiment.get_total_combinations()
        
        if count >= total:
            logger.info(f"Requested {count} combinations, but only {total} possible. Generating all.")
            return self.generate_all(experiment)
        
        logger.info(f"Generating {count} random combinations from {total} possible")
        
        # Generate unique combinations
        seen_hashes = set()
        combinations = []
        attempts = 0
        max_attempts = count * 10  # Prevent infinite loop
        
        while len(combinations) < count and attempts < max_attempts:
            attempts += 1
            
            # Generate random variable values
            var_map = {}
            for name, values in experiment.variables.items():
                var_map[name] = random.choice(values)
            
            # Generate prompt
            prompt = self._substitute_variables(experiment.prompt_template, var_map)
            
            # Create combination
            combo = Combination(
                id=len(combinations) + 1,
                prompt=prompt,
                variables=var_map,
                hash=""  # Will be generated in __post_init__
            )
            
            # Check for duplicates
            if combo.hash not in seen_hashes:
                seen_hashes.add(combo.hash)
                combinations.append(combo)
        
        if len(combinations) < count:
            logger.warning(
                f"Could only generate {len(combinations)} unique combinations "
                f"(requested {count})"
            )
        
        return combinations
    
    def generate_first(self, experiment: RefExperiment, count: int) -> List[Combination]:
        """Generate first N combinations in order.
        
        Args:
            experiment: RefExperiment object
            count: Number of combinations to generate
            
        Returns:
            List of first N combinations
        """
        all_combos = self.generate_all(experiment)
        return all_combos[:count]
    
    def _substitute_variables(self, template: str, variables: dict) -> str:
        """Substitute variables in template.
        
        Args:
            template: Template string with {variable} placeholders
            variables: Dictionary of variable values
            
        Returns:
            String with substituted values
        """
        result = template
        for name, value in variables.items():
            placeholder = f"{{{name}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def estimate_time(
        self,
        count: int,
        seconds_per_image: float = 5.0
    ) -> float:
        """Estimate time to generate images.
        
        Args:
            count: Number of images to generate
            seconds_per_image: Estimated seconds per image
            
        Returns:
            Estimated time in seconds
        """
        return count * seconds_per_image