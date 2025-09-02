# Reference Image System - Task Breakdown

## General Development Guidance

### **Core Principles**
- **Use Python:** Implement all components using Python with standard project layout
- **Test-Driven Development:** Write tests before implementing each task
- **Build and Test:** Use `make build` and `make test` commands consistently

### **Post-Task Checklist**
1. Update `arch_reference_system.md` if any architectural changes were made
2. Mark the task as complete in `tasks_reference_system.md`
3. Document implementation notes and architectural decisions in `tasks_reference_system.md`
4. Update remaining tasks if architecture changes affected dependencies
5. Ensure `make build` and `make test` run successfully with no warnings
6. Run a linter and fix any issues, run tests and fix any issues
7. Commit changes with descriptive commit message following conventional commits
8. Don't include Claude as an author or coauthor

### **Code Quality Standards**
- **Testing:** Table-driven tests with subtests, >80% coverage, mock external dependencies

---

## Task List

### Phase 1: Foundation (READY)

#### Task 1.1: Create Reference Data Models ⏳ READY
**Description:** Implement core data models for references
**Dependencies:** None
**Estimated Time:** 2 hours

**Subtasks:**
- [ ] Create `src/references/__init__.py`
- [ ] Create `src/references/models.py` with:
  - [ ] `BaseReference` abstract class
  - [ ] `CharacterReference` dataclass
  - [ ] `LocationReference` dataclass  
  - [ ] `ObjectReference` dataclass
  - [ ] `StyleGuide` dataclass
- [ ] Add validation methods to each model
- [ ] Write unit tests for models
- [ ] Add type hints and docstrings

**Acceptance Criteria:**
- All reference models defined with proper validation
- Unit tests pass with >80% coverage
- Models support serialization to/from JSON
- Clear error messages for invalid data

**Implementation Notes:**

#### Task 1.2: Implement Reference Storage System ⏳ READY
**Description:** Create file-based storage for references
**Dependencies:** Task 1.1
**Estimated Time:** 3 hours

**Subtasks:**
- [ ] Create `src/references/storage.py`
- [ ] Implement `ReferenceStorage` class with:
  - [ ] `save_reference()` method
  - [ ] `load_reference()` method
  - [ ] `list_references()` method
  - [ ] `delete_reference()` method
  - [ ] `exists()` method
- [ ] Add directory structure creation
- [ ] Implement JSON serialization/deserialization
- [ ] Add file locking for concurrent access
- [ ] Write unit tests with temporary directories
- [ ] Add error handling for I/O operations

**Acceptance Criteria:**
- References can be saved and loaded reliably
- Directory structure is created automatically
- Concurrent access is handled safely
- Comprehensive error handling and logging
- Tests verify all CRUD operations

**Implementation Notes:**

### Phase 2: Reference Generation (BLOCKED: 1.1, 1.2)

#### Task 2.1: Create Reference Generator Base ⏳ BLOCKED
**Description:** Implement base class for reference generation
**Dependencies:** Task 1.1, Task 1.2
**Estimated Time:** 2 hours

**Subtasks:**
- [ ] Create `src/references/generators.py`
- [ ] Implement `BaseReferenceGenerator` abstract class
- [ ] Add Gemini client integration
- [ ] Implement common prompt building utilities
- [ ] Add reference image processing utilities
- [ ] Write base test class for generators
- [ ] Add configuration for generation parameters

**Acceptance Criteria:**
- Base generator class provides common functionality
- Proper integration with existing Gemini client
- Extensible design for different reference types
- Error handling for generation failures
- Tests verify base functionality

**Implementation Notes:**

#### Task 2.2: Implement Character Reference Generator ⏳ BLOCKED
**Description:** Generate character reference sheets and poses
**Dependencies:** Task 2.1
**Estimated Time:** 4 hours

**Subtasks:**
- [ ] Implement `CharacterReferenceGenerator` class
- [ ] Add `generate_character_sheet()` method
- [ ] Add `generate_character_pose()` method
- [ ] Implement character consistency prompts
- [ ] Add batch generation for multiple poses
- [ ] Handle expression combinations
- [ ] Write comprehensive tests with mocked Gemini
- [ ] Add character reference validation

