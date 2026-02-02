"""
VibeGuard Policy Engine

Evaluates commits against organization-defined policies.
"""

import re
import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
from fnmatch import fnmatch


class Action(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    REQUIRE_REVIEW = "require_reviewers"


@dataclass
class Trigger:
    ai_confidence: Optional[str] = None      # "> 70%"
    ai_percentage: Optional[str] = None      # "> 50%"
    lines_changed: Optional[str] = None      # "> 100"
    review_time: Optional[str] = None        # "< 2 minutes"
    paths: List[str] = field(default_factory=list)
    checks: List[str] = field(default_factory=list)


@dataclass
class Policy:
    name: str
    description: str
    trigger: Trigger
    action: Action
    message: str = ""
    reviewers: Optional[Dict] = None
    override: Optional[Dict] = None


@dataclass
class CommitAnalysis:
    files: List[Dict]           # [{path, ai_confidence, lines_changed}]
    max_ai_confidence: float    # Highest AI confidence in any file
    ai_percentage: float        # % of lines that are AI-generated
    total_lines_changed: int    # Total lines changed
    review_time_seconds: Optional[int] = None
    security_issues: List[Dict] = field(default_factory=list)


@dataclass
class Violation:
    policy_name: str
    message: str
    files: List[str]


@dataclass
class Warning:
    policy_name: str
    message: str


@dataclass
class EvaluationResult:
    allowed: bool
    violations: List[Violation]
    warnings: List[Warning]
    required_reviewers: List[str]


class PolicyEngine:
    """
    Evaluates commits against defined policies.
    """
    
    def __init__(self, config_yaml: str):
        """
        Initialize the policy engine with YAML configuration.
        
        Args:
            config_yaml: YAML string containing policy definitions
        """
        config = yaml.safe_load(config_yaml)
        self.version = config.get('version', '1.0')
        self.org = config.get('org', 'default')
        self.policies = self._parse_policies(config.get('policies', []))

    def _parse_policies(self, policy_dicts: List[Dict]) -> List[Policy]:
        """Parse policy dictionaries into Policy objects."""
        policies = []
        for p in policy_dicts:
            trigger_dict = p.get('trigger', {})
            trigger = Trigger(
                ai_confidence=trigger_dict.get('ai_confidence'),
                ai_percentage=trigger_dict.get('ai_percentage'),
                lines_changed=trigger_dict.get('lines_changed'),
                review_time=trigger_dict.get('review_time'),
                paths=p.get('paths', []),
                checks=trigger_dict.get('checks', [])
            )
            
            action_str = p.get('action', 'allow')
            if action_str == 'block_on_fail':
                action = Action.BLOCK
            else:
                action = Action(action_str)
            
            policy = Policy(
                name=p.get('name', 'unnamed'),
                description=p.get('description', ''),
                trigger=trigger,
                action=action,
                message=p.get('message', ''),
                reviewers=p.get('reviewers'),
                override=p.get('override')
            )
            policies.append(policy)
        
        return policies

    def evaluate(self, analysis: CommitAnalysis) -> EvaluationResult:
        """
        Evaluate a commit analysis against all policies.
        
        Args:
            analysis: CommitAnalysis object with commit details
            
        Returns:
            EvaluationResult with violations, warnings, and required reviewers
        """
        result = EvaluationResult(
            allowed=True,
            violations=[],
            warnings=[],
            required_reviewers=[]
        )
        
        for policy in self.policies:
            eval_result = self._evaluate_policy(policy, analysis)
            
            if eval_result['triggered']:
                if policy.action == Action.BLOCK:
                    result.allowed = False
                    result.violations.append(Violation(
                        policy_name=policy.name,
                        message=eval_result['message'],
                        files=eval_result['matched_files']
                    ))
                elif policy.action == Action.WARN:
                    result.warnings.append(Warning(
                        policy_name=policy.name,
                        message=eval_result['message']
                    ))
                elif policy.action == Action.REQUIRE_REVIEW:
                    if policy.reviewers:
                        teams = policy.reviewers.get('teams', [])
                        result.required_reviewers.extend(teams)
        
        return result

    def _evaluate_policy(self, policy: Policy, analysis: CommitAnalysis) -> Dict:
        """Evaluate a single policy against the analysis."""
        result = {
            'triggered': False,
            'message': policy.message,
            'matched_files': []
        }
        
        # Check trigger conditions
        if not self._trigger_matches(policy.trigger, analysis):
            return result
        
        # Check path restrictions
        if policy.trigger.paths:
            matched_files = self._match_paths(policy.trigger.paths, analysis.files)
            if not matched_files:
                return result
            result['matched_files'] = matched_files
        else:
            result['matched_files'] = [f['path'] for f in analysis.files]
        
        # Check security checks if specified
        if policy.trigger.checks:
            checks_passed = self._run_checks(policy.trigger.checks, analysis)
            if checks_passed:
                return result  # Checks passed, policy not violated
        
        result['triggered'] = True
        return result

    def _trigger_matches(self, trigger: Trigger, analysis: CommitAnalysis) -> bool:
        """Check if trigger conditions match the analysis."""
        if trigger.ai_confidence:
            if not self._compare_threshold(trigger.ai_confidence, analysis.max_ai_confidence * 100):
                return False
        
        if trigger.ai_percentage:
            if not self._compare_threshold(trigger.ai_percentage, analysis.ai_percentage):
                return False
        
        if trigger.lines_changed:
            if not self._compare_threshold(trigger.lines_changed, analysis.total_lines_changed):
                return False
        
        if trigger.review_time and analysis.review_time_seconds is not None:
            # Convert "< 2 minutes" to seconds comparison
            if not self._compare_time_threshold(trigger.review_time, analysis.review_time_seconds):
                return False
        
        return True

    def _compare_threshold(self, condition: str, value: float) -> bool:
        """
        Compare a value against a threshold condition.
        
        Examples:
            "> 70%" with value 85 -> True
            "< 50" with value 30 -> True
        """
        match = re.match(r'([<>=]+)\s*(\d+(?:\.\d+)?)\s*%?', condition.strip())
        if not match:
            return False
        
        operator, threshold = match.groups()
        threshold = float(threshold)
        
        if operator == '>':
            return value > threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '<':
            return value < threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '==' or operator == '=':
            return value == threshold
        
        return False

    def _compare_time_threshold(self, condition: str, seconds: int) -> bool:
        """Compare time threshold (e.g., "< 2 minutes")."""
        match = re.match(r'([<>=]+)\s*(\d+)\s*(second|minute|hour)s?', condition.strip())
        if not match:
            return False
        
        operator, amount, unit = match.groups()
        amount = int(amount)
        
        multipliers = {'second': 1, 'minute': 60, 'hour': 3600}
        threshold_seconds = amount * multipliers.get(unit, 1)
        
        return self._compare_threshold(f"{operator} {threshold_seconds}", seconds)

    def _match_paths(self, patterns: List[str], files: List[Dict]) -> List[str]:
        """Match file paths against glob patterns."""
        matched = []
        for f in files:
            path = f['path']
            for pattern in patterns:
                if fnmatch(path, pattern):
                    matched.append(path)
                    break
        return matched

    def _run_checks(self, checks: List[str], analysis: CommitAnalysis) -> bool:
        """Run security checks and return True if all pass."""
        check_types = {
            'hardcoded_secrets': self._check_secrets,
            'sql_injection': self._check_sql_injection,
            'xss_patterns': self._check_xss,
        }
        
        for check in checks:
            if check in check_types:
                if not check_types[check](analysis):
                    return False
        
        return True

    def _check_secrets(self, analysis: CommitAnalysis) -> bool:
        """Check for hardcoded secrets."""
        for issue in analysis.security_issues:
            if issue.get('type') == 'hardcoded_secret':
                return False
        return True

    def _check_sql_injection(self, analysis: CommitAnalysis) -> bool:
        """Check for SQL injection vulnerabilities."""
        for issue in analysis.security_issues:
            if issue.get('type') == 'sql_injection':
                return False
        return True

    def _check_xss(self, analysis: CommitAnalysis) -> bool:
        """Check for XSS vulnerabilities."""
        for issue in analysis.security_issues:
            if issue.get('type') == 'xss':
                return False
        return True


# Example configuration
EXAMPLE_CONFIG = """
version: "1.0"
org: acme-corp

policies:
  - name: no-ai-in-auth
    description: "AI-generated code not allowed in authentication"
    trigger:
      ai_confidence: "> 70%"
    paths:
      - "src/auth/**"
      - "src/security/**"
      - "**/middleware/auth*"
    action: block
    message: "AI-generated code requires senior review in auth modules"
    override:
      require_approval_from:
        - team: security-leads
        - min_approvals: 2

  - name: high-ai-review
    description: "PRs with >50% AI code need senior review"
    trigger:
      ai_percentage: "> 50%"
      lines_changed: "> 100"
    action: require_reviewers
    reviewers:
      teams: ["senior-engineers"]
      min_approvals: 1

  - name: review-quality
    description: "Flag PRs approved too quickly"
    trigger:
      review_time: "< 2 minutes"
      ai_percentage: "> 30%"
    action: warn
    message: "This PR was approved quickly. Please verify AI-generated sections."

  - name: security-gate
    description: "Block on security vulnerabilities"
    trigger:
      ai_confidence: "> 50%"
      checks:
        - hardcoded_secrets
        - sql_injection
        - xss_patterns
    action: block_on_fail
"""


def evaluate_commit(config_yaml: str, analysis_dict: Dict) -> Dict:
    """
    Convenience function to evaluate a commit.
    
    Args:
        config_yaml: YAML configuration string
        analysis_dict: Dictionary with commit analysis data
        
    Returns:
        Dictionary with evaluation results
    """
    engine = PolicyEngine(config_yaml)
    
    analysis = CommitAnalysis(
        files=analysis_dict.get('files', []),
        max_ai_confidence=analysis_dict.get('max_ai_confidence', 0),
        ai_percentage=analysis_dict.get('ai_percentage', 0),
        total_lines_changed=analysis_dict.get('total_lines_changed', 0),
        review_time_seconds=analysis_dict.get('review_time_seconds'),
        security_issues=analysis_dict.get('security_issues', [])
    )
    
    result = engine.evaluate(analysis)
    
    return {
        'allowed': result.allowed,
        'violations': [
            {'policy': v.policy_name, 'message': v.message, 'files': v.files}
            for v in result.violations
        ],
        'warnings': [
            {'policy': w.policy_name, 'message': w.message}
            for w in result.warnings
        ],
        'required_reviewers': result.required_reviewers
    }


if __name__ == "__main__":
    # Test the policy engine
    test_analysis = {
        'files': [
            {'path': 'src/auth/login.ts', 'ai_confidence': 0.92, 'lines_changed': 45},
            {'path': 'src/utils/helpers.ts', 'ai_confidence': 0.35, 'lines_changed': 20},
        ],
        'max_ai_confidence': 0.92,
        'ai_percentage': 69,
        'total_lines_changed': 65,
        'review_time_seconds': 90,  # 1.5 minutes
        'security_issues': []
    }
    
    result = evaluate_commit(EXAMPLE_CONFIG, test_analysis)
    print("Evaluation Result:")
    print(f"  Allowed: {result['allowed']}")
    print(f"  Violations: {result['violations']}")
    print(f"  Warnings: {result['warnings']}")
    print(f"  Required Reviewers: {result['required_reviewers']}")
