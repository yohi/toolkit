"""AI-powered code analysis for security, quality, and performance."""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import json
import re
import hashlib

from .llm_client import LLMClient, get_llm_client
from .prompt_templates import AnalysisPrompt
from ..patterns.observer import publish_event, EventType

logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Code analysis type enumeration."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    GENERAL = "general"


class IssueSeverity(Enum):
    """Issue severity enumeration."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class CodeIssue:
    """Individual code issue."""
    issue_id: str
    type: str                    # security, performance, quality, etc.
    severity: IssueSeverity
    title: str
    description: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""
    example_fix: Optional[str] = None
    references: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_fix_time: Optional[str] = None
    confidence: float = 1.0      # 0.0 to 1.0
    cwe_id: Optional[str] = None  # Common Weakness Enumeration ID

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'issue_id': self.issue_id,
            'type': self.type,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'file_path': self.file_path,
            'code_snippet': self.code_snippet,
            'recommendation': self.recommendation,
            'example_fix': self.example_fix,
            'references': self.references,
            'tags': self.tags,
            'estimated_fix_time': self.estimated_fix_time,
            'confidence': self.confidence,
            'cwe_id': self.cwe_id
        }


@dataclass
class SecurityAnalysis:
    """Security analysis result."""
    security_score: int          # 1-10 (10 = most secure)
    vulnerabilities: List[CodeIssue] = field(default_factory=list)
    security_patterns: List[str] = field(default_factory=list)
    risk_assessment: str = ""
    compliance_status: Dict[str, bool] = field(default_factory=dict)  # OWASP, PCI, etc.

    def get_critical_count(self) -> int:
        """Get count of critical security issues."""
        return sum(1 for issue in self.vulnerabilities if issue.severity == IssueSeverity.CRITICAL)

    def get_high_count(self) -> int:
        """Get count of high severity security issues."""
        return sum(1 for issue in self.vulnerabilities if issue.severity == IssueSeverity.HIGH)


@dataclass
class PerformanceAnalysis:
    """Performance analysis result."""
    performance_score: int       # 1-10 (10 = best performance)
    bottlenecks: List[CodeIssue] = field(default_factory=list)
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)
    optimization_opportunities: List[str] = field(default_factory=list)
    estimated_impact: str = ""

    def get_time_complexity(self) -> str:
        """Get estimated time complexity."""
        return self.complexity_metrics.get('time_complexity', 'Unknown')

    def get_space_complexity(self) -> str:
        """Get estimated space complexity."""
        return self.complexity_metrics.get('space_complexity', 'Unknown')


@dataclass
class CodeQualityScore:
    """Code quality analysis result."""
    overall_score: int           # 1-10 (10 = highest quality)
    maintainability: int         # 1-10
    readability: int             # 1-10
    testability: int             # 1-10
    modularity: int              # 1-10
    issues: List[CodeIssue] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)
    technical_debt_estimate: Optional[str] = None

    def get_quality_grade(self) -> str:
        """Get letter grade for overall quality."""
        if self.overall_score >= 9:
            return "A+"
        elif self.overall_score >= 8:
            return "A"
        elif self.overall_score >= 7:
            return "B"
        elif self.overall_score >= 6:
            return "C"
        elif self.overall_score >= 5:
            return "D"
        else:
            return "F"


@dataclass
class ComprehensiveAnalysis:
    """Comprehensive code analysis result."""
    analysis_id: str
    file_path: str
    language: str
    lines_of_code: int
    analysis_timestamp: str

    # Analysis results
    security: SecurityAnalysis
    performance: PerformanceAnalysis
    quality: CodeQualityScore

    # Summary
    overall_health_score: int    # 1-10
    critical_issues_count: int
    recommendations: List[str] = field(default_factory=list)
    priority_fixes: List[CodeIssue] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'analysis_id': self.analysis_id,
            'file_path': self.file_path,
            'language': self.language,
            'lines_of_code': self.lines_of_code,
            'analysis_timestamp': self.analysis_timestamp,
            'security': {
                'security_score': self.security.security_score,
                'vulnerabilities_count': len(self.security.vulnerabilities),
                'critical_count': self.security.get_critical_count(),
                'high_count': self.security.get_high_count(),
                'vulnerabilities': [v.to_dict() for v in self.security.vulnerabilities]
            },
            'performance': {
                'performance_score': self.performance.performance_score,
                'bottlenecks_count': len(self.performance.bottlenecks),
                'complexity_metrics': self.performance.complexity_metrics,
                'bottlenecks': [b.to_dict() for b in self.performance.bottlenecks]
            },
            'quality': {
                'overall_score': self.quality.overall_score,
                'quality_grade': self.quality.get_quality_grade(),
                'maintainability': self.quality.maintainability,
                'readability': self.quality.readability,
                'testability': self.quality.testability,
                'modularity': self.quality.modularity,
                'issues_count': len(self.quality.issues),
                'issues': [i.to_dict() for i in self.quality.issues]
            },
            'overall_health_score': self.overall_health_score,
            'critical_issues_count': self.critical_issues_count,
            'recommendations': self.recommendations,
            'priority_fixes': [f.to_dict() for f in self.priority_fixes]
        }


class AICodeAnalyzer:
    """AI-powered code analyzer."""

    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        fallback_enabled: bool = True,
        cache_enabled: bool = True
    ):
        """Initialize AI code analyzer.

        Args:
            llm_client: LLM client for AI analysis
            fallback_enabled: Enable rule-based fallback
            cache_enabled: Enable result caching
        """
        self.llm_client = llm_client or get_llm_client()
        self.fallback_enabled = fallback_enabled
        self.cache_enabled = cache_enabled

        # Prompt template
        self.prompt_template = AnalysisPrompt()

        # Rule-based patterns for fallback
        self._init_analysis_patterns()

        # Statistics
        self.stats = {
            'analyses_performed': 0,
            'ai_analyses': 0,
            'fallback_analyses': 0,
            'issues_found': 0,
            'critical_issues': 0,
            'security_issues': 0,
            'performance_issues': 0,
            'quality_issues': 0,
            'average_score': 0.0
        }

    def _init_analysis_patterns(self) -> None:
        """Initialize analysis patterns for rule-based fallback."""
        # Security vulnerability patterns
        self.security_patterns = {
            'sql_injection': [
                r'(?i)(execute|exec|query)\s*\(\s*["\'].*%s.*["\']',
                r'(?i)query\s*=\s*["\'].*\+.*["\']',
                r'(?i)SELECT.*\+.*FROM',
                r'(?i)f["\']SELECT.*\{.*\}.*FROM'
            ],
            'xss': [
                r'(?i)innerHTML\s*=\s*.*\+',
                r'(?i)document\.write\s*\(',
                r'(?i)eval\s*\(',
                r'(?i)dangerouslySetInnerHTML'
            ],
            'hardcoded_secrets': [
                r'(?i)(password|pwd|secret|key|token)\s*=\s*["\'][^"\']{8,}["\']',
                r'(?i)(api_key|apikey)\s*=\s*["\'][^"\']+["\']',
                r'(?i)(ACCESS_KEY|SECRET_KEY)\s*=\s*["\'][^"\']+["\']'
            ],
            'insecure_random': [
                r'(?i)random\(\)',
                r'(?i)Math\.random\(\)',
                r'(?i)new Random\(\)'
            ],
            'path_traversal': [
                r'(?i)open\s*\(\s*.*\+.*\)',
                r'(?i)readFile\s*\(\s*.*\+.*\)',
                r'(?i)\.\.\/.*\.\.\/'
            ]
        }

        # Performance anti-patterns
        self.performance_patterns = {
            'n_plus_one': [
                r'(?i)for.*in.*:.*query\(',
                r'(?i)for.*in.*:.*find\(',
                r'(?i)\.forEach\(.*=>\s*.*\.query\('
            ],
            'inefficient_loops': [
                r'(?i)for.*in.*for.*in',
                r'(?i)while.*while',
                r'(?i)for.*range\(len\('
            ],
            'memory_leaks': [
                r'(?i)setInterval\(',
                r'(?i)addEventListener.*without.*removeEventListener',
                r'(?i)new.*Array\(\d{4,}\)'
            ],
            'blocking_operations': [
                r'(?i)time\.sleep\(',
                r'(?i)Thread\.sleep\(',
                r'(?i)syncronous.*request'
            ]
        }

        # Code quality issues
        self.quality_patterns = {
            'long_functions': r'def\s+\w+\([^)]*\):(?:\s*[^\n]*\n){50,}',
            'deep_nesting': r'(?:\s{4,}if|\s{8,}if|\s{12,}if|\s{16,}if)',
            'magic_numbers': r'\b(?<![\w\.])\d{2,}(?![\w\.])\b',
            'duplicate_code': r'(.{20,})\n(?:.*\n)*?\1',
            'poor_naming': r'(?i)\b(temp|tmp|data|info|obj|var|thing)\d*\b',
            'missing_error_handling': r'(?i)(open|read|write|request|query)(?!.*(?:try|except|catch|error))',
            'commented_code': r'^\s*#\s*[a-zA-Z_][a-zA-Z0-9_]*\s*='
        }

    async def analyze_code_async(
        self,
        code: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        analysis_types: Optional[List[AnalysisType]] = None
    ) -> ComprehensiveAnalysis:
        """Analyze code comprehensively.

        Args:
            code: Code to analyze
            file_path: Optional file path
            language: Programming language
            analysis_types: Types of analysis to perform

        Returns:
            Comprehensive analysis result
        """
        if analysis_types is None:
            analysis_types = [AnalysisType.SECURITY, AnalysisType.PERFORMANCE, AnalysisType.QUALITY]

        logger.info(f"Analyzing code: {file_path or 'unnamed'} ({len(code)} chars)")

        # Generate analysis ID
        analysis_id = self._generate_analysis_id(code, file_path)

        # Detect language if not provided
        if not language:
            language = self._detect_language(code, file_path)

        # Initialize results
        security = SecurityAnalysis(security_score=10)
        performance = PerformanceAnalysis(performance_score=10)
        quality = CodeQualityScore(
            overall_score=10,
            maintainability=10,
            readability=10,
            testability=10,
            modularity=10
        )

        # Perform analyses
        try:
            # Security analysis
            if AnalysisType.SECURITY in analysis_types:
                security = await self._analyze_security(code, language, file_path)

            # Performance analysis
            if AnalysisType.PERFORMANCE in analysis_types:
                performance = await self._analyze_performance(code, language, file_path)

            # Quality analysis
            if AnalysisType.QUALITY in analysis_types:
                quality = await self._analyze_quality(code, language, file_path)

        except Exception as e:
            logger.error(f"Error during code analysis: {e}")

        # Calculate overall metrics
        overall_health_score = self._calculate_overall_score(security, performance, quality)
        critical_issues_count = self._count_critical_issues(security, performance, quality)
        priority_fixes = self._identify_priority_fixes(security, performance, quality)
        recommendations = self._generate_recommendations(security, performance, quality)

        # Create comprehensive result
        result = ComprehensiveAnalysis(
            analysis_id=analysis_id,
            file_path=file_path or "unknown",
            language=language,
            lines_of_code=len(code.splitlines()),
            analysis_timestamp=self._get_timestamp(),
            security=security,
            performance=performance,
            quality=quality,
            overall_health_score=overall_health_score,
            critical_issues_count=critical_issues_count,
            priority_fixes=priority_fixes,
            recommendations=recommendations
        )

        # Update statistics
        self._update_stats(result)

        # Publish analysis event
        publish_event(
            EventType.PROCESSING_COMPLETED,
            source="AICodeAnalyzer",
            data={
                'analysis_id': analysis_id,
                'file_path': file_path,
                'language': language,
                'overall_score': overall_health_score,
                'critical_issues': critical_issues_count,
                'security_score': security.security_score,
                'performance_score': performance.performance_score,
                'quality_score': quality.overall_score
            }
        )

        logger.info(f"Analysis complete: {analysis_id} (Score: {overall_health_score}/10)")
        return result

    def analyze_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        language: Optional[str] = None,
        analysis_types: Optional[List[AnalysisType]] = None
    ) -> ComprehensiveAnalysis:
        """Analyze code synchronously."""
        # Run async method
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.analyze_code_async(code, file_path, language, analysis_types)
        )

    async def _analyze_security(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None
    ) -> SecurityAnalysis:
        """Perform security analysis."""
        vulnerabilities = []
        security_score = 10

        try:
            # Try AI analysis first
            if self.llm_client:
                ai_result = await self._analyze_with_ai(code, AnalysisType.SECURITY, language, file_path)
                if ai_result and ai_result.get('issues'):
                    vulnerabilities.extend([
                        self._parse_issue(issue, 'security')
                        for issue in ai_result['issues']
                        if issue.get('type') == 'security'
                    ])
                    security_score = min(10, max(1, ai_result.get('overall_score', 10)))

            # Fallback to rule-based analysis
            if self.fallback_enabled:
                rule_vulnerabilities = self._analyze_security_with_rules(code, language, file_path)
                vulnerabilities.extend(rule_vulnerabilities)

        except Exception as e:
            logger.error(f"Security analysis error: {e}")

        # Adjust security score based on vulnerabilities
        critical_count = sum(1 for v in vulnerabilities if v.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for v in vulnerabilities if v.severity == IssueSeverity.HIGH)

        if critical_count > 0:
            security_score = min(security_score, 3)
        elif high_count > 2:
            security_score = min(security_score, 5)
        elif high_count > 0:
            security_score = min(security_score, 7)

        return SecurityAnalysis(
            security_score=security_score,
            vulnerabilities=vulnerabilities,
            security_patterns=list(self.security_patterns.keys()),
            risk_assessment=self._generate_security_risk_assessment(vulnerabilities),
            compliance_status=self._check_compliance(vulnerabilities)
        )

    async def _analyze_performance(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None
    ) -> PerformanceAnalysis:
        """Perform performance analysis."""
        bottlenecks = []
        performance_score = 10
        complexity_metrics = {}

        try:
            # Try AI analysis first
            if self.llm_client:
                ai_result = await self._analyze_with_ai(code, AnalysisType.PERFORMANCE, language, file_path)
                if ai_result and ai_result.get('issues'):
                    bottlenecks.extend([
                        self._parse_issue(issue, 'performance')
                        for issue in ai_result['issues']
                        if issue.get('type') == 'performance'
                    ])
                    performance_score = min(10, max(1, ai_result.get('overall_score', 10)))

                # Extract complexity metrics from AI response
                if ai_result.get('complexity_metrics'):
                    complexity_metrics = ai_result['complexity_metrics']

            # Fallback to rule-based analysis
            if self.fallback_enabled:
                rule_bottlenecks = self._analyze_performance_with_rules(code, language, file_path)
                bottlenecks.extend(rule_bottlenecks)

                # Calculate basic complexity metrics
                complexity_metrics.update(self._calculate_complexity_metrics(code, language))

        except Exception as e:
            logger.error(f"Performance analysis error: {e}")

        # Adjust performance score based on issues
        critical_perf_count = sum(1 for b in bottlenecks if b.severity == IssueSeverity.CRITICAL)
        high_perf_count = sum(1 for b in bottlenecks if b.severity == IssueSeverity.HIGH)

        if critical_perf_count > 0:
            performance_score = min(performance_score, 4)
        elif high_perf_count > 1:
            performance_score = min(performance_score, 6)
        elif high_perf_count > 0:
            performance_score = min(performance_score, 8)

        return PerformanceAnalysis(
            performance_score=performance_score,
            bottlenecks=bottlenecks,
            complexity_metrics=complexity_metrics,
            optimization_opportunities=self._identify_optimization_opportunities(bottlenecks),
            estimated_impact=self._estimate_performance_impact(bottlenecks)
        )

    async def _analyze_quality(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None
    ) -> CodeQualityScore:
        """Perform code quality analysis."""
        issues = []
        strengths = []

        try:
            # Try AI analysis first
            if self.llm_client:
                ai_result = await self._analyze_with_ai(code, AnalysisType.QUALITY, language, file_path)
                if ai_result:
                    if ai_result.get('issues'):
                        issues.extend([
                            self._parse_issue(issue, 'quality')
                            for issue in ai_result['issues']
                            if issue.get('type') in ['quality', 'style', 'maintainability']
                        ])

                    if ai_result.get('strengths'):
                        strengths.extend(ai_result['strengths'])

            # Fallback to rule-based analysis
            if self.fallback_enabled:
                rule_issues = self._analyze_quality_with_rules(code, language, file_path)
                issues.extend(rule_issues)

        except Exception as e:
            logger.error(f"Quality analysis error: {e}")

        # Calculate quality scores
        scores = self._calculate_quality_scores(code, issues, language)

        return CodeQualityScore(
            overall_score=scores['overall'],
            maintainability=scores['maintainability'],
            readability=scores['readability'],
            testability=scores['testability'],
            modularity=scores['modularity'],
            issues=issues,
            strengths=strengths,
            improvement_suggestions=self._generate_quality_suggestions(issues),
            technical_debt_estimate=self._estimate_technical_debt(issues)
        )

    async def _analyze_with_ai(
        self,
        code: str,
        analysis_type: AnalysisType,
        language: str,
        file_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Analyze code using AI/LLM."""
        if not self.llm_client:
            return None

        try:
            # Create analysis prompt
            context = {
                'language': language,
                'file_path': file_path,
                'analysis_focus': analysis_type.value
            }

            prompt = self.prompt_template.create_prompt(
                code_snippet=code,
                analysis_type=analysis_type.value,
                context=context
            )

            system_prompt = self.prompt_template.get_system_prompt()

            # Get LLM response
            response = await self.llm_client.generate_async(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=1500
            )

            # Parse AI response
            result = self._parse_ai_analysis_response(response.content)

            self.stats['ai_analyses'] += 1
            return result

        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return None

    def _parse_ai_analysis_response(self, content: str) -> Dict[str, Any]:
        """Parse AI analysis response."""
        try:
            # Try to parse as JSON
            if content.strip().startswith('{'):
                return json.loads(content)

            # Fallback text parsing
            return self._parse_text_analysis_response(content)

        except Exception as e:
            logger.error(f"Error parsing AI analysis response: {e}")
            return {}

    def _parse_text_analysis_response(self, text: str) -> Dict[str, Any]:
        """Parse text analysis response."""
        result = {
            'overall_score': 7,
            'issues': [],
            'strengths': [],
            'recommendations': []
        }

        # Extract overall score
        score_match = re.search(r'(?i)(?:overall|total|final).*?score.*?(\d+)', text)
        if score_match:
            result['overall_score'] = int(score_match.group(1))

        # Extract issues (simple pattern matching)
        issue_pattern = r'(?i)(issue|problem|vulnerability|bottleneck):\s*(.+?)(?:\n|$)'
        issues = re.findall(issue_pattern, text)
        for _, description in issues:
            result['issues'].append({
                'type': 'general',
                'severity': 'medium',
                'description': description.strip(),
                'recommendation': 'Review and fix this issue'
            })

        return result

    def _parse_issue(self, issue_data: Dict[str, Any], issue_type: str) -> CodeIssue:
        """Parse issue data into CodeIssue object."""
        severity_map = {
            'critical': IssueSeverity.CRITICAL,
            'high': IssueSeverity.HIGH,
            'medium': IssueSeverity.MEDIUM,
            'low': IssueSeverity.LOW,
            'info': IssueSeverity.INFO
        }

        severity = severity_map.get(issue_data.get('severity', 'medium').lower(), IssueSeverity.MEDIUM)

        return CodeIssue(
            issue_id=self._generate_issue_id(issue_data),
            type=issue_type,
            severity=severity,
            title=issue_data.get('title', issue_data.get('description', 'Code Issue')[:50]),
            description=issue_data.get('description', ''),
            line_number=issue_data.get('line_number'),
            recommendation=issue_data.get('recommendation', ''),
            example_fix=issue_data.get('example', issue_data.get('example_fix')),
            estimated_fix_time=issue_data.get('effort_estimate'),
            confidence=float(issue_data.get('confidence', 0.8))
        )

    def _generate_issue_id(self, issue_data: Dict[str, Any]) -> str:
        """Generate unique issue ID."""
        content = f"{issue_data.get('type', '')}{issue_data.get('description', '')}{issue_data.get('line_number', '')}"
        return hashlib.md5(content.encode()).hexdigest()[:8]

    def _generate_analysis_id(self, code: str, file_path: Optional[str] = None) -> str:
        """Generate unique analysis ID."""
        content = f"{file_path or ''}{len(code)}{hash(code)}"
        return f"analysis_{hashlib.md5(content.encode()).hexdigest()[:12]}"

    def _detect_language(self, code: str, file_path: Optional[str] = None) -> str:
        """Detect programming language."""
        if file_path:
            ext = file_path.split('.')[-1].lower()
            lang_map = {
                'py': 'python',
                'js': 'javascript',
                'ts': 'typescript',
                'java': 'java',
                'cpp': 'cpp',
                'c': 'c',
                'cs': 'csharp',
                'php': 'php',
                'rb': 'ruby',
                'go': 'go',
                'rs': 'rust'
            }
            if ext in lang_map:
                return lang_map[ext]

        # Simple heuristic detection
        if 'def ' in code and 'import ' in code:
            return 'python'
        elif 'function ' in code and 'var ' in code:
            return 'javascript'
        elif 'public class ' in code:
            return 'java'

        return 'unknown'

    def _analyze_security_with_rules(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None
    ) -> List[CodeIssue]:
        """Analyze security using rule-based patterns."""
        issues = []

        for vuln_type, patterns in self.security_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, code, re.MULTILINE))
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1

                    issue = CodeIssue(
                        issue_id=f"sec_{vuln_type}_{line_number}",
                        type='security',
                        severity=self._get_security_severity(vuln_type),
                        title=f"Potential {vuln_type.replace('_', ' ').title()}",
                        description=f"Detected potential {vuln_type.replace('_', ' ')} vulnerability",
                        line_number=line_number,
                        file_path=file_path,
                        code_snippet=match.group(0),
                        recommendation=self._get_security_recommendation(vuln_type),
                        confidence=0.7
                    )
                    issues.append(issue)

        return issues

    def _analyze_performance_with_rules(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None
    ) -> List[CodeIssue]:
        """Analyze performance using rule-based patterns."""
        issues = []

        for perf_type, patterns in self.performance_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, code, re.MULTILINE))
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1

                    issue = CodeIssue(
                        issue_id=f"perf_{perf_type}_{line_number}",
                        type='performance',
                        severity=self._get_performance_severity(perf_type),
                        title=f"Performance Issue: {perf_type.replace('_', ' ').title()}",
                        description=f"Detected potential {perf_type.replace('_', ' ')} issue",
                        line_number=line_number,
                        file_path=file_path,
                        code_snippet=match.group(0),
                        recommendation=self._get_performance_recommendation(perf_type),
                        confidence=0.6
                    )
                    issues.append(issue)

        return issues

    def _analyze_quality_with_rules(
        self,
        code: str,
        language: str,
        file_path: Optional[str] = None
    ) -> List[CodeIssue]:
        """Analyze code quality using rule-based patterns."""
        issues = []

        for quality_type, pattern in self.quality_patterns.items():
            matches = list(re.finditer(pattern, code, re.MULTILINE))
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1

                issue = CodeIssue(
                    issue_id=f"qual_{quality_type}_{line_number}",
                    type='quality',
                    severity=IssueSeverity.MEDIUM,
                    title=f"Code Quality: {quality_type.replace('_', ' ').title()}",
                    description=f"Detected {quality_type.replace('_', ' ')} issue",
                    line_number=line_number,
                    file_path=file_path,
                    code_snippet=match.group(0)[:100],
                    recommendation=self._get_quality_recommendation(quality_type),
                    confidence=0.5
                )
                issues.append(issue)

        return issues

    def _get_security_severity(self, vuln_type: str) -> IssueSeverity:
        """Get severity for security vulnerability type."""
        severity_map = {
            'sql_injection': IssueSeverity.CRITICAL,
            'xss': IssueSeverity.HIGH,
            'hardcoded_secrets': IssueSeverity.HIGH,
            'insecure_random': IssueSeverity.MEDIUM,
            'path_traversal': IssueSeverity.HIGH
        }
        return severity_map.get(vuln_type, IssueSeverity.MEDIUM)

    def _get_performance_severity(self, perf_type: str) -> IssueSeverity:
        """Get severity for performance issue type."""
        severity_map = {
            'n_plus_one': IssueSeverity.HIGH,
            'inefficient_loops': IssueSeverity.MEDIUM,
            'memory_leaks': IssueSeverity.HIGH,
            'blocking_operations': IssueSeverity.MEDIUM
        }
        return severity_map.get(perf_type, IssueSeverity.MEDIUM)

    def _get_security_recommendation(self, vuln_type: str) -> str:
        """Get recommendation for security vulnerability."""
        recommendations = {
            'sql_injection': 'Use parameterized queries or prepared statements',
            'xss': 'Sanitize user input and use safe DOM manipulation methods',
            'hardcoded_secrets': 'Move secrets to environment variables or secure key management',
            'insecure_random': 'Use cryptographically secure random number generators',
            'path_traversal': 'Validate and sanitize file paths, use allowlists'
        }
        return recommendations.get(vuln_type, 'Review and fix this security issue')

    def _get_performance_recommendation(self, perf_type: str) -> str:
        """Get recommendation for performance issue."""
        recommendations = {
            'n_plus_one': 'Use batch queries or eager loading to reduce database calls',
            'inefficient_loops': 'Optimize loop structure or use more efficient algorithms',
            'memory_leaks': 'Properly clean up resources and remove event listeners',
            'blocking_operations': 'Use asynchronous operations to avoid blocking'
        }
        return recommendations.get(perf_type, 'Optimize this performance issue')

    def _get_quality_recommendation(self, quality_type: str) -> str:
        """Get recommendation for code quality issue."""
        recommendations = {
            'long_functions': 'Break down into smaller, focused functions',
            'deep_nesting': 'Reduce nesting depth using early returns or helper functions',
            'magic_numbers': 'Replace with named constants',
            'duplicate_code': 'Extract common code into reusable functions',
            'poor_naming': 'Use descriptive, meaningful names',
            'missing_error_handling': 'Add proper error handling and validation',
            'commented_code': 'Remove commented code or convert to proper documentation'
        }
        return recommendations.get(quality_type, 'Improve code quality')

    def _calculate_complexity_metrics(self, code: str, language: str) -> Dict[str, Any]:
        """Calculate basic complexity metrics."""
        lines = code.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]

        # Cyclomatic complexity (simplified)
        decision_points = len(re.findall(r'\b(if|while|for|switch|case|catch|except)\b', code))
        cyclomatic_complexity = decision_points + 1

        # Nesting depth
        max_nesting = 0
        current_nesting = 0
        for line in lines:
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces > 0:
                current_nesting = leading_spaces // 4  # Assuming 4-space indentation
                max_nesting = max(max_nesting, current_nesting)

        return {
            'lines_of_code': len(non_empty_lines),
            'cyclomatic_complexity': cyclomatic_complexity,
            'max_nesting_depth': max_nesting,
            'time_complexity': 'O(n)' if 'for' in code or 'while' in code else 'O(1)',
            'space_complexity': 'O(n)' if 'list(' in code or 'dict(' in code else 'O(1)'
        }

    def _calculate_quality_scores(
        self,
        code: str,
        issues: List[CodeIssue],
        language: str
    ) -> Dict[str, int]:
        """Calculate quality scores."""
        base_score = 10

        # Deduct points for issues
        for issue in issues:
            if issue.severity == IssueSeverity.CRITICAL:
                base_score -= 3
            elif issue.severity == IssueSeverity.HIGH:
                base_score -= 2
            elif issue.severity == IssueSeverity.MEDIUM:
                base_score -= 1

        # Calculate specific scores
        lines = code.splitlines()
        non_empty_lines = [line for line in lines if line.strip()]

        # Readability score
        avg_line_length = sum(len(line) for line in non_empty_lines) / max(len(non_empty_lines), 1)
        readability = max(1, min(10, 10 - (avg_line_length - 80) // 10))

        # Maintainability score
        maintainability = max(1, base_score - len(issues) // 2)

        # Testability score (simplified)
        testability = max(1, 10 - len(re.findall(r'global\s+\w+', code)))

        # Modularity score
        function_count = len(re.findall(r'def\s+\w+|function\s+\w+', code))
        class_count = len(re.findall(r'class\s+\w+', code))
        modularity = min(10, max(1, (function_count + class_count) // 2 + 5))

        overall = (maintainability + readability + testability + modularity) // 4

        return {
            'overall': max(1, min(10, overall)),
            'maintainability': max(1, min(10, maintainability)),
            'readability': max(1, min(10, int(readability))),
            'testability': max(1, min(10, testability)),
            'modularity': max(1, min(10, modularity))
        }

    def _calculate_overall_score(
        self,
        security: SecurityAnalysis,
        performance: PerformanceAnalysis,
        quality: CodeQualityScore
    ) -> int:
        """Calculate overall health score."""
        # Weighted average with security being most important
        overall = (
            security.security_score * 0.4 +
            performance.performance_score * 0.3 +
            quality.overall_score * 0.3
        )
        return max(1, min(10, int(round(overall))))

    def _count_critical_issues(
        self,
        security: SecurityAnalysis,
        performance: PerformanceAnalysis,
        quality: CodeQualityScore
    ) -> int:
        """Count critical issues across all analyses."""
        critical_count = 0

        for issues_list in [security.vulnerabilities, performance.bottlenecks, quality.issues]:
            critical_count += sum(1 for issue in issues_list if issue.severity == IssueSeverity.CRITICAL)

        return critical_count

    def _identify_priority_fixes(
        self,
        security: SecurityAnalysis,
        performance: PerformanceAnalysis,
        quality: CodeQualityScore
    ) -> List[CodeIssue]:
        """Identify priority fixes from all analyses."""
        all_issues = []
        all_issues.extend(security.vulnerabilities)
        all_issues.extend(performance.bottlenecks)
        all_issues.extend(quality.issues)

        # Sort by severity and confidence
        severity_order = {
            IssueSeverity.CRITICAL: 5,
            IssueSeverity.HIGH: 4,
            IssueSeverity.MEDIUM: 3,
            IssueSeverity.LOW: 2,
            IssueSeverity.INFO: 1
        }

        priority_issues = sorted(
            all_issues,
            key=lambda x: (severity_order[x.severity], x.confidence),
            reverse=True
        )

        # Return top 5 priority issues
        return priority_issues[:5]

    def _generate_recommendations(
        self,
        security: SecurityAnalysis,
        performance: PerformanceAnalysis,
        quality: CodeQualityScore
    ) -> List[str]:
        """Generate high-level recommendations."""
        recommendations = []

        # Security recommendations
        if security.security_score < 7:
            recommendations.append("Immediate security review required - address critical vulnerabilities")
        elif security.get_critical_count() > 0:
            recommendations.append("Fix critical security vulnerabilities before deployment")

        # Performance recommendations
        if performance.performance_score < 6:
            recommendations.append("Performance optimization needed - review bottlenecks")
        elif len(performance.bottlenecks) > 3:
            recommendations.append("Consider optimizing performance hotspots")

        # Quality recommendations
        if quality.overall_score < 6:
            recommendations.append("Code quality improvements needed - focus on maintainability")
        elif len(quality.issues) > 5:
            recommendations.append("Address code quality issues to improve maintainability")

        # General recommendations
        if not recommendations:
            recommendations.append("Code quality is good - consider minor improvements where noted")

        return recommendations[:3]  # Limit to top 3 recommendations

    def _generate_security_risk_assessment(self, vulnerabilities: List[CodeIssue]) -> str:
        """Generate security risk assessment."""
        critical_count = sum(1 for v in vulnerabilities if v.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for v in vulnerabilities if v.severity == IssueSeverity.HIGH)

        if critical_count > 0:
            return f"HIGH RISK: {critical_count} critical vulnerabilities require immediate attention"
        elif high_count > 2:
            return f"MEDIUM RISK: {high_count} high-severity issues need prompt resolution"
        elif high_count > 0:
            return f"LOW RISK: {high_count} high-severity issues identified"
        else:
            return "MINIMAL RISK: No critical security issues detected"

    def _check_compliance(self, vulnerabilities: List[CodeIssue]) -> Dict[str, bool]:
        """Check compliance with security standards."""
        # Simplified compliance check
        has_injection_vulns = any('injection' in v.title.lower() for v in vulnerabilities)
        has_auth_issues = any('auth' in v.title.lower() for v in vulnerabilities)
        has_crypto_issues = any('crypto' in v.title.lower() or 'random' in v.title.lower() for v in vulnerabilities)

        return {
            'OWASP_A03_Injection': not has_injection_vulns,
            'OWASP_A07_Auth_Failures': not has_auth_issues,
            'OWASP_A02_Crypto_Failures': not has_crypto_issues
        }

    def _identify_optimization_opportunities(self, bottlenecks: List[CodeIssue]) -> List[str]:
        """Identify optimization opportunities."""
        opportunities = []

        if any('loop' in b.title.lower() for b in bottlenecks):
            opportunities.append("Optimize loop structures and algorithms")

        if any('query' in b.title.lower() or 'database' in b.title.lower() for b in bottlenecks):
            opportunities.append("Optimize database queries and reduce N+1 problems")

        if any('memory' in b.title.lower() for b in bottlenecks):
            opportunities.append("Implement memory management and resource cleanup")

        if not opportunities:
            opportunities.append("No major optimization opportunities identified")

        return opportunities

    def _estimate_performance_impact(self, bottlenecks: List[CodeIssue]) -> str:
        """Estimate performance impact."""
        critical_count = sum(1 for b in bottlenecks if b.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for b in bottlenecks if b.severity == IssueSeverity.HIGH)

        if critical_count > 0:
            return "HIGH IMPACT: Critical performance issues may cause significant slowdowns"
        elif high_count > 1:
            return "MEDIUM IMPACT: Multiple performance issues may affect user experience"
        elif high_count > 0:
            return "LOW IMPACT: Minor performance improvements possible"
        else:
            return "MINIMAL IMPACT: Performance appears adequate"

    def _generate_quality_suggestions(self, issues: List[CodeIssue]) -> List[str]:
        """Generate quality improvement suggestions."""
        suggestions = []

        if any('function' in i.title.lower() for i in issues):
            suggestions.append("Break down large functions into smaller, focused methods")

        if any('nesting' in i.title.lower() for i in issues):
            suggestions.append("Reduce code complexity and nesting depth")

        if any('naming' in i.title.lower() for i in issues):
            suggestions.append("Improve variable and function naming conventions")

        if any('duplicate' in i.title.lower() for i in issues):
            suggestions.append("Extract common code to reduce duplication")

        if not suggestions:
            suggestions.append("Code quality is good - minor improvements available")

        return suggestions[:3]

    def _estimate_technical_debt(self, issues: List[CodeIssue]) -> str:
        """Estimate technical debt."""
        total_issues = len(issues)
        critical_issues = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high_issues = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)

        # Simple estimation based on issue count and severity
        debt_hours = critical_issues * 4 + high_issues * 2 + (total_issues - critical_issues - high_issues) * 0.5

        if debt_hours > 20:
            return f"HIGH ({debt_hours:.1f} hours) - Significant refactoring needed"
        elif debt_hours > 10:
            return f"MEDIUM ({debt_hours:.1f} hours) - Moderate improvements needed"
        elif debt_hours > 5:
            return f"LOW ({debt_hours:.1f} hours) - Minor improvements recommended"
        else:
            return f"MINIMAL ({debt_hours:.1f} hours) - Code is well-maintained"

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def _update_stats(self, result: ComprehensiveAnalysis) -> None:
        """Update analyzer statistics."""
        self.stats['analyses_performed'] += 1
        self.stats['issues_found'] += len(result.security.vulnerabilities) + len(result.performance.bottlenecks) + len(result.quality.issues)
        self.stats['critical_issues'] += result.critical_issues_count
        self.stats['security_issues'] += len(result.security.vulnerabilities)
        self.stats['performance_issues'] += len(result.performance.bottlenecks)
        self.stats['quality_issues'] += len(result.quality.issues)

        # Update average score
        total_analyses = self.stats['analyses_performed']
        self.stats['average_score'] = (
            (self.stats['average_score'] * (total_analyses - 1) + result.overall_health_score) / total_analyses
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get analyzer statistics."""
        stats = self.stats.copy()

        # Calculate percentages
        if stats['analyses_performed'] > 0:
            stats['ai_percentage'] = (stats['ai_analyses'] / stats['analyses_performed']) * 100
            stats['fallback_percentage'] = (stats['fallback_analyses'] / stats['analyses_performed']) * 100
        else:
            stats['ai_percentage'] = 0.0
            stats['fallback_percentage'] = 0.0

        return stats


# Global analyzer instance
_global_analyzer: Optional[AICodeAnalyzer] = None


def get_code_analyzer() -> Optional[AICodeAnalyzer]:
    """Get global code analyzer."""
    return _global_analyzer


def set_code_analyzer(analyzer: AICodeAnalyzer) -> None:
    """Set global code analyzer."""
    global _global_analyzer
    _global_analyzer = analyzer
    logger.info("Set global AI code analyzer")


async def analyze_code(
    code: str,
    file_path: Optional[str] = None,
    language: Optional[str] = None,
    analysis_types: Optional[List[AnalysisType]] = None
) -> Optional[ComprehensiveAnalysis]:
    """Analyze code using global analyzer.

    Args:
        code: Code to analyze
        file_path: Optional file path
        language: Programming language
        analysis_types: Types of analysis to perform

    Returns:
        Comprehensive analysis result or None if no global analyzer
    """
    analyzer = get_code_analyzer()
    if analyzer:
        return await analyzer.analyze_code_async(code, file_path, language, analysis_types)
    return None
