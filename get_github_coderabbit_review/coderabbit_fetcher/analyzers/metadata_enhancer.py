"""
Enhanced metadata generator for CodeRabbit comments analysis.
"""

from collections import Counter
from typing import Any, Dict, List

from ..models import AnalyzedComments


class MetadataEnhancer:
    """Generates enhanced metadata for CodeRabbit analysis prompts."""

    def __init__(self) -> None:
        """Initialize metadata enhancer."""
        pass

    def generate_enhanced_metadata(
        self,
        analyzed_comments: AnalyzedComments,
        pr_info: Dict[str, Any],
        comment_counts: Dict[str, int],
    ) -> List[str]:
        """Generate enhanced metadata section for the prompt.

        Args:
            analyzed_comments: Analyzed CodeRabbit comments
            pr_info: PR information from GitHub API
            comment_counts: Comment counts by type

        Returns:
            List of metadata lines
        """
        metadata_lines = []

        # Basic comment statistics
        total_comments = comment_counts.get("total", 0)
        actionable = comment_counts.get("actionable", 0)
        nitpick = comment_counts.get("nitpick", 0)
        outside_diff = comment_counts.get("outside_diff", 0)

        metadata_lines.append(
            f"- **Total Comments**: {total_comments} ({actionable} Actionable, {nitpick} Nitpick, {outside_diff} Outside Diff Range)"
        )

        # File type analysis
        file_types = self._analyze_file_types(analyzed_comments, pr_info)
        metadata_lines.append(f"- **File Types**: {file_types}")

        # Technology stack detection
        tech_stack = self._detect_technology_stack(analyzed_comments, pr_info)
        metadata_lines.append(f"- **Technology Stack**: {tech_stack}")

        # Primary issues analysis
        primary_issues = self._analyze_primary_issues(analyzed_comments)
        metadata_lines.append(f"- **Primary Issues**: {primary_issues}")

        # Complexity level assessment
        complexity_level = self._assess_complexity_level(analyzed_comments, pr_info)
        metadata_lines.append(f"- **Complexity Level**: {complexity_level}")

        # Change impact scope
        impact_scope = self._analyze_change_impact_scope(analyzed_comments, pr_info)
        metadata_lines.append(f"- **Change Impact Scope**: {impact_scope}")

        # Testing requirements
        testing_requirements = self._determine_testing_requirements(analyzed_comments, pr_info)
        metadata_lines.append(f"- **Testing Requirements**: {testing_requirements}")

        # File distribution
        file_distribution = self._calculate_file_distribution(analyzed_comments, pr_info)
        metadata_lines.append(f"- **File Distribution**: {file_distribution}")

        # Priority distribution
        priority_distribution = self._calculate_priority_distribution(comment_counts)
        metadata_lines.append(f"- **Priority Distribution**: {priority_distribution}")

        # Risk assessment
        risk_assessment = self._assess_risk_level(analyzed_comments, pr_info, comment_counts)
        metadata_lines.append(f"- **Risk Assessment**: {risk_assessment}")

        # Estimated resolution time
        resolution_time = self._estimate_resolution_time(analyzed_comments, pr_info, comment_counts)
        metadata_lines.append(f"- **Estimated Resolution Time**: {resolution_time}")

        return metadata_lines

    def _analyze_file_types(
        self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]
    ) -> str:
        """Analyze file types involved in the PR."""
        file_extensions = set()

        # Extract from comments
        if hasattr(analyzed_comments, "review_comments"):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, "actionable_comments", []),
                    getattr(review, "nitpick_comments", []),
                    getattr(review, "outside_diff_comments", []),
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, "file_path", "")
                        if file_path and "." in file_path:
                            ext = file_path.split(".")[-1]
                            file_extensions.add(ext)

        # Map extensions to descriptions
        type_mapping = {
            "mk": "Makefile (.mk)",
            "sh": "Shell script (.sh)",
            "py": "Python (.py)",
            "js": "JavaScript (.js)",
            "ts": "TypeScript (.ts)",
            "yml": "YAML (.yml)",
            "yaml": "YAML (.yaml)",
            "json": "JSON (.json)",
            "md": "Markdown (.md)",
            "txt": "Text (.txt)",
        }

        descriptions = []
        for ext in sorted(file_extensions):
            descriptions.append(type_mapping.get(ext, f"{ext.upper()} (.{ext})"))

        return ", ".join(descriptions) if descriptions else "Mixed file types"

    def _detect_technology_stack(
        self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]
    ) -> str:
        """Detect technology stack from file types and content."""
        technologies = set()

        # Analyze file extensions and content
        if hasattr(analyzed_comments, "review_comments"):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, "actionable_comments", []),
                    getattr(review, "nitpick_comments", []),
                    getattr(review, "outside_diff_comments", []),
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, "file_path", "")
                        raw_content = getattr(comment, "raw_content", "")

                        # File-based detection
                        if file_path.endswith(".mk"):
                            technologies.add("Make build system")
                        elif file_path.endswith(".sh"):
                            technologies.add("shell scripting")
                        elif file_path.endswith(".py"):
                            technologies.add("Python")
                        elif file_path.endswith((".js", ".ts")):
                            technologies.add("JavaScript/TypeScript")

                        # Content-based detection
                        if "bun" in raw_content.lower():
                            technologies.add("bun package manager")
                        if "npm" in raw_content.lower():
                            technologies.add("npm")
                        if "docker" in raw_content.lower():
                            technologies.add("Docker")
                        if "kubernetes" in raw_content.lower():
                            technologies.add("Kubernetes")

        return ", ".join(sorted(technologies)) if technologies else "General development"

    def _analyze_primary_issues(self, analyzed_comments: AnalyzedComments) -> str:
        """Analyze primary issues from comment content."""
        issue_categories: Counter[str] = Counter()

        if hasattr(analyzed_comments, "review_comments"):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, "actionable_comments", []),
                    getattr(review, "nitpick_comments", []),
                    getattr(review, "outside_diff_comments", []),
                ]:
                    for comment in comment_list:
                        raw_content = getattr(comment, "raw_content", "").lower()

                        # Categorize issues
                        if any(term in raw_content for term in ["path", "directory", "hardcoded"]):
                            issue_categories["PATH handling"] += 1
                        if any(
                            term in raw_content
                            for term in ["command", "syntax", "shell", "makefile"]
                        ):
                            issue_categories["command syntax"] += 1
                        if any(
                            term in raw_content
                            for term in ["file", "existence", "check", "missing"]
                        ):
                            issue_categories["file existence checks"] += 1
                        if any(term in raw_content for term in ["backup", "date", "expansion"]):
                            issue_categories["variable expansion"] += 1
                        if any(term in raw_content for term in ["phony", "alias", "help"]):
                            issue_categories["build configuration"] += 1

        # Return top 3 issues
        top_issues = [issue for issue, _ in issue_categories.most_common(3)]
        return ", ".join(top_issues) if top_issues else "Code quality improvements"

    def _assess_complexity_level(
        self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]
    ) -> str:
        """Assess complexity level based on various factors."""
        complexity_score = 0

        # File count factor
        files_changed = pr_info.get("files_changed", 0)
        if files_changed > 10:
            complexity_score += 3
        elif files_changed > 5:
            complexity_score += 2
        elif files_changed > 2:
            complexity_score += 1

        # Lines changed factor
        lines_added = pr_info.get("lines_added", 0)
        lines_deleted = pr_info.get("lines_deleted", 0)
        total_lines = lines_added + lines_deleted

        if total_lines > 1000:
            complexity_score += 3
        elif total_lines > 500:
            complexity_score += 2
        elif total_lines > 100:
            complexity_score += 1

        # Comment complexity factor
        if hasattr(analyzed_comments, "review_comments"):
            actionable_count = 0
            for review in analyzed_comments.review_comments:
                actionable_count += len(getattr(review, "actionable_comments", []))

            if actionable_count > 5:
                complexity_score += 2
            elif actionable_count > 2:
                complexity_score += 1

        # Determine complexity level
        if complexity_score >= 6:
            return "High (complex system changes)"
        elif complexity_score >= 3:
            return "Medium (build system configuration)"
        else:
            return "Low (minor adjustments)"

    def _analyze_change_impact_scope(
        self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]
    ) -> str:
        """Analyze the scope of changes and their impact."""
        impact_areas = set()

        if hasattr(analyzed_comments, "review_comments"):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, "actionable_comments", []),
                    getattr(review, "nitpick_comments", []),
                    getattr(review, "outside_diff_comments", []),
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, "file_path", "")
                        raw_content = getattr(comment, "raw_content", "").lower()

                        # Categorize impact areas
                        if "install" in file_path or "install" in raw_content:
                            impact_areas.add("package installation")
                        if "setup" in file_path or "setup" in raw_content:
                            impact_areas.add("configuration management")
                        if any(term in raw_content for term in ["build", "make", "compile"]):
                            impact_areas.add("build automation")
                        if any(term in raw_content for term in ["script", "shell", "command"]):
                            impact_areas.add("script execution")
                        if any(term in raw_content for term in ["path", "environment", "variable"]):
                            impact_areas.add("environment configuration")

        return ", ".join(sorted(impact_areas)) if impact_areas else "General code improvements"

    def _determine_testing_requirements(
        self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]
    ) -> str:
        """Determine testing requirements based on changes."""
        requirements = []

        # Check file types for testing needs
        if hasattr(analyzed_comments, "review_comments"):
            has_scripts = False
            has_makefiles = False

            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, "actionable_comments", []),
                    getattr(review, "nitpick_comments", []),
                    getattr(review, "outside_diff_comments", []),
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, "file_path", "")
                        if file_path.endswith(".sh"):
                            has_scripts = True
                        elif file_path.endswith(".mk"):
                            has_makefiles = True

            if has_makefiles:
                requirements.append("Manual execution verification")
            if has_scripts:
                requirements.append("cross-platform compatibility")

        return ", ".join(requirements) if requirements else "Basic functionality testing"

    def _calculate_file_distribution(
        self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]
    ) -> str:
        """Calculate file distribution statistics."""
        file_counts: Counter[str] = Counter()

        if hasattr(analyzed_comments, "review_comments"):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, "actionable_comments", []),
                    getattr(review, "nitpick_comments", []),
                    getattr(review, "outside_diff_comments", []),
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, "file_path", "")
                        if file_path.endswith(".mk"):
                            file_counts["mk files"] += 1
                        elif file_path.endswith(".sh"):
                            file_counts["sh files"] += 1
                        elif file_path.endswith(".py"):
                            file_counts["py files"] += 1
                        else:
                            file_counts["other"] += 1

        # Format as "type: count" pairs
        distribution_parts = []
        for file_type, count in file_counts.most_common():
            distribution_parts.append(f"{file_type}: {count}")

        return ", ".join(distribution_parts) if distribution_parts else "mixed files: 1"

    def _calculate_priority_distribution(self, comment_counts: Dict[str, int]) -> str:
        """Calculate priority distribution based on comment types."""
        # Map comment types to priorities based on expected output
        actionable = comment_counts.get("actionable", 0)
        nitpick = comment_counts.get("nitpick", 0)
        outside_diff = comment_counts.get("outside_diff", 0)

        # Actionable comments are typically High priority
        # Nitpick comments are typically Medium priority
        # Outside diff comments vary but often Medium

        critical = 0  # Reserved for security issues
        high = actionable  # Actionable comments
        medium = nitpick + outside_diff  # Nitpick + Outside diff comments
        low = 0  # Minor style issues

        return f"Critical: {critical}, High: {high}, Medium: {medium}, Low: {low}"

    def _assess_risk_level(
        self,
        analyzed_comments: AnalyzedComments,
        pr_info: Dict[str, Any],
        comment_counts: Dict[str, int],
    ) -> str:
        """Assess risk level based on changes and issues."""
        risk_score = 0

        # Actionable comments increase risk
        actionable_count = comment_counts.get("actionable", 0)
        risk_score += actionable_count * 2

        # File types affect risk
        if hasattr(analyzed_comments, "review_comments"):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, "actionable_comments", []),
                    getattr(review, "nitpick_comments", []),
                    getattr(review, "outside_diff_comments", []),
                ]:
                    for comment in comment_list:
                        file_path = getattr(comment, "file_path", "")
                        raw_content = getattr(comment, "raw_content", "").lower()

                        # Build system changes are risky
                        if file_path.endswith(".mk"):
                            risk_score += 1

                        # Configuration changes have backward compatibility risks
                        if any(term in raw_content for term in ["config", "setup", "install"]):
                            risk_score += 1

        # Determine risk level
        if risk_score >= 8:
            return "High (system-wide impact, potential breaking changes)"
        elif risk_score >= 4:
            return "Medium (configuration changes, backward compatibility)"
        else:
            return "Low (minor improvements, low impact)"

    def _estimate_resolution_time(
        self,
        analyzed_comments: AnalyzedComments,
        pr_info: Dict[str, Any],
        comment_counts: Dict[str, int],
    ) -> str:
        """Estimate time required to resolve all issues."""
        time_score = 0

        # Base time per comment type
        actionable_count = comment_counts.get("actionable", 0)
        nitpick_count = comment_counts.get("nitpick", 0)

        # Actionable comments take more time
        time_score += actionable_count * 30  # 30 minutes each
        time_score += nitpick_count * 10  # 10 minutes each

        # Complexity factors
        if hasattr(analyzed_comments, "review_comments"):
            for review in analyzed_comments.review_comments:
                for comment_list in [
                    getattr(review, "actionable_comments", []),
                    getattr(review, "nitpick_comments", []),
                ]:
                    for comment in comment_list:
                        raw_content = getattr(comment, "raw_content", "").lower()

                        # Complex issues take longer
                        if any(
                            term in raw_content
                            for term in ["build system", "makefile", "shell script"]
                        ):
                            time_score += 15  # Additional complexity

        # Convert to human-readable time
        if time_score >= 240:  # 4+ hours
            return f"{time_score // 60} hours (build system expertise required)"
        elif time_score >= 120:  # 2+ hours
            return f"{time_score // 60}-{(time_score + 60) // 60} hours (build system expertise required)"
        elif time_score >= 60:  # 1+ hour
            return "1-2 hours (moderate complexity)"
        else:
            return "30-60 minutes (straightforward fixes)"
