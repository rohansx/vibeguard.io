"""
VibeGuard Pattern Detector

Detects known AI code patterns and signatures.
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class PatternMatch:
    pattern_name: str
    confidence: float
    line_start: int
    line_end: int
    snippet: str


class PatternDetector:
    """
    Detects AI code patterns.
    
    AI-generated code often has recognizable patterns:
    - Formulaic error handling
    - Standard boilerplate structures
    - Characteristic comment styles
    - Consistent naming patterns
    """
    
    def __init__(self):
        self.patterns = self._build_patterns()
    
    def _build_patterns(self) -> List[Tuple[str, str, float]]:
        """Build pattern list: (name, regex, confidence_weight)"""
        return [
            # Error handling patterns
            (
                "copilot_try_catch",
                r'try\s*\{[^}]+\}\s*catch\s*\(\s*(?:error|err|e)\s*(?::\s*\w+)?\s*\)\s*\{[^}]*(?:console\.(?:error|log)|throw)[^}]*\}',
                0.15
            ),
            (
                "standard_error_throw",
                r"throw\s+new\s+Error\s*\(\s*['\"`](?:Failed to|Unable to|Error|Invalid|Cannot)[^'\"`]+['\"`]\s*\)",
                0.12
            ),
            
            # Async patterns
            (
                "async_await_fetch",
                r"async\s+(?:function\s+)?\w+\s*\([^)]*\)\s*(?::\s*Promise<[^>]+>)?\s*\{[^}]*await\s+fetch",
                0.10
            ),
            (
                "promise_chain",
                r"\.then\s*\(\s*(?:\([^)]*\)|[a-z]+)\s*=>\s*\{?[^}]*\}\s*\)\s*\.catch",
                0.08
            ),
            
            # Comment patterns
            (
                "jsdoc_complete",
                r'/\*\*\s*\n(?:\s*\*\s*@\w+[^\n]*\n)+\s*\*/',
                0.10
            ),
            (
                "inline_explanation",
                r'//\s*[A-Z][a-z]+(?:\s+[a-z]+){3,}',
                0.08
            ),
            
            # Variable patterns
            (
                "descriptive_const",
                r"const\s+[a-z]+(?:[A-Z][a-z]+){2,}\s*=",
                0.06
            ),
            (
                "response_data_pattern",
                r"(?:const|let)\s+(?:response|data|result)\s*=\s*await",
                0.08
            ),
            
            # Function patterns
            (
                "arrow_with_types",
                r"const\s+\w+\s*=\s*(?:async\s*)?\([^)]*:\s*\w+[^)]*\)\s*(?::\s*\w+(?:<[^>]+>)?)?\s*=>",
                0.10
            ),
            (
                "export_default_function",
                r"export\s+default\s+(?:async\s+)?function\s+\w+",
                0.06
            ),
            
            # React patterns
            (
                "use_effect_deps",
                r"useEffect\s*\(\s*\(\s*\)\s*=>\s*\{[^}]+\}\s*,\s*\[[^\]]*\]\s*\)",
                0.08
            ),
            (
                "use_state_destructure",
                r"const\s*\[\s*\w+\s*,\s*set[A-Z]\w+\s*\]\s*=\s*useState",
                0.08
            ),
            
            # Import patterns
            (
                "grouped_imports",
                r"import\s*\{[^}]{20,}\}\s*from\s*['\"][^'\"]+['\"]",
                0.05
            ),
            
            # Type patterns
            (
                "interface_complete",
                r"interface\s+\w+\s*\{(?:\s*\w+\s*:\s*\w+(?:<[^>]+>)?;?\s*){3,}\}",
                0.08
            ),
            (
                "type_alias",
                r"type\s+\w+\s*=\s*\{(?:\s*\w+\s*:\s*\w+(?:<[^>]+>)?;?\s*){2,}\}",
                0.06
            ),
            
            # Python patterns
            (
                "python_docstring",
                r'"""[^"]+(?:Args:|Returns:|Raises:)[^"]+"""',
                0.10
            ),
            (
                "python_type_hints",
                r"def\s+\w+\s*\([^)]*:\s*\w+[^)]*\)\s*->\s*\w+:",
                0.08
            ),
            (
                "python_try_except",
                r"try:\s*\n[^e]+except\s+\w+(?:\s+as\s+\w+)?:\s*\n",
                0.10
            ),
            
            # Go patterns
            (
                "go_error_check",
                r"if\s+err\s*!=\s*nil\s*\{[^}]*return[^}]*\}",
                0.12
            ),
            (
                "go_defer",
                r"defer\s+(?:\w+\.)?(?:Close|Unlock|Done)\s*\(\s*\)",
                0.08
            ),
            
            # Generic AI signatures
            (
                "numbered_steps",
                r"//\s*(?:Step\s+)?\d+[.:]\s*[A-Z]",
                0.06
            ),
            (
                "todo_ai_style",
                r"//\s*TODO:\s*[A-Z][a-z]+\s+[a-z]+",
                0.05
            ),
        ]
    
    def detect(self, code: str) -> Dict:
        """
        Detect AI patterns in code.
        
        Returns:
            Dict with pattern matches and overall score
        """
        matches: List[PatternMatch] = []
        total_weight = 0
        lines = code.split('\n')
        
        for name, pattern, weight in self.patterns:
            for match in re.finditer(pattern, code, re.MULTILINE | re.DOTALL):
                # Find line numbers
                start_pos = match.start()
                end_pos = match.end()
                
                start_line = code[:start_pos].count('\n') + 1
                end_line = code[:end_pos].count('\n') + 1
                
                snippet = match.group(0)[:100]
                if len(match.group(0)) > 100:
                    snippet += "..."
                
                matches.append(PatternMatch(
                    pattern_name=name,
                    confidence=weight,
                    line_start=start_line,
                    line_end=end_line,
                    snippet=snippet
                ))
                total_weight += weight
        
        # Normalize score (cap at 1.0)
        pattern_score = min(total_weight, 1.0)
        
        return {
            "pattern_score": round(pattern_score, 3),
            "patterns_matched": len(matches),
            "matches": [
                {
                    "pattern": m.pattern_name,
                    "confidence": m.confidence,
                    "lines": f"{m.line_start}-{m.line_end}",
                    "snippet": m.snippet
                }
                for m in matches
            ],
            "method": "pattern_matching"
        }


def detect_patterns(code: str) -> Dict:
    """Convenience function to detect patterns."""
    detector = PatternDetector()
    return detector.detect(code)


if __name__ == "__main__":
    sample = '''
import { useState, useEffect } from 'react';

interface User {
    id: string;
    name: string;
    email: string;
}

/**
 * Fetches user data from the API
 * @param userId - The user ID to fetch
 * @returns Promise resolving to user data
 */
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

export default function UserProfile({ userId }: { userId: string }) {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        fetchUserData(userId)
            .then(data => setUser(data))
            .finally(() => setLoading(false));
    }, [userId]);
    
    if (loading) return <div>Loading...</div>;
    if (!user) return <div>User not found</div>;
    
    return (
        <div>
            <h1>{user.name}</h1>
            <p>{user.email}</p>
        </div>
    );
}
'''
    
    result = detect_patterns(sample)
    print(f"Pattern Score: {result['pattern_score']}")
    print(f"Patterns Matched: {result['patterns_matched']}")
    for m in result['matches']:
        print(f"  - {m['pattern']} (confidence: {m['confidence']})")
