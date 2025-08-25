import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from dlp_processor import DLPProcessor, PIIEntity, ScanResult


class TestPIIEntity:
    """Test cases for PIIEntity dataclass."""
    
    def test_pii_entity_creation(self):
        """Test creating a PIIEntity instance."""
        entity = PIIEntity(
            entity_type="ssn",
            value="123-45-6789",
            confidence=0.95,
            start_pos=10,
            end_pos=21,
            context="SSN: 123-45-6789"
        )
        
        assert entity.entity_type == "ssn"
        assert entity.value == "123-45-6789"
        assert entity.confidence == 0.95
        assert entity.start_pos == 10
        assert entity.end_pos == 21
        assert entity.context == "SSN: 123-45-6789"
    
    def test_pii_entity_defaults(self):
        """Test PIIEntity with minimal required fields."""
        entity = PIIEntity(
            entity_type="email",
            value="test@example.com",
            confidence=0.8,
            start_pos=0,
            end_pos=18,
            context="test@example.com"
        )
        
        assert entity.entity_type == "email"
        assert entity.value == "test@example.com"


class TestScanResult:
    """Test cases for ScanResult dataclass."""
    
    def test_scan_result_creation(self):
        """Test creating a ScanResult instance."""
        entities = [
            PIIEntity("ssn", "123-45-6789", 0.9, 0, 11, "SSN: 123-45-6789")
        ]
        
        result = ScanResult(
            file_path="/test/file.txt",
            file_type="text",
            file_size=100,
            pii_entities=entities,
            risk_score=0.7,
            scan_timestamp="2024-01-01T00:00:00",
            is_safe=False
        )
        
        assert result.file_path == "/test/file.txt"
        assert result.file_type == "text"
        assert result.file_size == 100
        assert len(result.pii_entities) == 1
        assert result.risk_score == 0.7
        assert result.is_safe is False


