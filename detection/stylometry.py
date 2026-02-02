"""
VibeGuard Stylometry Analyzer

Analyzes code style patterns that indicate AI generation.

AI-generated code tends to have:
- High naming consistency (camelCase everywhere, or snake_case everywhere)
- Moderate, formulaic comments
- Consistent line lengths
- Perfect indentation
- Higher boilerplate ratio
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional
import statistics


@dataclass
class StyleFeatures:
    naming_consistency: float      # 0-1, higher = more consistent (AI signal)
    comment_density: float         # comments per line
    avg_line_length: float         # average characters per line
    line_length_variance: float    # variance in line lengths
    indentation_consistency: float # 0-1, higher = more consistent
    boilerplate_ratio: float       # common patterns ratio
    empty_line_ratio: float        # empty lines / total lines
    max_nesting_depth: int         # deepest nesting level


class StylometryAnalyzer:
    """
    Analyzes code style patterns to detect AI-generated code.
    """
    
    def __init__(self):
        self.boilerplate_patterns = [
            r'try\s*\{[\s\S]*?catch',
            r'if\s*\(\s*!\s*\w+\s*\)\s*\{?\s*return',
            r'async\s+function\s+\w+\s*\([^)]*\)\s*\{',
            r'const\s+\w+\s*=\s*async\s*\([^)]*\)\s*=>',
            r'export\s+(default\s+)?(function|class|const)',
            r'import\s+\{[^}]+\}\s+from',
            r'@\w+\([^)]*\)',  # Decorators
            r'public\s+(static\s+)?(async\s+)?\w+\s*\(',  # Method signatures
            r'private\s+(readonly\s+)?\w+:\s*\w+',  # Private fields
            r'interface\s+\w+\s*\{',  # Interface definitions
            r'type\s+\w+\s*=\s*\{',  # Type definitions
        ]
        
        self.ai_comment_patterns = [
            r'//\s*TODO:?\s*\w+',
            r'//\s*[A-Z][a-z]+\s+[a-z]+',  # Sentence-like comments
            r'/\*\*[\s\S]*?\*/',  # JSDoc blocks
            r'#\s*[A-Z][a-z]+',  # Python comments starting with capital
        ]

    def analyze(self, code: str, language: str = "auto") -> StyleFeatures:
        """
        Analyze code and extract style features.
        
        Args:
            code: Source code to analyze
            language: Programming language (auto-detected if not specified)
            
        Returns:
            StyleFeatures dataclass with extracted features
        """
        lines = code.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        return StyleFeatures(
            naming_consistency=self._analyze_naming(code),
            comment_density=self._analyze_comments(lines, language),
            avg_line_length=self._avg_line_length(non_empty_lines),
            line_length_variance=self._line_length_variance(non_empty_lines),
            indentation_consistency=self._analyze_indentation(lines),
            boilerplate_ratio=self._analyze_boilerplate(code),
            empty_line_ratio=self._empty_line_ratio(lines),
            max_nesting_depth=self._max_nesting_depth(code)
        )

    def _analyze_naming(self, code: str) -> float:
        """
        AI tends to be very consistent with naming conventions.
        Humans mix styles more often.
        """
        # Extract identifiers (simplified)
        identifiers = re.findall(r'\b([a-z][a-zA-Z0-9_]*)\b', code)
        
        if len(identifiers) < 5:
            return 0.5
        
        camel_case = sum(1 for i in identifiers if re.match(r'^[a-z]+([A-Z][a-z]*)*$', i))
        snake_case = sum(1 for i in identifiers if '_' in i and i.islower())
        
        total = len(identifiers)
        dominant_style_ratio = max(camel_case, snake_case) / total
        
        # High consistency (>0.9) suggests AI
        return dominant_style_ratio

    def _analyze_comments(self, lines: List[str], language: str) -> float:
        """AI typically adds moderate, formulaic comments."""
        comment_markers = {
            'python': ['#'],
            'javascript': ['//', '/*'],
            'typescript': ['//', '/*'],
            'go': ['//', '/*'],
            'java': ['//', '/*'],
            'auto': ['//', '#', '/*']
        }
        
        markers = comment_markers.get(language, comment_markers['auto'])
        comment_lines = sum(
            1 for l in lines 
            if any(l.strip().startswith(m) for m in markers)
        )
        
        return comment_lines / max(len(lines), 1)

    def _avg_line_length(self, lines: List[str]) -> float:
        """AI tends toward consistent line lengths (~45-80 chars)."""
        lengths = [len(l) for l in lines if l.strip()]
        return statistics.mean(lengths) if lengths else 0

    def _line_length_variance(self, lines: List[str]) -> float:
        """Low variance in line length is an AI signal."""
        lengths = [len(l) for l in lines if l.strip()]
        if len(lengths) < 2:
            return 0
        return statistics.stdev(lengths)

    def _analyze_indentation(self, lines: List[str]) -> float:
        """AI has perfect indentation consistency."""
        indents = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indents.append(indent)
        
        if not indents:
            return 0.5
        
        # Check if indentation follows consistent pattern (2 or 4 spaces)
        indent_unit = 2 if any(i % 2 == 0 and i % 4 != 0 for i in indents) else 4
        consistent = sum(1 for i in indents if i % indent_unit == 0)
        
        return consistent / len(indents)

    def _analyze_boilerplate(self, code: str) -> float:
        """AI generates more standard patterns."""
        matches = sum(len(re.findall(p, code)) for p in self.boilerplate_patterns)
        lines = len(code.split('\n'))
        return min(matches / max(lines / 10, 1), 1.0)

    def _empty_line_ratio(self, lines: List[str]) -> float:
        """AI tends to add consistent spacing."""
        empty = sum(1 for l in lines if not l.strip())
        return empty / max(len(lines), 1)

    def _max_nesting_depth(self, code: str) -> int:
        """Calculate maximum nesting depth."""
        max_depth = 0
        current_depth = 0
        
        for char in code:
            if char in '{[(':
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char in '}])':
                current_depth = max(0, current_depth - 1)
        
        return max_depth

    def calculate_ai_probability(self, features: StyleFeatures) -> float:
        """
        Weighted combination of features.
        Returns probability that code is AI-generated (0-1).
        """
        weights = {
            'naming_consistency': 0.20,
            'indentation_consistency': 0.20,
            'boilerplate_ratio': 0.20,
            'comment_density': 0.10,
            'line_length_variance': 0.15,
            'empty_line_ratio': 0.10,
            'nesting_depth': 0.05
        }
        
        # Transform features to AI probability signals
        signals = {
            'naming_consistency': features.naming_consistency,  # High = AI
            'indentation_consistency': features.indentation_consistency,  # High = AI
            'boilerplate_ratio': features.boilerplate_ratio,  # High = AI
            'comment_density': 1 - abs(features.comment_density - 0.15) * 5,  # ~15% is AI-like
            'line_length_variance': max(0, 1 - features.line_length_variance / 30),  # Low variance = AI
            'empty_line_ratio': 1 - abs(features.empty_line_ratio - 0.15) * 5,  # ~15% is AI-like
            'nesting_depth': max(0, 1 - features.max_nesting_depth / 10)  # Shallow = AI
        }
        
        # Clip signals to [0, 1]
        signals = {k: max(0, min(1, v)) for k, v in signals.items()}
        
        probability = sum(signals[k] * weights[k] for k in weights)
        return probability


def analyze_code(code: str, language: str = "auto") -> Dict:
    """
    Convenience function to analyze code and return results as dict.
    """
    analyzer = StylometryAnalyzer()
    features = analyzer.analyze(code, language)
    probability = analyzer.calculate_ai_probability(features)
    
    return {
        "ai_probability": round(probability, 3),
        "confidence": "high" if probability > 0.8 else "medium" if probability > 0.5 else "low",
        "features": {
            "naming_consistency": round(features.naming_consistency, 3),
            "comment_density": round(features.comment_density, 3),
            "avg_line_length": round(features.avg_line_length, 1),
            "line_length_variance": round(features.line_length_variance, 1),
            "indentation_consistency": round(features.indentation_consistency, 3),
            "boilerplate_ratio": round(features.boilerplate_ratio, 3),
            "empty_line_ratio": round(features.empty_line_ratio, 3),
            "max_nesting_depth": features.max_nesting_depth
        },
        "method": "stylometry"
    }


if __name__ == "__main__":
    # Test with sample code
    sample_ai_code = '''
async function fetchUserData(userId: string): Promise<User> {
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch user');
        }
        const data = await response.json();
        return data as User;
    } catch (error) {
        console.error('Error fetching user:', error);
        throw error;
    }
}

export default fetchUserData;
'''
    
    sample_human_code = '''
// TODO fix this later
async function getUser(id) {
  const r = await fetch('/api/users/' + id)
  if(!r.ok) throw 'nope'
  return r.json()
}

module.exports = { getUser }
'''
    
    print("AI-like code:")
    print(analyze_code(sample_ai_code))
    print("\nHuman-like code:")
    print(analyze_code(sample_human_code))
