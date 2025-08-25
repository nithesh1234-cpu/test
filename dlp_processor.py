import re
import json
import hashlib
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PIIEntity:
    """Represents a detected PII entity."""
    entity_type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    context: str


@dataclass
class ScanResult:
    """Represents the result of a DLP scan."""
    file_path: str
    file_type: str
    file_size: int
    pii_entities: List[PIIEntity]
    risk_score: float
    scan_timestamp: str
    is_safe: bool


class DLPProcessor:
    """Main DLP processor for detecting PII/PHI in various file types."""
    
    def __init__(self):
        self.pii_patterns = {
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ip_address': r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',
            'date_of_birth': r'\b(0[1-9]|1[0-2])[/-](0[1-9]|[12]\d|3[01])[/-]\d{4}\b'
        }
        
        self.phi_patterns = {
            'medical_record': r'\bMRN[:\s]*\d+\b',
            'diagnosis': r'\b(ICD|ICD-10|ICD-9)[:\s]*[A-Z]\d{2}\.?\d*\b',
            'prescription': r'\bRX[:\s]*\d+\b',
            'patient_id': r'\bPID[:\s]*\d+\b'
        }
        
        self.risk_thresholds = {
            'low': 0.3,
            'medium': 0.6,
            'high': 0.8
        }
    
    def scan_text_file(self, file_path: str) -> ScanResult:
        """Scan a text file for PII/PHI content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            pii_entities = self._detect_pii_in_text(content)
            risk_score = self._calculate_risk_score(pii_entities, len(content))
            
            return ScanResult(
                file_path=file_path,
                file_type='text',
                file_size=len(content),
                pii_entities=pii_entities,
                risk_score=risk_score,
                scan_timestamp=self._get_timestamp(),
                is_safe=risk_score < self.risk_thresholds['medium']
            )
        except Exception as e:
            raise ValueError(f"Error scanning file {file_path}: {str(e)}")
    
    def scan_json_file(self, file_path: str) -> ScanResult:
        """Scan a JSON file for PII/PHI content."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            content = json.dumps(data, indent=2)
            pii_entities = self._detect_pii_in_text(content)
            risk_score = self._calculate_risk_score(pii_entities, len(content))
            
            return ScanResult(
                file_path=file_path,
                file_type='json',
                file_size=len(content),
                pii_entities=pii_entities,
                risk_score=risk_score,
                scan_timestamp=self._get_timestamp(),
                is_safe=risk_score < self.risk_thresholds['medium']
            )
        except Exception as e:
            raise ValueError(f"Error scanning JSON file {file_path}: {str(e)}")
    
    def scan_pdf_file(self, file_path: str) -> ScanResult:
        """Scan a PDF file for PII/PHI content."""
        # This is a simplified version - in practice you'd use PyPDF2 or similar
        try:
            # Simulate PDF scanning
            file_size = Path(file_path).stat().st_size
            pii_entities = self._detect_pii_in_pdf(file_path)
            risk_score = self._calculate_risk_score(pii_entities, file_size)
            
            return ScanResult(
                file_path=file_path,
                file_type='pdf',
                file_size=file_size,
                pii_entities=pii_entities,
                risk_score=risk_score,
                scan_timestamp=self._get_timestamp(),
                is_safe=risk_score < self.risk_thresholds['medium']
            )
        except Exception as e:
            raise ValueError(f"Error scanning PDF file {file_path}: {str(e)}")
    
    def _detect_pii_in_text(self, content: str) -> List[PIIEntity]:
        """Detect PII entities in text content."""
        entities = []
        
        # Check all PII patterns
        for entity_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                start, end = match.span()
                context = content[max(0, start-20):min(len(content), end+20)]
                
                entities.append(PIIEntity(
                    entity_type=entity_type,
                    value=match.group(),
                    confidence=0.9,  # High confidence for regex matches
                    start_pos=start,
                    end_pos=end,
                    context=context
                ))
        
        # Check all PHI patterns
        for entity_type, pattern in self.phi_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                start, end = match.span()
                context = content[max(0, start-20):min(len(content), end+20)]
                
                entities.append(PIIEntity(
                    entity_type=entity_type,
                    value=match.group(),
                    confidence=0.85,  # Slightly lower for PHI patterns
                    start_pos=start,
                    end_pos=end,
                    context=context
                ))
        
        return entities
    
    def _detect_pii_in_pdf(self, file_path: str) -> List[PIIEntity]:
        """Detect PII entities in PDF content (simplified)."""
        # In practice, you'd extract text from PDF first
        # For now, return empty list to simulate no PII found
        return []
    
    def _calculate_risk_score(self, entities: List[PIIEntity], content_length: int) -> float:
        """Calculate risk score based on detected entities and content size."""
        if not entities:
            return 0.0
        
        # Base score from entity count and types
        entity_score = len(entities) * 0.1
        
        # Bonus for high-risk entity types
        high_risk_types = {'ssn', 'credit_card', 'medical_record'}
        high_risk_bonus = sum(0.2 for entity in entities if entity.entity_type in high_risk_types)
        
        # Normalize by content length
        length_factor = min(1.0, content_length / 10000)
        
        risk_score = min(1.0, (entity_score + high_risk_bonus) * length_factor)
        return round(risk_score, 3)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_scan_summary(self, results: List[ScanResult]) -> Dict:
        """Generate a summary of multiple scan results."""
        total_files = len(results)
        total_pii = sum(len(result.pii_entities) for result in results)
        high_risk_files = sum(1 for result in results if result.risk_score >= self.risk_thresholds['high'])
        
        return {
            'total_files_scanned': total_files,
            'total_pii_entities_found': total_pii,
            'high_risk_files': high_risk_files,
            'average_risk_score': round(sum(result.risk_score for result in results) / total_files, 3) if total_files > 0 else 0.0,
            'scan_completion_time': self._get_timestamp()
        }
    
    def validate_file_path(self, file_path: str) -> bool:
        """Validate if file path exists and is accessible."""
        try:
            path = Path(file_path)
            return path.exists() and path.is_file() and path.stat().st_size > 0
        except Exception:
            return False
    
    def sanitize_content(self, content: str, entities: List[PIIEntity]) -> str:
        """Sanitize content by masking detected PII entities."""
        sanitized = content
        # Sort entities by position in reverse order to avoid index shifting
        sorted_entities = sorted(entities, key=lambda x: x.start_pos, reverse=True)
        
        for entity in sorted_entities:
            mask = '*' * len(entity.value)
            sanitized = sanitized[:entity.start_pos] + mask + sanitized[entity.end_pos:]
        
        return sanitized