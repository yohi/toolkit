"""
Integration test to verify uvx output matches expected PR #38 prompt.
"""

import subprocess
from pathlib import Path

import pytest


class TestPR38ExactMatch:
    """Test uvx output matches expected PR #38 AI agent prompt."""

    @pytest.fixture
    def expected_content(self):
        """Load expected PR #38 prompt content."""
        expected_file = (
            Path(__file__).parent.parent / "pr38" / "expected" / "expected_pr_38_ai_agent_prompt.md"
        )
        with open(expected_file, encoding="utf-8") as f:
            return f.read()

    @pytest.fixture
    def uvx_output(self):
        """Run uvx command and capture output."""
        # Change to project root directory
        project_root = Path(__file__).parent.parent.parent

        try:
            result = subprocess.run(
                [
                    "uvx",
                    "--from",
                    ".",
                    "-n",
                    "crf",
                    "https://github.com/yohi/dots/pull/38",
                    "--quiet",
                ],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode != 0:
                pytest.fail(
                    f"uvx command failed with return code {result.returncode}. "
                    f"stderr: {result.stderr}"
                )

            return result.stdout

        except subprocess.TimeoutExpired:
            pytest.fail("uvx command timed out after 120 seconds")
        except FileNotFoundError:
            pytest.skip("uvx not available in test environment")

    def test_uvx_output_structure_matches_expected(self, uvx_output, expected_content):
        """Test that uvx output has the same structure as expected content."""
        # Split content into lines for comparison
        uvx_lines = uvx_output.strip().split("\n")
        expected_lines = expected_content.strip().split("\n")

        # Check major sections exist
        uvx_sections = self._extract_sections(uvx_lines)
        expected_sections = self._extract_sections(expected_lines)

        # Verify all expected sections are present
        for section in expected_sections:
            assert section in uvx_sections, f"Missing section: {section}"

    def test_uvx_output_pr_context_matches(self, uvx_output, expected_content):
        """Test that PR context information matches expected values."""
        uvx_pr_context = self._extract_pr_context(uvx_output)
        expected_pr_context = self._extract_pr_context(expected_content)

        # Check key PR information (these should be dynamically fetched, not hardcoded)
        assert uvx_pr_context.get("url") == expected_pr_context.get("url")

        # These should be dynamically fetched from GitHub API
        assert uvx_pr_context.get("title") is not None
        assert uvx_pr_context.get("author") is not None
        assert uvx_pr_context.get("branch") is not None

    def test_uvx_output_comment_counts_match(self, uvx_output, expected_content):
        """Test that comment counts match expected values."""
        uvx_counts = self._extract_comment_counts(uvx_output)
        expected_counts = self._extract_comment_counts(expected_content)

        # These counts should match exactly
        assert uvx_counts.get("total") == expected_counts.get(
            "total"
        ), f"Total comments mismatch: {uvx_counts.get('total')} vs {expected_counts.get('total')}"
        assert uvx_counts.get("actionable") == expected_counts.get(
            "actionable"
        ), f"Actionable comments mismatch: {uvx_counts.get('actionable')} vs {expected_counts.get('actionable')}"
        assert uvx_counts.get("nitpick") == expected_counts.get(
            "nitpick"
        ), f"Nitpick comments mismatch: {uvx_counts.get('nitpick')} vs {expected_counts.get('nitpick')}"
        assert uvx_counts.get("outside_diff") == expected_counts.get(
            "outside_diff"
        ), f"Outside diff comments mismatch: {uvx_counts.get('outside_diff')} vs {expected_counts.get('outside_diff')}"

    def test_uvx_output_has_enhanced_metadata(self, uvx_output):
        """Test that uvx output includes enhanced metadata sections."""
        # Check for enhanced metadata sections
        assert "<comment_metadata>" in uvx_output
        assert "File Distribution:" in uvx_output
        assert "Priority Distribution:" in uvx_output
        assert "Risk Assessment:" in uvx_output
        assert "Estimated Resolution Time:" in uvx_output

    def test_uvx_output_has_verification_templates(self, uvx_output):
        """Test that uvx output includes appropriate verification templates."""
        # Should have verification templates for Makefile projects
        assert "<verification_templates>" in uvx_output
        assert "Actionable Comment Verification:" in uvx_output
        assert "make --dry-run" in uvx_output or "Makefile syntax" in uvx_output

    def test_uvx_output_no_hardcoded_content(self, uvx_output):
        """Test that uvx output doesn't contain hardcoded PR-specific content."""
        # These should NOT be hardcoded
        hardcoded_patterns = [
            "claude周り更新",  # Should be fetched from GitHub API
            "yohi",  # Should be fetched from GitHub API
            "feature/claude",  # Should be fetched from GitHub API
        ]

        # Check that these appear in the output (meaning they were fetched dynamically)
        # but also verify they're in the right context (PR Context section)
        pr_context_section = self._extract_pr_context_section(uvx_output)

        for pattern in hardcoded_patterns:
            if pattern in uvx_output:
                # If it appears, it should be in the PR Context section (dynamic fetch)
                assert (
                    pattern in pr_context_section
                ), f"Pattern '{pattern}' found outside PR Context section - may be hardcoded"

    def test_uvx_output_deterministic_processing(self, uvx_output):
        """Test that uvx output shows deterministic processing framework."""
        # Should include deterministic processing framework
        assert "<deterministic_processing_framework>" in uvx_output
        assert "コメントタイプ抽出" in uvx_output
        assert "キーワードマッチング" in uvx_output
        assert "security_keywords" in uvx_output
        assert "functionality_keywords" in uvx_output

    def _extract_sections(self, lines):
        """Extract major sections from content lines."""
        sections = []
        for line in lines:
            if line.startswith("#") and not line.startswith("###"):
                sections.append(line.strip())
            elif line.startswith("<") and line.endswith(">") and not line.startswith("</"):
                sections.append(line.strip())
        return sections

    def _extract_pr_context(self, content):
        """Extract PR context information from content."""
        context = {}
        lines = content.split("\n")

        for line in lines:
            if line.startswith("**PR URL**:"):
                context["url"] = line.split(":", 1)[1].strip()
            elif line.startswith("**PR Title**:"):
                context["title"] = line.split(":", 1)[1].strip()
            elif line.startswith("**Author**:"):
                context["author"] = line.split(":", 1)[1].strip()
            elif line.startswith("**Branch**:"):
                context["branch"] = line.split(":", 1)[1].strip()

        return context

    def _extract_comment_counts(self, content):
        """Extract comment counts from content."""
        counts = {}
        lines = content.split("\n")

        for line in lines:
            if "**Total Comments**:" in line:
                # Parse format: "**Total Comments**: 8 (3 Actionable, 5 Nitpick, 0 Outside Diff Range)"
                parts = line.split(":")[1].strip()
                if "(" in parts:
                    total_part = parts.split("(")[0].strip()
                    counts["total"] = int(total_part)

                    details_part = parts.split("(")[1].replace(")", "")
                    for detail in details_part.split(","):
                        detail = detail.strip()
                        if "Actionable" in detail:
                            counts["actionable"] = int(detail.split()[0])
                        elif "Nitpick" in detail:
                            counts["nitpick"] = int(detail.split()[0])
                        elif "Outside Diff" in detail:
                            counts["outside_diff"] = int(detail.split()[0])

        return counts

    def _extract_pr_context_section(self, content):
        """Extract the PR Context section from content."""
        lines = content.split("\n")
        in_pr_context = False
        pr_context_lines = []

        for line in lines:
            if line.strip() == "## Pull Request Context":
                in_pr_context = True
                continue
            elif line.startswith("##") and in_pr_context:
                # End of PR Context section
                break
            elif in_pr_context:
                pr_context_lines.append(line)

        return "\n".join(pr_context_lines)

    def test_uvx_execution_performance(self, uvx_output):
        """Test that uvx execution completes within reasonable time."""
        # This test is implicitly covered by the timeout in uvx_output fixture
        # If we get here, execution completed within 120 seconds
        assert len(uvx_output) > 1000, "Output should be substantial (>1000 characters)"

    def test_uvx_output_encoding_and_format(self, uvx_output):
        """Test that uvx output has proper encoding and format."""
        # Should be valid UTF-8
        assert isinstance(uvx_output, str)

        # Should contain markdown formatting
        assert "# CodeRabbit Review Analysis - AI Agent Prompt" in uvx_output
        assert "**" in uvx_output  # Bold formatting
        assert "```" in uvx_output or "<" in uvx_output  # Code blocks or XML tags
