"""
VGX Security Scanner

Pattern-based security vulnerability detection.
"""

import re
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class SecurityIssue:
    severity: str  # critical, high, medium, low
    type: str
    message: str
    line: int
    column: int
    code_snippet: str


# Security patterns
SECURITY_PATTERNS = {
    'hardcoded_secret': {
        'severity': 'critical',
        'patterns': [
            r'(?i)(api[_-]?key|apikey|secret[_-]?key|secretkey|auth[_-]?token|password|passwd|pwd)\s*[=:]\s*["\'][^"\']{8,}["\']',
            r'(?i)(aws[_-]?access[_-]?key|aws[_-]?secret)\s*[=:]\s*["\'][A-Za-z0-9+/=]{20,}["\']',
            r'(?i)bearer\s+[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+',
            r'(?i)(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}',  # GitHub tokens
            r'sk-[a-zA-Z0-9]{48}',  # OpenAI keys
            r'(?i)private[_-]?key\s*[=:]\s*["\']-----BEGIN',
        ],
        'message': 'Hardcoded secret detected',
    },
    'sql_injection': {
        'severity': 'high',
        'patterns': [
            r'(?i)(execute|query|raw)\s*\(\s*["\']?\s*SELECT.*\+',
            r'(?i)(execute|query|raw)\s*\(\s*f["\'].*SELECT',
            r'(?i)cursor\.(execute|executemany)\s*\(\s*["\'].*%s.*%s',
            r'(?i)\.query\s*\(\s*`[^`]*\$\{',  # Template literal SQL
            r'(?i)SELECT\s+.*\s+FROM\s+.*\s+WHERE\s+.*\s*\+\s*(?:req|request|params|body|query)',
        ],
        'message': 'Potential SQL injection vulnerability',
    },
    'xss': {
        'severity': 'high',
        'patterns': [
            r'(?i)innerHTML\s*=\s*(?![\'"]\s*[\'"])',
            r'(?i)document\.write\s*\(',
            r'(?i)\.html\s*\(\s*(?:req|request|params|data|input)',
            r'(?i)dangerouslySetInnerHTML',
            r'(?i)v-html\s*=',
        ],
        'message': 'Potential XSS vulnerability',
    },
    'path_traversal': {
        'severity': 'high',
        'patterns': [
            r'(?i)(open|readFile|readFileSync|createReadStream)\s*\(\s*(?:req|request|params)',
            r'(?i)path\.join\s*\([^)]*(?:req|request|params|body|query)',
            r'(?i)\.\./',
        ],
        'message': 'Potential path traversal vulnerability',
    },
    'insecure_random': {
        'severity': 'medium',
        'patterns': [
            r'Math\.random\s*\(\s*\)',
            r'(?i)random\.random\s*\(\s*\)',
            r'(?i)rand\s*\(\s*\)',
        ],
        'message': 'Insecure random number generator (use crypto module for security)',
    },
    'eval_usage': {
        'severity': 'high',
        'patterns': [
            r'\beval\s*\(',
            r'(?i)exec\s*\(\s*(?:req|request|params|input)',
            r'Function\s*\(\s*["\']',
            r'(?i)subprocess\.(?:call|run|Popen)\s*\(\s*(?:req|request|params|input|shell\s*=\s*True)',
        ],
        'message': 'Dangerous eval/exec usage detected',
    },
    'weak_crypto': {
        'severity': 'medium',
        'patterns': [
            r'(?i)md5\s*\(',
            r'(?i)sha1\s*\(',
            r'(?i)createHash\s*\(\s*["\']md5["\']',
            r'(?i)createHash\s*\(\s*["\']sha1["\']',
            r'(?i)DES|3DES|RC4',
        ],
        'message': 'Weak cryptographic algorithm detected',
    },
    'cors_wildcard': {
        'severity': 'medium',
        'patterns': [
            r'(?i)Access-Control-Allow-Origin["\']?\s*[,:]\s*["\']?\*',
            r'(?i)cors\s*\(\s*\{\s*origin\s*:\s*["\']?\*',
        ],
        'message': 'CORS wildcard allows any origin',
    },
}


def scan_code(code: str, language: str = "auto") -> Dict[str, Any]:
    """
    Scan code for security vulnerabilities.
    
    Args:
        code: Source code to scan
        language: Programming language
        
    Returns:
        Dict with security scan results
    """
    issues: List[Dict] = []
    lines = code.split('\n')
    
    for vuln_type, config in SECURITY_PATTERNS.items():
        for pattern in config['patterns']:
            try:
                for match in re.finditer(pattern, code):
                    # Find line number
                    start = match.start()
                    line_num = code[:start].count('\n') + 1
                    
                    # Get code snippet
                    if line_num <= len(lines):
                        snippet = lines[line_num - 1].strip()
                    else:
                        snippet = match.group(0)[:50]
                    
                    issues.append({
                        'type': vuln_type,
                        'severity': config['severity'],
                        'message': config['message'],
                        'line': line_num,
                        'column': match.start() - code.rfind('\n', 0, start),
                        'snippet': snippet[:100],
                    })
            except re.error:
                continue
    
    # Deduplicate by line
    seen = set()
    unique_issues = []
    for issue in issues:
        key = (issue['type'], issue['line'])
        if key not in seen:
            seen.add(key)
            unique_issues.append(issue)
    
    # Sort by severity
    severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    unique_issues.sort(key=lambda x: severity_order.get(x['severity'], 4))
    
    # Summary
    critical = sum(1 for i in unique_issues if i['severity'] == 'critical')
    high = sum(1 for i in unique_issues if i['severity'] == 'high')
    medium = sum(1 for i in unique_issues if i['severity'] == 'medium')
    low = sum(1 for i in unique_issues if i['severity'] == 'low')
    
    return {
        'issues': unique_issues,
        'summary': {
            'total': len(unique_issues),
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low,
        },
        'passed': len(unique_issues) == 0,
    }


if __name__ == "__main__":
    # Test security scanning
    test_code = '''
const API_KEY = "sk-1234567890abcdefghijklmnopqrstuvwxyz12345678";

async function getUser(id) {
    const query = "SELECT * FROM users WHERE id = " + id;
    const result = await db.query(query);
    document.innerHTML = result.name;
    return result;
}

function generateToken() {
    return Math.random().toString(36);
}
'''
    
    result = scan_code(test_code, "javascript")
    print(f"Found {result['summary']['total']} issues:")
    for issue in result['issues']:
        print(f"  [{issue['severity'].upper()}] {issue['message']} (line {issue['line']})")
