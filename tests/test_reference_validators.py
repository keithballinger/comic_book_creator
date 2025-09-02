"""Unit tests for reference validators."""

import pytest
from io import BytesIO
from PIL import Image

from src.references.validators import (
    ValidationError,
    ValidationWarning,
    ReferenceValidator,
    ImageValidator,
    ConsistencyValidator,
    ValidationReport,
)
from src.references.models import (
    CharacterReference,
    LocationReference,
    ObjectReference,
    StyleGuide,
)


class TestValidationWarning:
    """Test ValidationWarning class."""
    
    def test_warning_creation(self):
        """Test creating a validation warning."""
        warning = ValidationWarning("test_field", "Test message", "major")
        
        assert warning.field == "test_field"
        assert warning.message == "Test message"
        assert warning.severity == "major"
        assert warning.timestamp is not None
    
    def test_warning_string(self):
        """Test warning string representation."""
        warning = ValidationWarning("name", "Invalid name", "critical")
        
        result = str(warning)
        assert "[CRITICAL]" in result
        assert "name:" in result
        assert "Invalid name" in result


class TestReferenceValidator:
    """Test ReferenceValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ReferenceValidator()
    
    def test_validate_valid_character(self, validator):
        """Test validating a valid character reference."""
        char = CharacterReference(
            name="Hero",
            description="A brave hero who saves the day",
            poses=["standing", "running"],
            expressions=["happy", "determined"]
        )
        
        is_valid, warnings = validator.validate_reference(char)
        
        assert is_valid
        assert len(warnings) == 0
    
    def test_validate_name_too_short(self, validator):
        """Test validation with name too short."""
        char = CharacterReference(
            name="H",
            description="A brave hero who saves the day"
        )
        
        is_valid, warnings = validator.validate_reference(char)
        
        assert is_valid  # Still valid, just has warnings
        assert len(warnings) > 0
        assert any(w.field == "name" and "too short" in w.message.lower() for w in warnings)
    
    def test_validate_name_too_long(self, validator):
        """Test validation with name too long."""
        char = CharacterReference(
            name="A" * 60,
            description="A brave hero who saves the day"
        )
        
        is_valid, warnings = validator.validate_reference(char)
        
        assert is_valid
        assert any(w.field == "name" and "too long" in w.message.lower() for w in warnings)
    
    def test_validate_invalid_name_pattern(self, validator):
        """Test validation with invalid name pattern."""
        char = CharacterReference(
            name="123Hero",  # Starts with number
            description="A brave hero who saves the day"
        )
        
        is_valid, warnings = validator.validate_reference(char)
        
        assert is_valid
        assert any(w.field == "name" and "invalid characters" in w.message.lower() for w in warnings)
    
    def test_validate_reserved_name(self, validator):
        """Test validation with reserved name."""
        char = CharacterReference(
            name="default",
            description="A brave hero who saves the day"
        )
        
        is_valid, warnings = validator.validate_reference(char)
        
        assert is_valid
        assert any(w.field == "name" and "reserved" in w.message.lower() for w in warnings)
        assert any(w.severity == "critical" for w in warnings)
    
    def test_validate_description_too_short(self, validator):
        """Test validation with description too short."""
        char = CharacterReference(
            name="Hero",
            description="Short"
        )
        
        is_valid, warnings = validator.validate_reference(char)
        
        assert is_valid
        assert any(w.field == "description" and "too short" in w.message.lower() for w in warnings)
    
    def test_validate_character_no_poses(self, validator):
        """Test character validation with no poses."""
        char = CharacterReference(
            name="Hero",
            description="A brave hero who saves the day",
            poses=[],
            expressions=["happy"]
        )
        
        is_valid, warnings = validator.validate_reference(char)
        
        assert is_valid
        assert any(w.field == "poses" and "no poses" in w.message.lower() for w in warnings)
    
    def test_validate_character_duplicate_poses(self, validator):
        """Test character validation with duplicate poses."""
        char = CharacterReference(
            name="Hero",
            description="A brave hero who saves the day",
            poses=["standing", "standing", "running"],
            expressions=["happy"]
        )
        
        is_valid, warnings = validator.validate_reference(char)
        
        assert is_valid
        assert any(w.field == "poses" and "duplicate" in w.message.lower() for w in warnings)
    
    def test_validate_location(self, validator):
        """Test location validation."""
        location = LocationReference(
            name="Forest",
            description="A mystical forest with ancient trees",
            angles=["wide", "close"],
            lighting_conditions=["dawn", "dusk"]
        )
        
        is_valid, warnings = validator.validate_reference(location)
        
        assert is_valid
        assert len(warnings) == 0
    
    def test_validate_location_no_angles(self, validator):
        """Test location validation with no angles."""
        location = LocationReference(
            name="Forest",
            description="A mystical forest with ancient trees",
            angles=[],
            lighting_conditions=["dawn"]
        )
        
        is_valid, warnings = validator.validate_reference(location)
        
        assert is_valid
        assert any(w.field == "angles" for w in warnings)
    
    def test_validate_object(self, validator):
        """Test object validation."""
        obj = ObjectReference(
            name="Sword",
            description="A magical sword with ancient runes",
            views=["front", "side"],
            states=["normal", "glowing"]
        )
        
        is_valid, warnings = validator.validate_reference(obj)
        
        assert is_valid
        assert len(warnings) == 0
    
    def test_validate_style_guide(self, validator):
        """Test style guide validation."""
        style = StyleGuide(
            name="Comic Style",
            description="A classic comic book art style",
            art_style="comic-book",
            color_palette=["#FF0000", "#00FF00", "#0000FF"]
        )
        
        is_valid, warnings = validator.validate_reference(style)
        
        assert is_valid
        assert len(warnings) == 0
    
    def test_validate_style_guide_invalid_color(self, validator):
        """Test style guide with invalid color."""
        # Invalid color causes model validation to fail
        # So we test the validator's _is_valid_color method directly
        assert validator._is_valid_color("#FF0000")
        assert validator._is_valid_color("#00FF00")
        assert not validator._is_valid_color("not-a-color")
        assert not validator._is_valid_color("#FF00")  # Too short
        assert not validator._is_valid_color("#FF00GG")  # Invalid hex
    
    def test_validate_strict_mode(self, validator):
        """Test strict validation mode."""
        char = CharacterReference(
            name="default",  # Reserved name
            description="A brave hero who saves the day"
        )
        
        # Non-strict mode - still valid despite critical warning
        is_valid, warnings = validator.validate_reference(char, strict=False)
        assert is_valid
        assert any(w.severity == "critical" for w in warnings)
        
        # Strict mode - invalid due to critical warning
        is_valid, warnings = validator.validate_reference(char, strict=True)
        assert not is_valid


class TestImageValidator:
    """Test ImageValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ImageValidator()
    
    @pytest.fixture
    def valid_image_data(self):
        """Create valid image data."""
        img = Image.new('RGB', (512, 512), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def test_validate_valid_image(self, validator, valid_image_data):
        """Test validating a valid image."""
        is_valid, warnings = validator.validate_image(valid_image_data)
        
        assert is_valid
        assert len(warnings) == 0
    
    def test_validate_image_too_large_file(self, validator):
        """Test validating image with file size too large."""
        # Create fake large data
        large_data = b'x' * (11 * 1024 * 1024)  # 11MB
        
        is_valid, warnings = validator.validate_image(large_data)
        
        assert not is_valid
        assert any(w.field == "file_size" for w in warnings)
    
    def test_validate_image_too_small_dimensions(self, validator):
        """Test validating image with dimensions too small."""
        img = Image.new('RGB', (100, 100), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        is_valid, warnings = validator.validate_image(buffer.getvalue())
        
        assert is_valid  # Still valid, just has warnings
        assert any(w.field == "dimensions" and "too small" in w.message.lower() for w in warnings)
    
    def test_validate_image_too_large_dimensions(self, validator):
        """Test validating image with dimensions too large."""
        img = Image.new('RGB', (5000, 5000), color='green')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        is_valid, warnings = validator.validate_image(buffer.getvalue())
        
        assert is_valid
        assert any(w.field == "dimensions" and "too large" in w.message.lower() for w in warnings)
    
    def test_validate_unusual_aspect_ratio(self, validator):
        """Test validating image with unusual aspect ratio."""
        img = Image.new('RGB', (1024, 256), color='yellow')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        is_valid, warnings = validator.validate_image(buffer.getvalue())
        
        assert is_valid
        assert any(w.field == "aspect_ratio" for w in warnings)
    
    def test_validate_rgba_without_transparency(self, validator):
        """Test validating RGBA image without actual transparency."""
        img = Image.new('RGBA', (512, 512), color=(255, 0, 0, 255))
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        is_valid, warnings = validator.validate_image(buffer.getvalue())
        
        assert is_valid
        assert any(w.field == "transparency" for w in warnings)
    
    def test_validate_invalid_image_data(self, validator):
        """Test validating invalid image data."""
        invalid_data = b'not an image'
        
        is_valid, warnings = validator.validate_image(invalid_data)
        
        assert not is_valid
        assert any(w.severity == "critical" for w in warnings)
    
    def test_check_quality(self, validator):
        """Test image quality check."""
        # High quality PNG
        img = Image.new('RGB', (1024, 1024), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        quality_score, warnings = validator.check_quality(buffer.getvalue())
        
        assert quality_score > 0.9
        assert len(warnings) == 0
    
    def test_check_quality_low_res(self, validator):
        """Test quality check for low resolution image."""
        img = Image.new('RGB', (256, 256), color='blue')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        quality_score, warnings = validator.check_quality(buffer.getvalue())
        
        assert quality_score < 0.9
        assert any("resolution" in w.message.lower() for w in warnings)
    
    def test_check_quality_jpeg(self, validator):
        """Test quality check for JPEG image."""
        img = Image.new('RGB', (1024, 1024), color='green')
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        
        quality_score, warnings = validator.check_quality(buffer.getvalue())
        
        assert quality_score < 1.0
        assert any("compression" in w.message.lower() for w in warnings)


class TestConsistencyValidator:
    """Test ConsistencyValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ConsistencyValidator()
    
    def test_check_consistency_no_conflicts(self, validator):
        """Test consistency check with no conflicts."""
        references = [
            CharacterReference(name="Hero", description="A brave hero"),
            CharacterReference(name="Villain", description="An evil villain"),
            LocationReference(name="Forest", description="A dark forest"),
        ]
        
        warnings = validator.check_consistency(references)
        
        assert len(warnings) == 0
    
    def test_check_consistency_duplicate_names(self, validator):
        """Test consistency check with duplicate names."""
        references = [
            CharacterReference(name="Hero", description="A brave hero"),
            CharacterReference(name="Hero", description="Another hero"),
        ]
        
        warnings = validator.check_consistency(references)
        
        assert len(warnings) > 0
        assert any("duplicate" in w.message.lower() for w in warnings)
    
    def test_check_consistency_similar_names(self, validator):
        """Test consistency check with similar names."""
        references = [
            CharacterReference(name="Hero", description="A brave hero"),
            CharacterReference(name="Heroes", description="Multiple heroes"),
        ]
        
        warnings = validator.check_consistency(references)
        
        assert any("similar" in w.message.lower() for w in warnings)
    
    def test_check_consistency_multiple_styles(self, validator):
        """Test consistency check with multiple style guides."""
        references = [
            StyleGuide(name="Comic Style", description="Comic book style", art_style="comic"),
            StyleGuide(name="Manga Style", description="Manga style", art_style="manga"),
        ]
        
        warnings = validator.check_consistency(references)
        
        assert any("multiple art styles" in w.message.lower() for w in warnings)
    
    def test_name_similarity(self, validator):
        """Test name similarity calculation."""
        # Exact match
        assert validator._name_similarity("Hero", "Hero") == 1.0
        
        # Case insensitive
        assert validator._name_similarity("Hero", "hero") == 1.0
        
        # Substring
        assert validator._name_similarity("Hero", "Superhero") == 0.85
        
        # Common prefix
        similarity = validator._name_similarity("Hero", "Heroes")
        assert 0.5 < similarity < 1.0
        
        # No similarity
        assert validator._name_similarity("Hero", "Villain") == 0.0


class TestValidationReport:
    """Test ValidationReport class."""
    
    @pytest.fixture
    def report(self):
        """Create report instance."""
        return ValidationReport()
    
    def test_add_reference_result(self, report):
        """Test adding reference validation result."""
        warnings = [ValidationWarning("name", "Test warning", "minor")]
        report.add_reference_result("character/Hero", True, warnings)
        
        assert "character/Hero" in report.reference_results
        assert report.reference_results["character/Hero"][0] is True
        assert len(report.reference_results["character/Hero"][1]) == 1
    
    def test_add_image_result(self, report):
        """Test adding image validation result."""
        warnings = [ValidationWarning("size", "Too large", "major")]
        report.add_image_result("hero.png", False, warnings)
        
        assert "hero.png" in report.image_results
        assert report.image_results["hero.png"][0] is False
    
    def test_is_valid_all_valid(self, report):
        """Test is_valid when all validations pass."""
        report.add_reference_result("char1", True, [])
        report.add_image_result("img1", True, [])
        
        assert report.is_valid()
    
    def test_is_valid_with_invalid_reference(self, report):
        """Test is_valid with invalid reference."""
        report.add_reference_result("char1", False, [])
        report.add_image_result("img1", True, [])
        
        assert not report.is_valid()
    
    def test_is_valid_with_critical_consistency(self, report):
        """Test is_valid with critical consistency warning."""
        report.add_reference_result("char1", True, [])
        report.set_consistency_warnings([
            ValidationWarning("consistency", "Critical issue", "critical")
        ])
        
        assert not report.is_valid()
    
    def test_get_summary(self, report):
        """Test getting validation summary."""
        report.add_reference_result("char1", True, [
            ValidationWarning("name", "Minor issue", "minor")
        ])
        report.add_reference_result("char2", False, [
            ValidationWarning("desc", "Major issue", "major")
        ])
        report.add_image_result("img1", True, [])
        report.set_consistency_warnings([
            ValidationWarning("naming", "Warning", "warning")
        ])
        
        summary = report.get_summary()
        
        assert summary["is_valid"] is False
        assert summary["references"]["total"] == 2
        assert summary["references"]["valid"] == 1
        assert summary["images"]["total"] == 1
        assert summary["images"]["valid"] == 1
        assert summary["warnings"]["total"] == 3
        assert summary["warnings"]["by_severity"]["minor"] == 1
        assert summary["warnings"]["by_severity"]["major"] == 1
        assert summary["warnings"]["by_severity"]["warning"] == 1
    
    def test_format_report(self, report):
        """Test formatting report as string."""
        report.add_reference_result("character/Hero", True, [
            ValidationWarning("poses", "No poses defined", "warning")
        ])
        
        formatted = report.format_report()
        
        assert "VALIDATION REPORT" in formatted
        assert "✅ VALID" in formatted
        assert "character/Hero" in formatted
        assert "No poses defined" in formatted