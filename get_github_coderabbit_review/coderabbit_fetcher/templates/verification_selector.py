"""
Verification template selector for different project types.
"""

from typing import Any, Dict, List

from ..models import AnalyzedComments


class VerificationTemplateSelector:
    """Selects appropriate verification templates based on project type."""

    def __init__(self):
        """Initialize verification template selector."""
        self.templates = {
            "makefile": self._get_makefile_templates(),
            "shell": self._get_shell_templates(),
            "python": self._get_python_templates(),
            "javascript": self._get_javascript_templates(),
            "mixed": self._get_mixed_templates(),
        }

    def select_template(
        self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]
    ) -> List[str]:
        """Select appropriate verification template based on project type.

        Args:
            analyzed_comments: Analyzed CodeRabbit comments
            pr_info: PR information from GitHub API

        Returns:
            List of verification template lines
        """
        project_type = self._detect_project_type(analyzed_comments, pr_info)
        return self.templates.get(project_type, self.templates["mixed"])

    def _detect_project_type(
        self, analyzed_comments: AnalyzedComments, pr_info: Dict[str, Any]
    ) -> str:
        """Detect project type from file extensions and content."""
        file_extensions = set()
        content_indicators = set()

        # Analyze files from comments
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

                        # Extract file extensions
                        if "." in file_path:
                            ext = file_path.split(".")[-1]
                            file_extensions.add(ext)

                        # Extract content indicators
                        if "makefile" in raw_content or "make" in raw_content:
                            content_indicators.add("makefile")
                        if "shell" in raw_content or "bash" in raw_content or "sh" in raw_content:
                            content_indicators.add("shell")
                        if "python" in raw_content or "pip" in raw_content:
                            content_indicators.add("python")
                        if (
                            "javascript" in raw_content
                            or "npm" in raw_content
                            or "node" in raw_content
                        ):
                            content_indicators.add("javascript")

        # Determine primary project type
        if "mk" in file_extensions or "makefile" in content_indicators:
            if "sh" in file_extensions or "shell" in content_indicators:
                return "makefile"  # Makefile with shell scripts
            return "makefile"
        elif "sh" in file_extensions or "shell" in content_indicators:
            return "shell"
        elif "py" in file_extensions or "python" in content_indicators:
            return "python"
        elif (
            any(ext in file_extensions for ext in ["js", "ts"])
            or "javascript" in content_indicators
        ):
            return "javascript"
        else:
            return "mixed"

    def _get_makefile_templates(self) -> List[str]:
        """Get verification templates for Makefile projects."""
        return [
            "<verification_templates>",
            "**Actionable Comment Verification**:",
            "1. **Code Change**: Apply the suggested modification to the specified file and line range",
            "2. **Syntax Check**: Execute `make --dry-run <target>` to verify Makefile syntax correctness",
            "3. **Functional Test**: Run the affected make target to confirm it executes without errors",
            "4. **Success Criteria**: Exit code 0, expected output generated, no error messages",
            "",
            "**Nitpick Comment Verification**:",
            "1. **Style Improvement**: Apply the suggested style or quality enhancement",
            "2. **Consistency Check**: Verify the change maintains consistency with existing codebase patterns",
            "3. **Documentation Update**: Update relevant documentation if the change affects user-facing behavior",
            "4. **Success Criteria**: Improved readability, maintained functionality, no regressions",
            "",
            "**Build System Specific Verification**:",
            "1. **Dependency Check**: Verify all required tools (bun, gh, etc.) are available",
            "2. **Path Validation**: Confirm PATH modifications work across different shell environments",
            "3. **Cross-Platform Test**: Test on multiple platforms if applicable (Linux, macOS)",
            "4. **Success Criteria**: Consistent behavior across target environments",
            "</verification_templates>",
        ]

    def _get_shell_templates(self) -> List[str]:
        """Get verification templates for shell script projects."""
        return [
            "<verification_templates>",
            "**Actionable Comment Verification**:",
            "1. **Code Change**: Apply the suggested modification to the specified file and line range",
            "2. **Syntax Check**: Execute `bash -n <script>` to verify shell syntax correctness",
            "3. **Functional Test**: Run the script in a test environment to confirm it executes without errors",
            "4. **Success Criteria**: Exit code 0, expected output generated, no error messages",
            "",
            "**Nitpick Comment Verification**:",
            "1. **Style Improvement**: Apply the suggested style or quality enhancement",
            "2. **ShellCheck**: Run `shellcheck <script>` to verify shell best practices",
            "3. **Portability Test**: Test script on different shell environments (bash, zsh, etc.)",
            "4. **Success Criteria**: Improved readability, maintained functionality, no shell warnings",
            "",
            "**Shell Script Specific Verification**:",
            "1. **Environment Check**: Verify all required environment variables and tools are available",
            "2. **Permission Check**: Confirm script has proper execution permissions",
            "3. **Error Handling**: Test error conditions and ensure proper exit codes",
            "4. **Success Criteria**: Robust execution across different environments",
            "</verification_templates>",
        ]

    def _get_python_templates(self) -> List[str]:
        """Get verification templates for Python projects."""
        return [
            "<verification_templates>",
            "**Actionable Comment Verification**:",
            "1. **Code Change**: Apply the suggested modification to the specified file and line range",
            "2. **Syntax Check**: Execute `python -m py_compile <file>` to verify Python syntax correctness",
            '3. **Import Test**: Run `python -c "import <module>"` to confirm import resolution',
            "4. **Package Test**: Execute `python setup.py check` to validate package configuration",
            "5. **Success Criteria**: No syntax errors, successful imports, valid package metadata",
            "",
            "**Nitpick Comment Verification**:",
            "1. **Style Improvement**: Apply the suggested code quality or style enhancement",
            "2. **Lint Check**: Run `flake8` or `pylint` on modified files to verify style compliance",
            "3. **Type Check**: Execute `mypy <file>` if type hints are involved",
            "4. **Success Criteria**: Improved code quality metrics, no new lint warnings",
            "",
            "**Package Structure Verification**:",
            "1. **Build Test**: Execute `python setup.py bdist_wheel` to create distribution package",
            "2. **Install Test**: Run `pip install dist/*.whl` in clean environment",
            "3. **Import Test**: Verify `import <package>` works in installed environment",
            "4. **Dependency Check**: Confirm all dependencies are properly declared and installable",
            "5. **Success Criteria**: Successful package build, clean installation, working imports",
            "",
            "**Configuration File Verification**:",
            "1. **Syntax Check**: Validate YAML/JSON syntax using appropriate parser",
            "2. **Schema Validation**: Verify configuration structure matches expected schema",
            "3. **Environment Test**: Test configuration loading in different environments",
            "4. **Success Criteria**: Valid syntax, correct structure, successful loading",
            "</verification_templates>",
        ]

    def _get_javascript_templates(self) -> List[str]:
        """Get verification templates for JavaScript/TypeScript projects."""
        return [
            "<verification_templates>",
            "**Actionable Comment Verification**:",
            "1. **Code Change**: Apply the suggested modification to the specified file and line range",
            "2. **Syntax Check**: Execute `node --check <file>` to verify JavaScript syntax correctness",
            "3. **Type Check**: Run `tsc --noEmit` for TypeScript files to verify type correctness",
            "4. **Build Test**: Execute `npm run build` to confirm the project builds successfully",
            "5. **Success Criteria**: No syntax errors, successful type checking, clean build",
            "",
            "**Nitpick Comment Verification**:",
            "1. **Style Improvement**: Apply the suggested code quality or style enhancement",
            "2. **Lint Check**: Run `eslint <file>` to verify code style compliance",
            "3. **Format Check**: Execute `prettier --check <file>` to verify formatting",
            "4. **Success Criteria**: Improved code quality metrics, no new lint warnings",
            "",
            "**Package Management Verification**:",
            "1. **Dependency Check**: Run `npm audit` to check for security vulnerabilities",
            "2. **Install Test**: Execute `npm ci` in clean environment to verify dependencies",
            "3. **Script Test**: Run relevant npm scripts to verify functionality",
            "4. **Success Criteria**: No security issues, successful installation, working scripts",
            "</verification_templates>",
        ]

    def _get_mixed_templates(self) -> List[str]:
        """Get verification templates for mixed or unknown project types."""
        return [
            "<verification_templates>",
            "**Actionable Comment Verification**:",
            "1. **Code Change**: Apply the suggested modification to the specified file and line range",
            "2. **Syntax Check**: Use appropriate syntax checker for the file type",
            "3. **Functional Test**: Run relevant tests to confirm changes work as expected",
            "4. **Success Criteria**: No syntax errors, passing tests, expected behavior",
            "",
            "**Nitpick Comment Verification**:",
            "1. **Style Improvement**: Apply the suggested style or quality enhancement",
            "2. **Consistency Check**: Verify the change maintains consistency with existing codebase",
            "3. **Documentation Update**: Update relevant documentation if needed",
            "4. **Success Criteria**: Improved readability, maintained functionality, no regressions",
            "",
            "**General Verification**:",
            "1. **Build Check**: Run the project's build process to verify no breakage",
            "2. **Test Suite**: Execute the test suite to ensure no regressions",
            "3. **Integration Test**: Test the changes in a realistic environment",
            "4. **Success Criteria**: Successful build, passing tests, working integration",
            "</verification_templates>",
        ]
