# Reference Experiments Task Breakdown

## General Development Guidance

### **Core Principles**
- **Use Python:** Implement all components using Python with standard project layout
- **Test-Driven Development:** Write tests before implementing each task
- **Build and Test:** Use `make build` and `make test` commands consistently

### **Post-Task Checklist**
1. Update `arch_reference_experiments.md` if any architectural changes were made
2. Mark the task as complete in `tasks_reference_experiments.md`
3. Document implementation notes and architectural decisions in `tasks_reference_experiments.md`
4. Update remaining tasks if architecture changes affected dependencies
5. Ensure `make build` and `make test` run successfully with no warnings
6. Run `ruff check src/` and fix any issues
7. Commit changes with descriptive commit message following conventional commits
8. Don't include Claude as an author or coauthor

### **Code Quality Standards**
- **Testing:** Table-driven tests with subtests, >80% coverage, mock external dependencies
- **Error Handling:** Use proper exception handling with context
- **Type Hints:** Use type hints for all function signatures
- **Documentation:** Docstrings for all public functions and classes
- **Async/Await:** Proper async handling for API calls

## Task List

### Phase 1: Core Infrastructure [Priority: High]

#### Task 1.1: Create Data Models
**Status**: [ ] Pending
**Dependencies**: None
**Description**: Define core data structures for reference experiments
**Files to create**:
- `src/refexp/__init__.py`
- `src/refexp/models.py`

**Implementation**:
```python
@dataclass
class RefExperiment:
    name: str
    description: Optional[str]
    prompt_template: str
    variables: Dict[str, List[str]]
    settings: Dict[str, Any]
    image_settings: Dict[str, Any]
    source_file: str
    
@dataclass
class Combination:
    id: int
    prompt: str
    variables: Dict[str, str]
    hash: str
    
# Additional classes: GeneratedImage, ExperimentSession
```

**Tests**:
- `tests/test_refexp/test_models.py`
- Test model initialization, validation, serialization

---

#### Task 1.2: Implement YAML File Parser
**Status**: [ ] Pending
**Dependencies**: Task 1.1
**Description**: Create parser for YAML experiment files with validation
**Files to create**:
- `src/refexp/parser.py`

**Implementation**:
- Load and parse YAML files using PyYAML
- Extract prompt template, variables, and settings
- Validate YAML schema (required/optional fields)
- Ensure all template variables are defined
- Handle nested settings and image_settings
- Proper error messages for parsing failures

**Tests**:
- `tests/test_refexp/test_parser.py`
- Test valid YAML files with all fields
- Test minimal YAML with only required fields
- Test invalid schemas and malformed YAML
- Test settings override behavior

---

#### Task 1.3: Build Combination Generator
**Status**: [ ] Pending
**Dependencies**: Task 1.1
**Description**: Generate prompt combinations from parsed experiments
**Files to create**:
- `src/refexp/combinator.py`

**Implementation**:
- Generate all combinations (Cartesian product)
- Generate random combinations with seed
- Handle limits and max combinations
- Implement deduplication via hashing

**Tests**:
- `tests/test_refexp/test_combinator.py`
- Test all generation modes
- Test reproducibility with seeds
- Test limit enforcement

---

### Phase 2: Image Generation Integration [Priority: High]

#### Task 2.1: Create Image Generator Wrapper
**Status**: [ ] Pending
**Dependencies**: Task 1.1, Task 1.3
**Description**: Integrate with existing Gemini API client
**Files to create**:
- `src/refexp/generator.py`

**Implementation**:
- Wrap existing `GeminiClient.generate_image()`
- Handle batch generation with concurrency control
- Implement progress callbacks
- Add retry logic with exponential backoff

**Tests**:
- `tests/test_refexp/test_generator.py`
- Mock Gemini API calls
- Test concurrency control
- Test error handling and retries

---

#### Task 2.2: Implement Reference Tracker
**Status**: [ ] Pending
**Dependencies**: Task 2.1
**Description**: Manage reference_images.md updates
**Files to create**:
- `src/refexp/tracker.py`

