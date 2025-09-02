# Reference Image System - Technical Architecture

## System Overview

The Reference Image System provides consistent visual references for characters, locations, and objects across comic generation. It integrates with the existing page generation pipeline to ensure visual consistency and quality.

## Core Components

### 1. Reference Manager (`src/references/`)

```
src/references/
├── __init__.py
├── manager.py           # Main reference management
├── models.py           # Reference data models
├── generators.py       # Reference image generation
├── storage.py          # File storage and retrieval
└── validators.py       # Reference validation
```

#### Reference Manager (`manager.py`)
- Central interface for all reference operations
- Handles CRUD operations for references
- Manages reference-to-generation mapping
- Provides reference lookup and caching

#### Reference Models (`models.py`)
```python
@dataclass
class CharacterReference:
    name: str
    description: str
    poses: List[str]
    expressions: List[str]
    outfits: List[str]
    images: Dict[str, bytes]  # pose/expression -> image_data
    style_notes: str
    created_at: datetime
    updated_at: datetime

@dataclass
class LocationReference:
    name: str
    description: str
    angles: List[str]
    lighting_conditions: List[str]
    time_of_day: List[str]
    images: Dict[str, bytes]  # angle/lighting -> image_data
    style_notes: str

@dataclass
class ObjectReference:
    name: str
    description: str
    views: List[str]
    states: List[str]  # new, aged, broken, etc.
    images: Dict[str, bytes]
    style_notes: str

@dataclass
class StyleGuide:
    name: str
    art_style: str
    color_palette: List[str]
    line_style: str
    lighting_style: str
    typography: str
    reference_image: bytes
```

### 2. Reference Generators (`generators.py`)

#### Character Generator
```python
class CharacterReferenceGenerator:
    async def generate_character_sheet(
        self,
        name: str,
        base_description: str,
        poses: List[str],
        expressions: List[str]
    ) -> CharacterReference
    
    async def generate_character_pose(
        self,
        character: CharacterReference,
        pose: str,
        expression: str = "neutral"
    ) -> bytes
```

#### Location Generator
```python
class LocationReferenceGenerator:
    async def generate_location_views(
        self,
        name: str,
        description: str,
        angles: List[str],
        lighting: List[str]
    ) -> LocationReference
```

### 3. Storage System (`storage.py`)

```python
class ReferenceStorage:
    def __init__(self, base_path: str = "references/"):
        self.base_path = Path(base_path)
        self.characters_path = self.base_path / "characters"
        self.locations_path = self.base_path / "locations"
        self.objects_path = self.base_path / "objects"
        self.styles_path = self.base_path / "styles"
    
    def save_reference(self, ref_type: str, reference: BaseReference)
    def load_reference(self, ref_type: str, name: str) -> BaseReference
    def list_references(self, ref_type: str) -> List[str]
    def delete_reference(self, ref_type: str, name: str)
```

## Integration Points

### 1. Page Generator Integration

#### Modified PageGenerator (`src/generator/page_generator.py`)
```python
class PageGenerator:
    def __init__(
        self,
        gemini_client,
        reference_manager: ReferenceManager,
        debug_dir=None
    ):
        self.reference_manager = reference_manager
    
    async def generate_page(
        self,
        page: Page,
        previous_pages: Optional[List[Image.Image]] = None,
        style_context: Optional[Dict[str, Any]] = None
    ) -> bytes:
        # Extract referenced entities
        referenced_chars = self._extract_character_references(page)
        referenced_locations = self._extract_location_references(page)
        
        # Load reference images
        char_refs = await self.reference_manager.get_character_images(referenced_chars)
        location_refs = await self.reference_manager.get_location_images(referenced_locations)
        
        # Build enhanced prompt with references
        prompt = self._build_page_prompt_with_references(
            page, char_refs, location_refs
        )
        
        # Generate with reference context
        return await self._generate_with_references(prompt, char_refs, location_refs)
```

### 2. CLI Integration

#### New CLI Commands (`src/cli.py`)
```python
@cli.group()
def reference():
    """Reference management commands."""
    pass

@reference.command()
def create_character(name: str, description: str, poses: List[str]):
    """Create character reference."""
    
@reference.command()  
def create_location(name: str, description: str, angles: List[str]):
    """Create location reference."""

@reference.command()
def list_references(ref_type: str = None):
    """List available references."""

@reference.command()
def update_reference(ref_type: str, name: str, **kwargs):
    """Update existing reference."""
```

## Data Flow

### Reference Creation Flow
1. User requests reference creation via CLI
2. ReferenceGenerator creates initial images using Gemini
3. ReferenceStorage saves images and metadata to disk
4. ReferenceManager indexes the new reference

### Comic Generation Flow
1. Script parser extracts character/location names
2. ReferenceManager looks up matching references
3. PageGenerator includes reference images in Gemini context
4. Enhanced prompt generated with reference descriptions
5. Gemini generates page using reference consistency

## Storage Structure

```
references/
├── characters/
│   ├── alex.json              # Metadata
│   ├── alex_standing.png      # Pose images
│   ├── alex_surprised.png
│   └── alex_determined.png
├── locations/
│   ├── enchanted_forest.json  # Metadata
│   ├── forest_wide.png        # View images
│   ├── forest_closeup.png
│   └── forest_altar.png
├── objects/
│   ├── ancient_map.json
│   ├── map_closed.png
│   └── map_open.png
└── styles/
    ├── fantasy_adventure.json
    └── fantasy_style_guide.png
```

### Reference JSON Format
```json
{
  "name": "Alex the Adventurer",
  "type": "character",
  "description": "teenage hero with brown hair, brave expression",
  "poses": ["standing", "pointing", "surprised", "determined"],
  "expressions": ["neutral", "happy", "surprised", "determined"],
  "images": {
    "standing_neutral": "alex_standing_neutral.png",
    "pointing_determined": "alex_pointing_determined.png"
  },
  "style_notes": "consistent brown hair, green adventurer outfit",
  "created_at": "2025-09-02T10:30:00Z",
  "updated_at": "2025-09-02T10:30:00Z"
}
```

## Performance Considerations

### Caching Strategy
- In-memory cache for frequently used references
- LRU eviction for memory management
- Disk cache for generated variations

### Optimization
- Lazy loading of reference images
- Batch generation of character poses
- Reference image compression
- Parallel reference generation

## Error Handling

### Reference Not Found
- Graceful degradation to text-only descriptions
- Logging of missing references
- Suggestion of similar available references

### Generation Failures
- Retry logic with exponential backoff
- Fallback to simpler reference descriptions
- Error reporting and logging

## Security Considerations

### Input Validation
- Sanitize reference names and descriptions
- Validate image formats and sizes
- Check for malicious content in uploads

### Storage Security
- Secure file permissions on reference directory
- Input validation for file paths
- Size limits on reference images

## Extension Points

### Custom Reference Types
```python
class CustomReference(BaseReference):
    def __init__(self, ref_type: str, **kwargs):
        super().__init__(**kwargs)
        self.ref_type = ref_type

# Register custom type
reference_manager.register_type("weapon", CustomReference)
```

### Reference Plugins
```python
class ReferencePlugin:
    def process_reference(self, reference: BaseReference) -> BaseReference:
        # Custom processing logic
        pass

# Plugin registration
reference_manager.add_plugin(MyCustomPlugin())
```

## Testing Strategy

### Unit Tests
- Reference CRUD operations
- Image generation and storage
- Reference lookup and matching

### Integration Tests  
- End-to-end reference creation flow
- Comic generation with references
- CLI command functionality

### Performance Tests
- Reference lookup speed
- Memory usage with large reference sets
- Concurrent access patterns