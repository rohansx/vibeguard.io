"""
VibeGuard Combined Detector

Combines multiple detection methods for higher accuracy.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from .stylometry import StylometryAnalyzer, analyze_code as analyze_stylometry
from .patterns import PatternDetector, detect_patterns


@dataclass
class DetectionResult:
    ai_probability: float
    confidence: str
    stylometry_score: float
    pattern_score: float
    methods_used: list
    details: dict


class CombinedDetector:
    """
    Combines multiple detection methods:
    1. Stylometry (writing patterns)
    2. Pattern matching (known AI signatures)
    3. Telemetry matching (if available)
    
    Weights:
    - Stylometry: 40%
    - Patterns: 40%
    - Telemetry: 20% (when available)
    """
    
    def __init__(self):
        self.stylometry = StylometryAnalyzer()
        self.patterns = PatternDetector()
        
        # Weights for combining scores
        self.weights = {
            'stylometry': 0.45,
            'patterns': 0.45,
            'telemetry': 0.10  # Bonus when telemetry matches
        }
    
    def detect(
        self,
        code: str,
        language: str = "auto",
        telemetry_hash: Optional[str] = None
    ) -> DetectionResult:
        """
        Run combined detection on code.
        
        Args:
            code: Source code to analyze
            language: Programming language (auto-detected if not specified)
            telemetry_hash: Optional hash from IDE telemetry for matching
            
        Returns:
            DetectionResult with combined score and details
        """
        methods_used = []
        
        # Run stylometry analysis
        style_features = self.stylometry.analyze(code, language)
        style_score = self.stylometry.calculate_ai_probability(style_features)
        methods_used.append("stylometry")
        
        # Run pattern detection
        pattern_result = self.patterns.detect(code)
        pattern_score = pattern_result['pattern_score']
        methods_used.append("pattern_matching")
        
        # Check telemetry if hash provided
        telemetry_score = 0
        telemetry_match = False
        if telemetry_hash:
            telemetry_match = self._check_telemetry(telemetry_hash)
            if telemetry_match:
                telemetry_score = 1.0
                methods_used.append("telemetry")
        
        # Combine scores
        if telemetry_match:
            # If telemetry confirms AI, heavily weight it
            combined = (
                style_score * 0.30 +
                pattern_score * 0.30 +
                telemetry_score * 0.40
            )
        else:
            # Without telemetry, split between stylometry and patterns
            combined = (
                style_score * self.weights['stylometry'] +
                pattern_score * self.weights['patterns']
            ) / (self.weights['stylometry'] + self.weights['patterns'])
        
        # Determine confidence level
        if combined > 0.85:
            confidence = "very_high"
        elif combined > 0.7:
            confidence = "high"
        elif combined > 0.5:
            confidence = "medium"
        elif combined > 0.3:
            confidence = "low"
        else:
            confidence = "very_low"
        
        return DetectionResult(
            ai_probability=round(combined, 3),
            confidence=confidence,
            stylometry_score=round(style_score, 3),
            pattern_score=round(pattern_score, 3),
            methods_used=methods_used,
            details={
                'stylometry': {
                    'score': round(style_score, 3),
                    'features': {
                        'naming_consistency': round(style_features.naming_consistency, 3),
                        'comment_density': round(style_features.comment_density, 3),
                        'indentation_consistency': round(style_features.indentation_consistency, 3),
                        'boilerplate_ratio': round(style_features.boilerplate_ratio, 3),
                    }
                },
                'patterns': {
                    'score': round(pattern_score, 3),
                    'patterns_matched': pattern_result['patterns_matched'],
                    'top_patterns': pattern_result['matches'][:5] if pattern_result['matches'] else []
                },
                'telemetry': {
                    'matched': telemetry_match,
                    'hash': telemetry_hash
                } if telemetry_hash else None
            }
        )
    
    def _check_telemetry(self, code_hash: str) -> bool:
        """
        Check if code hash matches known AI-generated code.
        
        In production, this would query a database of telemetry events
        from IDE extensions.
        """
        # TODO: Implement telemetry database lookup
        return False


def analyze(
    code: str,
    language: str = "auto",
    telemetry_hash: Optional[str] = None
) -> Dict:
    """
    Analyze code for AI generation.
    
    Args:
        code: Source code to analyze
        language: Programming language
        telemetry_hash: Optional IDE telemetry hash
        
    Returns:
        Dict with analysis results
    """
    detector = CombinedDetector()
    result = detector.detect(code, language, telemetry_hash)
    
    return {
        'ai_probability': result.ai_probability,
        'confidence': result.confidence,
        'stylometry_score': result.stylometry_score,
        'pattern_score': result.pattern_score,
        'methods_used': result.methods_used,
        'details': result.details
    }


def analyze_file(file_path: str) -> Dict:
    """Analyze a file for AI generation."""
    with open(file_path, 'r') as f:
        code = f.read()
    
    # Detect language from extension
    ext = file_path.split('.')[-1] if '.' in file_path else ''
    lang_map = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'tsx': 'typescript',
        'jsx': 'javascript',
        'go': 'go',
        'rs': 'rust',
        'java': 'java',
        'kt': 'kotlin',
        'rb': 'ruby',
        'php': 'php',
    }
    language = lang_map.get(ext, 'auto')
    
    result = analyze(code, language)
    result['file_path'] = file_path
    result['language'] = language
    
    return result


if __name__ == "__main__":
    # Test combined detection
    sample_ai = '''
async function fetchUserData(userId: string): Promise<User> {
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch user data');
        }
        const data = await response.json();
        return data as User;
    } catch (error) {
        console.error('Error fetching user:', error);
        throw error;
    }
}
'''
    
    sample_human = '''
// get user - quick and dirty
async function getUser(id) {
  const r = await fetch('/api/u/' + id)
  if (!r.ok) throw 'nope'
  return r.json()
}
'''
    
    print("AI-like code:")
    result = analyze(sample_ai, "typescript")
    print(f"  Probability: {result['ai_probability']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Stylometry: {result['stylometry_score']}")
    print(f"  Patterns: {result['pattern_score']}")
    
    print("\nHuman-like code:")
    result = analyze(sample_human, "javascript")
    print(f"  Probability: {result['ai_probability']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Stylometry: {result['stylometry_score']}")
    print(f"  Patterns: {result['pattern_score']}")
