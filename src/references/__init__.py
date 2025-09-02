"""Reference system for comic book generation.

This module provides reference management for characters, locations, objects,
and style guides to ensure visual consistency across comic pages.
"""

from .models import (
    BaseReference,
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
    create_reference_from_dict,
)
from .storage import (
    ReferenceStorage,
    ReferenceStorageError,
    ReferenceNotFoundError,
)
from .generators import (
    BaseReferenceGenerator,
    CharacterReferenceGenerator,
    LocationReferenceGenerator,
    ObjectReferenceGenerator,
    StyleGuideGenerator,
    GenerationConfig,
)

__all__ = [
    # Models
    "BaseReference",
    "CharacterReference", 
    "LocationReference",
    "ObjectReference",
    "StyleGuide",
    "create_reference_from_dict",
    # Storage
    "ReferenceStorage",
    "ReferenceStorageError",
    "ReferenceNotFoundError",
    # Generators
    "BaseReferenceGenerator",
    "CharacterReferenceGenerator",
    "LocationReferenceGenerator",
    "ObjectReferenceGenerator",
    "StyleGuideGenerator",
    "GenerationConfig",
]