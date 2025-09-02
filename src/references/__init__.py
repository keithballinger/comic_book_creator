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
)

__all__ = [
    "BaseReference",
    "CharacterReference", 
    "LocationReference",
    "ObjectReference",
    "StyleGuide",
]