class TestDLPProcessor:
    """Test cases for DLPProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a DLPProcessor instance for testing."""
        return DLPProcessor()
    
    @pytest.fixture
    def sample_text_file(self):
        """Create a temporary text file with sample PII data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            Customer Information:
            Name: John Doe
            SSN: 123-45-6789
            Email: john.doe@example.com
            Phone: 555-123-4567
            Credit Card: 1234-5678-9012-3456
            IP Address: 192.168.1.1
            Date of Birth: 01/15/1980
            """)
            temp_file = f.name
        
        yield temp_file
        os.unlink(temp_file)
    
    @pytest.fixture
    def sample_json_file(self):
        """Create a temporary JSON file with sample PII data."""
        data = {
            "patient": {
                "id": "PID12345",
                "medical_record": "MRN: 987654321",
                "diagnosis": "ICD-10: A01.1",
                "prescription": "RX: 12345"
            },
            "contact": {
                "email": "patient@hospital.com",
                "phone": "555-987-6543"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            temp_file = f.name
        
        yield temp_file
        os.unlink(temp_file)
    
    @pytest.fixture
    def sample_pdf_file(self):
        """Create a temporary PDF file for testing."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Create a minimal PDF-like file
            f.write(b"%PDF-1.4\n%Test PDF content\n")
            temp_file = f.name
        
        yield temp_file
        os.unlink(temp_file)
    
    def test_processor_initialization(self, processor):
        """Test DLPProcessor initialization."""
        assert processor.pii_patterns is not None
        assert processor.phi_patterns is not None
        assert processor.risk_thresholds is not None
        
        # Check that patterns are properly defined
        assert 'ssn' in processor.pii_patterns
        assert 'credit_card' in processor.pii_patterns
        assert 'email' in processor.pii_patterns
        assert 'medical_record' in processor.phi_patterns
    
    def test_validate_file_path_valid(self, processor, sample_text_file):
        """Test file path validation with valid file."""
        assert processor.validate_file_path(sample_text_file) is True
    
    def test_validate_file_path_invalid(self, processor):
        """Test file path validation with invalid file."""
        assert processor.validate_file_path("/nonexistent/file.txt") is False
    
    def test_validate_file_path_empty(self, processor):
        """Test file path validation with empty string."""
        assert processor.validate_file_path("") is False
    
    def test_detect_pii_in_text(self, processor):
        """Test PII detection in text content."""
        content = "SSN: 123-45-6789, Email: test@example.com"
        entities = processor._detect_pii_in_text(content)
        
        assert len(entities) == 2
        
        # Check SSN entity
        ssn_entity = next(e for e in entities if e.entity_type == 'ssn')
        assert ssn_entity.value == "123-45-6789"
        assert ssn_entity.confidence == 0.9
        
        # Check email entity
        email_entity = next(e for e in entities if e.entity_type == 'email')
        assert email_entity.value == "test@example.com"
        assert email_entity.confidence == 0.9
    
    def test_detect_phi_in_text(self, processor):
        """Test PHI detection in text content."""
        content = "MRN: 12345, ICD-10: A01.1, RX: 98765"
        entities = processor._detect_pii_in_text(content)
        
        phi_entities = [e for e in entities if e.entity_type in processor.phi_patterns]
        assert len(phi_entities) == 3
        
        # Check medical record entity
        mrn_entity = next(e for e in phi_entities if e.entity_type == 'medical_record')
        assert mrn_entity.value == "MRN: 12345"
        assert mrn_entity.confidence == 0.85
    
    def test_calculate_risk_score_no_entities(self, processor):
        """Test risk score calculation with no PII entities."""
        score = processor._calculate_risk_score([], 1000)
        assert score == 0.0
    
    def test_calculate_risk_score_with_entities(self, processor):
        """Test risk score calculation with PII entities."""
        entities = [
            PIIEntity("ssn", "123-45-6789", 0.9, 0, 11, "SSN: 123-45-6789"),
            PIIEntity("email", "test@example.com", 0.9, 15, 33, "test@example.com")
        ]
        
        score = processor._calculate_risk_score(entities, 1000)
        assert score > 0.0
        assert score <= 1.0
    
    def test_calculate_risk_score_high_risk_types(self, processor):
        """Test risk score calculation with high-risk entity types."""
        entities = [
            PIIEntity("ssn", "123-45-6789", 0.9, 0, 11, "SSN: 123-45-6789"),
            PIIEntity("credit_card", "1234-5678-9012-3456", 0.9, 15, 34, "CC: 1234-5678-9012-3456")
        ]
        
        score = processor._calculate_risk_score(entities, 1000)
        # Should be higher due to high-risk types
        assert score > 0.4
    
    def test_scan_text_file(self, processor, sample_text_file):
        """Test scanning a text file."""
        result = processor.scan_text_file(sample_text_file)
        
        assert isinstance(result, ScanResult)
        assert result.file_path == sample_text_file
        assert result.file_type == "text"
        assert result.file_size > 0
        assert len(result.pii_entities) > 0
        assert result.risk_score > 0.0
        assert isinstance(result.scan_timestamp, str)
    
    def test_scan_json_file(self, processor, sample_json_file):
        """Test scanning a JSON file."""
        result = processor.scan_json_file(sample_json_file)
        
        assert isinstance(result, ScanResult)
        assert result.file_path == sample_json_file
        assert result.file_type == "json"
        assert result.file_size > 0
        assert len(result.pii_entities) > 0
        assert result.risk_score > 0.0
    
    def test_scan_pdf_file(self, processor, sample_pdf_file):
        """Test scanning a PDF file."""
        result = processor.scan_pdf_file(sample_pdf_file)
        
        assert isinstance(result, ScanResult)
        assert result.file_path == sample_pdf_file
        assert result.file_type == "pdf"
        assert result.file_size > 0
        # PDF scanning is simplified, so no PII should be found
        assert len(result.pii_entities) == 0
        assert result.risk_score == 0.0
    
    def test_scan_text_file_error(self, processor):
        """Test scanning a non-existent text file."""
        with pytest.raises(ValueError):
            processor.scan_text_file("/nonexistent/file.txt")
    
    def test_scan_json_file_error(self, processor):
        """Test scanning a malformed JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with pytest.raises(ValueError):
                processor.scan_json_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    def test_get_scan_summary(self, processor):
        """Test generating scan summary."""
        # Create mock scan results
        results = [
            ScanResult("file1.txt", "text", 100, [], 0.0, "2024-01-01T00:00:00", True),
            ScanResult("file2.txt", "text", 200, [PIIEntity("ssn", "123-45-6789", 0.9, 0, 11, "")], 0.8, "2024-01-01T00:00:00", False),
            ScanResult("file3.txt", "text", 300, [], 0.1, "2024-01-01T00:00:00", True)
        ]
        
        summary = processor.get_scan_summary(results)
        
        assert summary['total_files_scanned'] == 3
        assert summary['total_pii_entities_found'] == 1
        assert summary['high_risk_files'] == 1
        assert summary['average_risk_score'] == pytest.approx(0.3, abs=0.01)
        assert 'scan_completion_time' in summary
    
    def test_get_scan_summary_empty(self, processor):
        """Test generating scan summary with empty results."""
        summary = processor.get_scan_summary([])
        
        assert summary['total_files_scanned'] == 0
        assert summary['total_pii_entities_found'] == 0
        assert summary['high_risk_files'] == 0
        assert summary['average_risk_score'] == 0.0
    
    def test_sanitize_content(self, processor):
        """Test content sanitization."""
        content = "SSN: 123-45-6789, Email: test@example.com"
        entities = [
            PIIEntity("ssn", "123-45-6789", 0.9, 5, 16, ""),
            PIIEntity("email", "test@example.com", 0.9, 24, 42, "")
        ]
        
        sanitized = processor.sanitize_content(content, entities)
        
        assert "123-45-6789" not in sanitized
        assert "test@example.com" not in sanitized
        assert "SSN: ***********" in sanitized
        assert "Email: ****************" in sanitized
    
    def test_sanitize_content_no_entities(self, processor):
        """Test content sanitization with no entities."""
        content = "No PII here"
        entities = []
        
        sanitized = processor.sanitize_content(content, entities)
        assert sanitized == content
    
    @patch('dlp_processor.datetime')
    def test_get_timestamp(self, mock_datetime, processor):
        """Test timestamp generation."""
        mock_datetime.now.return_value.isoformat.return_value = "2024-01-01T00:00:00"
        
        timestamp = processor._get_timestamp()
        assert timestamp == "2024-01-01T00:00:00"
    
    def test_risk_thresholds(self, processor):
        """Test risk threshold configuration."""
        assert processor.risk_thresholds['low'] == 0.3
        assert processor.risk_thresholds['medium'] == 0.6
        assert processor.risk_thresholds['high'] == 0.8
        
        # Test threshold logic
        assert processor.risk_thresholds['low'] < processor.risk_thresholds['medium']
        assert processor.risk_thresholds['medium'] < processor.risk_thresholds['high']
    
    def test_pii_patterns_validity(self, processor):
        """Test that PII patterns are valid regex."""
        import re
        
        test_content = "123-45-6789"  # Valid SSN
        
        for entity_type, pattern in processor.pii_patterns.items():
            # Ensure pattern compiles
            compiled_pattern = re.compile(pattern)
            # Test with sample data
            assert compiled_pattern.search(test_content) is not None or entity_type != 'ssn'
    
    def test_phi_patterns_validity(self, processor):
        """Test that PHI patterns are valid regex."""
        import re
        
        test_content = "MRN: 12345"  # Valid medical record
        
        for entity_type, pattern in processor.phi_patterns.items():
            # Ensure pattern compiles
            compiled_pattern = re.compile(pattern)
            # Test with sample data
            assert compiled_pattern.search(test_content) is not None or entity_type != 'medical_record'


class TestIntegration:
    """Integration tests for the DLP processor."""
    
    @pytest.fixture
    def processor(self):
        return DLPProcessor()
    
    def test_end_to_end_scanning(self, processor):
        """Test complete end-to-end scanning workflow."""
        # Create test content with multiple PII types
        test_content = """
        Patient Information:
        Name: Jane Smith
        SSN: 987-65-4321
        Email: jane.smith@hospital.com
        Phone: 555-987-6543
        Medical Record: MRN: 123456789
        Diagnosis: ICD-10: B01.1
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file = f.name
        
        try:
            # Scan the file
            result = processor.scan_text_file(temp_file)
            
            # Verify results
            assert result.file_type == "text"
            assert len(result.pii_entities) >= 5  # Should detect multiple entities
            assert result.risk_score > 0.0
            
            # Check specific entity types
            entity_types = [e.entity_type for e in result.pii_entities]
            assert 'ssn' in entity_types
            assert 'email' in entity_types
            assert 'phone' in entity_types
            assert 'medical_record' in entity_types
            assert 'diagnosis' in entity_types
            
            # Test sanitization
            sanitized = processor.sanitize_content(test_content, result.pii_entities)
            assert "987-65-4321" not in sanitized
            assert "jane.smith@hospital.com" not in sanitized
            
        finally:
            os.unlink(temp_file)
    
    def test_multiple_file_types(self, processor):
        """Test scanning multiple file types."""
        # Create text file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("SSN: 111-22-3333")
            text_file = f.name
        
        # Create JSON file
        json_data = {"ssn": "444-55-6666", "email": "test@example.com"}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_file = f.name
        
        try:
            # Scan both files
            text_result = processor.scan_text_file(text_file)
            json_result = processor.scan_json_file(json_file)
            
            # Verify both scans completed
            assert text_result.file_type == "text"
            assert json_result.file_type == "json"
            assert len(text_result.pii_entities) > 0
            assert len(json_result.pii_entities) > 0
            
            # Generate summary
            summary = processor.get_scan_summary([text_result, json_result])
            assert summary['total_files_scanned'] == 2
            assert summary['total_pii_entities_found'] > 0
            
        finally:
            os.unlink(text_file)
            os.unlink(json_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])