**Implementation**:
- Format markdown entries
- Append to existing file
- Create backups before updates
- Handle file locking for concurrent access

**Tests**:
- `tests/test_refexp/test_tracker.py`
- Test markdown formatting
- Test file operations
- Test backup creation

---

### Phase 3: CLI Integration [Priority: High]

#### Task 3.1: Create CLI Command
**Status**: [ ] Pending
**Dependencies**: Task 2.1, Task 2.2
**Description**: Add ref-exp command to CLI
**Files to create**:
- `src/cli_refexp.py`

**Implementation**:
- Parse command arguments (iterations, seed, output, etc.)
- Integrate with Rich progress display
- Handle interrupts gracefully
- Display results summary

**Integration**:
- Update `src/cli.py` to import and add ref-exp command

**Tests**:
- `tests/test_cli_refexp.py`
- Test command parsing
- Test different iteration modes
- Test error handling

---

### Phase 4: Configuration & Rate Limiting [Priority: Medium]

#### Task 4.1: Extend Configuration System
**Status**: [ ] Pending
**Dependencies**: None
**Description**: Add reference experiment configuration
**Files to modify**:
- `src/config/loader.py`

**Implementation**:
- Add `ReferenceExperimentConfig` dataclass
- Add to main `Config` class
- Update YAML parsing
- Add environment variable overrides

**Tests**:
- Update `tests/test_config.py`
- Test new configuration loading
- Test defaults and overrides

---

#### Task 4.2: Integrate Rate Limiting
**Status**: [ ] Pending
**Dependencies**: Task 2.1
**Description**: Use existing rate limiter for API calls
**Files to modify**:
- `src/refexp/generator.py`

**Implementation**:
- Import and use `src/api/rate_limiter.py`
- Configure rate limits from config
- Handle rate limit exceptions
- Implement backoff strategy

**Tests**:
- Test rate limiting behavior
- Test backoff and retry

---

### Phase 5: Error Handling & Recovery [Priority: Medium]

#### Task 5.1: Implement Checkpoint System
**Status**: [ ] Pending
**Dependencies**: Task 2.1
**Description**: Save and resume experiment progress
**Files to create**:
- `src/refexp/checkpoint.py`

**Implementation**:
- Save progress to JSON checkpoint file
- Load and validate checkpoints
- Resume from last successful combination
- Clean up old checkpoints

**Tests**:
- `tests/test_refexp/test_checkpoint.py`
- Test save/load cycle
- Test resume functionality
- Test corruption handling

---

#### Task 5.2: Add Comprehensive Error Handling
**Status**: [ ] Pending
**Dependencies**: All Phase 1-3 tasks
**Description**: Implement proper error handling throughout
**Files to modify**:
- All refexp modules

**Implementation**:
- Define custom exception classes
- Add try-catch blocks with context
- Log errors appropriately
- Implement graceful degradation

**Tests**:
- Add error test cases to all test files
- Test recovery scenarios

---

### Phase 6: Performance Optimization [Priority: Low]

#### Task 6.1: Implement Caching System
**Status**: [ ] Pending
**Dependencies**: Task 2.1
**Description**: Cache generated images by prompt hash
**Files to create**:
- `src/refexp/cache.py`

**Implementation**:
- Hash prompts for cache keys
- Store images with metadata
- Implement TTL and cleanup
- Add cache hit/miss logging

**Tests**:
- `tests/test_refexp/test_cache.py`
- Test caching behavior
- Test TTL enforcement
- Test cache cleanup

---

#### Task 6.2: Optimize Memory Usage
**Status**: [ ] Pending
**Dependencies**: Task 1.3, Task 2.1
**Description**: Stream large combination sets
**Files to modify**:
- `src/refexp/combinator.py`
- `src/refexp/generator.py`