**Acceptance Criteria:**
- Can generate character sheets with multiple poses
- Consistent character appearance across poses
- Efficient batch generation of poses
- Proper error handling and retry logic
- Tests verify generation quality and consistency

**Implementation Notes:**

#### Task 2.3: Implement Location Reference Generator ⏳ BLOCKED
**Description:** Generate location reference images
**Dependencies:** Task 2.1  
**Estimated Time:** 3 hours

**Subtasks:**
- [ ] Implement `LocationReferenceGenerator` class
- [ ] Add `generate_location_views()` method
- [ ] Implement lighting and angle variations
- [ ] Add establishing shot generation
- [ ] Handle interior/exterior variations
- [ ] Write tests for location generation
- [ ] Add location reference validation

**Acceptance Criteria:**
- Can generate location views from different angles
- Supports various lighting conditions
- Consistent location appearance
- Efficient generation process
- Tests verify location consistency

**Implementation Notes:**

### Phase 3: Reference Management (BLOCKED: 1.1, 1.2, 2.1)

#### Task 3.1: Implement Reference Manager ⏳ BLOCKED
**Description:** Central management system for all references
**Dependencies:** Task 1.1, Task 1.2, Task 2.1
**Estimated Time:** 4 hours

**Subtasks:**
- [ ] Create `src/references/manager.py`
- [ ] Implement `ReferenceManager` class
- [ ] Add reference CRUD operations
- [ ] Implement reference lookup and matching
- [ ] Add caching system for performance
- [ ] Implement reference naming conventions
- [ ] Add reference validation and cleanup
- [ ] Write comprehensive manager tests
- [ ] Add configuration management

**Acceptance Criteria:**
- Central interface for all reference operations
- Efficient reference lookup and caching
- Proper validation and error handling
- Clean API for integration with generators
- Tests verify all manager functionality

**Implementation Notes:**

#### Task 3.2: Add Reference Validators ⏳ BLOCKED
**Description:** Validation system for reference data
**Dependencies:** Task 3.1
**Estimated Time:** 2 hours

**Subtasks:**
- [ ] Create `src/references/validators.py`
- [ ] Implement reference format validation
- [ ] Add image quality validation
- [ ] Implement consistency checking
- [ ] Add reference completeness validation
- [ ] Write validator tests
- [ ] Add custom validation rules

**Acceptance Criteria:**
- Comprehensive validation of reference data
- Image quality and format checking
- Consistency validation across references
- Clear validation error messages
- Tests verify all validation scenarios

**Implementation Notes:**

### Phase 4: CLI Integration (BLOCKED: 3.1, 3.2)

#### Task 4.1: Add Reference CLI Commands ⏳ BLOCKED
**Description:** CLI interface for reference management
**Dependencies:** Task 3.1, Task 3.2
**Estimated Time:** 3 hours

**Subtasks:**
- [ ] Add reference command group to CLI
- [ ] Implement `create-character` command
- [ ] Implement `create-location` command
- [ ] Implement `create-object` command
- [ ] Add `list-references` command
- [ ] Add `update-reference` command
- [ ] Add `delete-reference` command
- [ ] Write CLI integration tests
- [ ] Add command help and examples

**Acceptance Criteria:**
- Complete CLI interface for reference management
- Proper argument parsing and validation
- Clear error messages and help text
- Integration tests verify CLI functionality
- Good user experience with examples

**Implementation Notes:**

#### Task 4.2: Add Reference Validation CLI ⏳ BLOCKED
**Description:** CLI commands for reference validation and cleanup
**Dependencies:** Task 4.1
**Estimated Time:** 2 hours

**Subtasks:**
- [ ] Add `validate-reference` command
- [ ] Add `cleanup-references` command
- [ ] Add `archive-references` command
- [ ] Implement batch validation
- [ ] Add reference repair functionality
- [ ] Write validation CLI tests
- [ ] Add progress reporting for long operations

**Acceptance Criteria:**
- Comprehensive reference validation via CLI
- Cleanup and maintenance commands
- Batch operations with progress reporting
- Tests verify validation and cleanup
- Clear reporting of validation results

**Implementation Notes:**

