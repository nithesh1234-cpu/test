#!/usr/bin/env python3
"""
Example usage of the DLP Processor.
This script demonstrates how to use the DLP processor to scan files for PII/PHI.
"""

import json
from dlp_processor import DLPProcessor, ScanResult


def main():
    """Main example function."""
    print("🔍 DLP Processor Example Usage")
    print("=" * 40)
    
    # Initialize the processor
    processor = DLPProcessor()
    
    # Example 1: Scan text content directly
    print("\n📝 Example 1: Scanning text content")
    sample_text = """
    Customer Information:
    Name: John Doe
    SSN: 123-45-6789
    Email: john.doe@example.com
    Phone: 555-123-4567
    Credit Card: 1234-5678-9012-3456
    """
    
    entities = processor._detect_pii_in_text(sample_text)
    print(f"Found {len(entities)} PII entities:")
    for entity in entities:
        print(f"  - {entity.entity_type}: {entity.value} (confidence: {entity.confidence})")
    
    # Example 2: Risk scoring
    print("\n⚠️ Example 2: Risk scoring")
    risk_score = processor._calculate_risk_score(entities, len(sample_text))
    print(f"Risk score: {risk_score}")
    print(f"Risk level: {'High' if risk_score >= 0.8 else 'Medium' if risk_score >= 0.6 else 'Low'}")
    
    # Example 3: Content sanitization
    print("\n🔒 Example 3: Content sanitization")
    sanitized = processor.sanitize_content(sample_text, entities)
    print("Sanitized content:")
    print(sanitized)
    
    # Example 4: Create a temporary file and scan it
    print("\n📁 Example 4: File scanning")
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_text)
        temp_file = f.name
    
    try:
        result = processor.scan_text_file(temp_file)
        print(f"File scan result:")
        print(f"  - File: {result.file_path}")
        print(f"  - Type: {result.file_type}")
        print(f"  - Size: {result.file_size} bytes")
        print(f"  - PII entities found: {len(result.pii_entities)}")
        print(f"  - Risk score: {result.risk_score}")
        print(f"  - Is safe: {result.is_safe}")
        print(f"  - Timestamp: {result.scan_timestamp}")
    finally:
        os.unlink(temp_file)
    
    # Example 5: JSON data scanning
    print("\n📊 Example 5: JSON data scanning")
    sample_json = {
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
        json.dump(sample_json, f, indent=2)
        temp_json_file = f.name
    
    try:
        json_result = processor.scan_json_file(temp_json_file)
        print(f"JSON scan result:")
        print(f"  - PII entities found: {len(json_result.pii_entities)}")
        print(f"  - Risk score: {json_result.risk_score}")
        
        # Show detected entities
        for entity in json_result.pii_entities:
            print(f"    - {entity.entity_type}: {entity.value}")
    finally:
        os.unlink(temp_json_file)
    
    # Example 6: Batch processing simulation
    print("\n🔄 Example 6: Batch processing simulation")
    mock_results = [
        ScanResult("file1.txt", "text", 100, [], 0.0, "2024-01-01T00:00:00", True),
        ScanResult("file2.txt", "text", 200, entities[:1], 0.5, "2024-01-01T00:00:00", True),
        ScanResult("file3.txt", "text", 300, entities, 0.8, "2024-01-01T00:00:00", False)
    ]
    
    summary = processor.get_scan_summary(mock_results)
    print("Batch scan summary:")
    for key, value in summary.items():
        print(f"  - {key}: {value}")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()