**Implementation**:
- Use generators for large combination sets
- Process in configurable batches
- Clear image data after saving
- Monitor memory usage

**Tests**:
- Test with large combination sets
- Test memory efficiency

---

### Phase 7: Documentation & Examples [Priority: Low]

#### Task 7.1: Create Example YAML Files
**Status**: [ ] Pending
**Dependencies**: Task 1.2
**Description**: Provide sample experiment files
**Files to create**:
- `examples/reference_experiments/character_styles.yaml`
- `examples/reference_experiments/scene_lighting.yaml`
- `examples/reference_experiments/composition_tests.yaml`
- `examples/reference_experiments/README.md`

**Example Content**:
```yaml
# character_styles.yaml
name: "Character Style Variations"
description: "Test different art styles for character generation"
prompt: "Create a {style} portrait of a {character} with {emotion} expression"
variables:
  style: ["anime", "realistic", "comic book", "watercolor"]
  character: ["warrior", "mage", "detective"]
  emotion: ["happy", "serious", "mysterious"]
settings:
  quality: high
  iterations: 10
```

---

#### Task 7.2: Update Main Documentation
**Status**: [ ] Pending
**Dependencies**: All tasks
**Description**: Update README and other docs
**Files to modify**:
- `README.md`

**Updates**:
- Add reference experiments section
- Update CLI commands
- Add configuration examples

---

### Phase 8: Integration Testing [Priority: High]

#### Task 8.1: Create End-to-End Tests
**Status**: [ ] Pending
**Dependencies**: All Phase 1-3 tasks
**Description**: Test complete workflow
**Files to create**:
- `tests/test_refexp/test_integration.py`

**Tests**:
- Full workflow from YAML file to images
- Test with mock Gemini API
- Test error scenarios
- Test checkpoint recovery
- Test settings override from YAML

---

#### Task 8.2: Add to CI/CD Pipeline
**Status**: [ ] Pending
**Dependencies**: Task 8.1
**Description**: Ensure tests run in CI
**Files to modify**:
- `.github/workflows/test.yml` (if exists)
- `Makefile`

**Updates**:
- Add refexp tests to test suite
- Update coverage requirements
- Add integration test job

---

## Implementation Order

**Week 1**: Phase 1 (Core Infrastructure) + Phase 3 (CLI Integration)
- Get basic functionality working end-to-end
- Focus on parser, combinator, and CLI

**Week 2**: Phase 2 (Image Generation) + Phase 4 (Configuration)
- Integrate with Gemini API
- Add configuration support
- Implement reference tracker

**Week 3**: Phase 5 (Error Handling) + Phase 8 (Integration Testing)
- Add robust error handling
- Implement checkpoint system
- Complete integration tests

**Week 4**: Phase 6 (Performance) + Phase 7 (Documentation)
- Optimize performance
- Add caching
- Complete documentation and examples

## Success Criteria

1. **Functionality**:
   - [ ] Can parse YAML files correctly
   - [ ] Validates YAML schema and structure
   - [ ] Generates all specified combinations
   - [ ] Creates images via Gemini API
   - [ ] Updates reference_images.md correctly
   - [ ] CLI command works as specified
   - [ ] Settings from YAML are properly applied

2. **Quality**:
   - [ ] Test coverage > 80%
   - [ ] All tests passing
   - [ ] No linting errors
   - [ ] Type hints on all functions
   - [ ] Comprehensive error handling

3. **Performance**:
   - [ ] Can handle 1000+ combinations
   - [ ] Respects API rate limits
   - [ ] Memory efficient for large sets
   - [ ] Concurrent generation working

4. **Documentation**:
   - [ ] User guide complete
   - [ ] Architecture document current
   - [ ] Code well-documented
   - [ ] Examples provided

## Notes

- Reuse existing components where possible (GeminiClient, RateLimiter, Config)
- Maintain consistency with existing codebase style
- Focus on integration rather than reimplementation
- Prioritize user experience with good progress feedback
- Ensure backward compatibility with existing functionality