### Phase 5: Generation Integration (BLOCKED: 3.1, 4.1)

#### Task 5.1: Integrate References into Page Generation ⏳ BLOCKED
**Description:** Use references in comic page generation
**Dependencies:** Task 3.1, Task 4.1
**Estimated Time:** 4 hours

**Subtasks:**
- [ ] Modify `PageGenerator` to accept `ReferenceManager`
- [ ] Add reference extraction from page content
- [ ] Implement reference image inclusion in Gemini prompts
- [ ] Add reference consistency prompts
- [ ] Handle missing reference gracefully
- [ ] Update page generation tests
- [ ] Add reference usage logging

**Acceptance Criteria:**
- Page generation uses available references
- Consistent character/location appearance
- Graceful handling of missing references
- Proper integration with existing pipeline
- Tests verify reference integration

**Implementation Notes:**

#### Task 5.2: Add Reference Context to Prompts ⏳ BLOCKED
**Description:** Enhance prompts with reference information
**Dependencies:** Task 5.1
**Estimated Time:** 3 hours

**Subtasks:**
- [ ] Modify prompt building to include references
- [ ] Add reference image context to Gemini calls
- [ ] Implement reference description integration
- [ ] Add style consistency instructions
- [ ] Handle multiple reference types in one panel
- [ ] Update prompt debugging output
- [ ] Add reference usage statistics

**Acceptance Criteria:**
- Prompts include relevant reference context
- Reference images passed to Gemini properly
- Style consistency maintained across pages
- Debug output shows reference usage
- Statistics track reference effectiveness

**Implementation Notes:**

### Phase 6: Testing and Polish (BLOCKED: 5.1, 5.2)

#### Task 6.1: End-to-End Integration Testing ⏳ BLOCKED
**Description:** Comprehensive testing of reference system
**Dependencies:** Task 5.1, Task 5.2
**Estimated Time:** 3 hours

**Subtasks:**
- [ ] Create end-to-end test scenarios
- [ ] Test complete reference creation workflow
- [ ] Test comic generation with references
- [ ] Add performance benchmarking
- [ ] Test error scenarios and recovery
- [ ] Add memory usage testing
- [ ] Create test reference library

**Acceptance Criteria:**
- Complete end-to-end functionality verified
- Performance meets requirements
- Error handling thoroughly tested
- Memory usage within acceptable limits
- Test reference library for demos

**Implementation Notes:**

#### Task 6.2: Documentation and Examples ⏳ BLOCKED
**Description:** Complete documentation and example workflows
**Dependencies:** Task 6.1
**Estimated Time:** 2 hours

**Subtasks:**
- [ ] Update user guide with final CLI commands
- [ ] Add reference system examples to documentation
- [ ] Create tutorial workflow
- [ ] Add troubleshooting guide
- [ ] Update main README with reference features
- [ ] Create example reference library
- [ ] Add video/screenshot documentation

**Acceptance Criteria:**
- Complete and accurate documentation
- Working examples and tutorials
- Clear troubleshooting guidance
- Example reference library available
- Professional documentation quality

**Implementation Notes:**

---

## Implementation Progress

### Completed Tasks
None yet - ready to begin!

### Current Focus
Starting with Task 1.1: Create Reference Data Models

### Next Up
Task 1.2: Implement Reference Storage System

### Blockers
None - foundation tasks are ready to start

---

## Technical Decisions Log

### Decision 1: Storage Format
**Date:** TBD
**Decision:** Use JSON for reference metadata with separate image files
**Rationale:** Simple, human-readable, easy to version control
**Alternatives Considered:** SQLite database, binary format
**Impact:** Easier debugging and manual editing

### Decision 2: Reference Naming
**Date:** TBD  
**Decision:** TBD
**Rationale:** TBD

---

## Performance Requirements

- Reference lookup: < 100ms
- Character generation: < 30s for full sheet
- Memory usage: < 500MB for reference cache
- Storage: Efficient image compression

## Quality Gates

- [ ] All unit tests pass
- [ ] Integration tests pass  
- [ ] Code coverage > 80%
- [ ] No lint warnings
- [ ] Documentation complete
- [ ] Performance requirements met