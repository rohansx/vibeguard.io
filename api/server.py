"""
VibeGuard API Server

Main API server for the VibeGuard compliance platform.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from detection.stylometry import analyze_code, StylometryAnalyzer
from policy.engine import PolicyEngine, evaluate_commit, EXAMPLE_CONFIG

app = Flask(__name__)
CORS(app)

# Initialize components
stylometry = StylometryAnalyzer()
policy_engine = PolicyEngine(EXAMPLE_CONFIG)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'service': 'vibeguard',
        'version': '0.1.0'
    })


@app.route('/api/v1/analyze', methods=['POST'])
def analyze():
    """
    Analyze code for AI generation probability.
    
    Request body:
    {
        "code": "function foo() { ... }",
        "language": "typescript",  // optional
        "filename": "src/utils.ts"  // optional
    }
    """
    data = request.get_json()
    
    if not data or 'code' not in data:
        return jsonify({'error': 'Missing "code" in request body'}), 400
    
    code = data['code']
    language = data.get('language', 'auto')
    filename = data.get('filename', 'unknown')
    
    result = analyze_code(code, language)
    result['filename'] = filename
    
    return jsonify(result)


@app.route('/api/v1/analyze/batch', methods=['POST'])
def analyze_batch():
    """
    Analyze multiple files at once.
    
    Request body:
    {
        "files": [
            {"path": "src/foo.ts", "content": "..."},
            {"path": "src/bar.ts", "content": "..."}
        ]
    }
    """
    data = request.get_json()
    
    if not data or 'files' not in data:
        return jsonify({'error': 'Missing "files" in request body'}), 400
    
    results = []
    total_ai_probability = 0
    
    for file in data['files']:
        if 'content' not in file or 'path' not in file:
            continue
        
        result = analyze_code(file['content'])
        result['path'] = file['path']
        results.append(result)
        total_ai_probability += result['ai_probability']
    
    avg_probability = total_ai_probability / len(results) if results else 0
    
    ai_files = [r for r in results if r['ai_probability'] > 0.7]
    human_files = [r for r in results if r['ai_probability'] <= 0.7]
    
    return jsonify({
        'files_analyzed': len(results),
        'ai_detected': len(ai_files),
        'human_written': len(human_files),
        'average_ai_probability': round(avg_probability, 3),
        'results': results
    })


@app.route('/api/v1/evaluate', methods=['POST'])
def evaluate():
    """
    Evaluate a commit against policies.
    
    Request body:
    {
        "files": [
            {"path": "src/auth/login.ts", "ai_confidence": 0.92, "lines_changed": 45}
        ],
        "max_ai_confidence": 0.92,
        "ai_percentage": 69,
        "total_lines_changed": 65,
        "review_time_seconds": 90,
        "config": "..." // optional custom policy YAML
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Missing request body'}), 400
    
    config = data.get('config', EXAMPLE_CONFIG)
    
    analysis = {
        'files': data.get('files', []),
        'max_ai_confidence': data.get('max_ai_confidence', 0),
        'ai_percentage': data.get('ai_percentage', 0),
        'total_lines_changed': data.get('total_lines_changed', 0),
        'review_time_seconds': data.get('review_time_seconds'),
        'security_issues': data.get('security_issues', [])
    }
    
    result = evaluate_commit(config, analysis)
    
    return jsonify(result)


@app.route('/api/v1/scan', methods=['POST'])
def scan():
    """
    Full PR/commit scan: analyze files + evaluate policies.
    
    Request body:
    {
        "files": [
            {"path": "src/foo.ts", "content": "..."}
        ],
        "review_time_seconds": 120,  // optional
        "config": "..."  // optional policy YAML
    }
    """
    data = request.get_json()
    
    if not data or 'files' not in data:
        return jsonify({'error': 'Missing "files" in request body'}), 400
    
    # Analyze each file
    analysis_results = []
    max_ai_confidence = 0
    total_ai_lines = 0
    total_lines = 0
    
    for file in data['files']:
        if 'content' not in file or 'path' not in file:
            continue
        
        result = analyze_code(file['content'])
        lines = len(file['content'].split('\n'))
        
        analysis_results.append({
            'path': file['path'],
            'ai_confidence': result['ai_probability'],
            'lines_changed': lines,
            'status': 'ai-generated' if result['ai_probability'] > 0.7 else 'human-written'
        })
        
        if result['ai_probability'] > max_ai_confidence:
            max_ai_confidence = result['ai_probability']
        
        if result['ai_probability'] > 0.7:
            total_ai_lines += lines
        total_lines += lines
    
    ai_percentage = (total_ai_lines / total_lines * 100) if total_lines > 0 else 0
    
    # Evaluate policies
    config = data.get('config', EXAMPLE_CONFIG)
    policy_analysis = {
        'files': analysis_results,
        'max_ai_confidence': max_ai_confidence,
        'ai_percentage': ai_percentage,
        'total_lines_changed': total_lines,
        'review_time_seconds': data.get('review_time_seconds'),
        'security_issues': []
    }
    
    policy_result = evaluate_commit(config, policy_analysis)
    
    return jsonify({
        'status': 'completed',
        'files_scanned': len(analysis_results),
        'ai_detected': len([r for r in analysis_results if r['status'] == 'ai-generated']),
        'human_written': len([r for r in analysis_results if r['status'] == 'human-written']),
        'max_ai_confidence': round(max_ai_confidence, 3),
        'ai_percentage': round(ai_percentage, 1),
        'results': analysis_results,
        'policy_evaluation': policy_result,
        'blocked': not policy_result['allowed'],
        'violations': policy_result['violations'],
        'warnings': policy_result['warnings']
    })


@app.route('/api/v1/policies', methods=['GET'])
def get_policies():
    """Get the current policy configuration."""
    return jsonify({
        'version': policy_engine.version,
        'org': policy_engine.org,
        'policies': [
            {
                'name': p.name,
                'description': p.description,
                'action': p.action.value
            }
            for p in policy_engine.policies
        ]
    })


@app.route('/api/v1/report', methods=['POST'])
def generate_report():
    """
    Generate an audit report.
    
    Request body:
    {
        "type": "soc2",  // soc2, iso27001, summary
        "period": "2026-Q1",
        "commits": [...]  // historical commit analyses
    }
    """
    data = request.get_json()
    report_type = data.get('type', 'summary')
    period = data.get('period', 'current')
    
    # Mock report for now
    return jsonify({
        'report_type': report_type,
        'period': period,
        'generated_at': '2026-02-02T05:00:00Z',
        'summary': {
            'total_commits': 142,
            'ai_generated_commits': 89,
            'ai_percentage': 62.7,
            'policy_violations': 3,
            'violations_resolved': 3,
            'average_review_time_minutes': 4.2
        },
        'compliance_status': 'compliant',
        'evidence_items': [
            'AI code detection enabled on all repositories',
            'Policy enforcement active since 2026-01-15',
            'All violations required senior review before merge',
            'Audit trail maintained for all commits'
        ]
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
