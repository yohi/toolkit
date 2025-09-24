"""Unit tests for PersonaManager and DefaultPersonaGenerator classes."""

import os
import tempfile

import pytest
from coderabbit_fetcher.exceptions import PersonaLoadError
from coderabbit_fetcher.persona_manager import DefaultPersonaGenerator, PersonaManager


class TestPersonaManager:
    """Test cases for PersonaManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = PersonaManager()

        # Sample persona files content
        self.valid_persona = """# CodeRabbit Expert

You are an experienced software developer specialized in code review analysis.
Your role is to analyze CodeRabbit feedback and provide actionable improvements.

## Instructions
1. Analyze the provided CodeRabbit comments
2. Prioritize issues by severity
3. Provide specific solutions with code examples
4. Explain the rationale behind recommendations

## Output Format
- Use clear headings and bullet points
- Include file references and line numbers
- Provide before/after code examples when helpful
"""

        self.minimal_persona = (
            """You are a code reviewer. Analyze CodeRabbit comments and suggest fixes."""
        )

        self.japanese_persona = """# コードレビュー専門家

あなたは経験豊富なソフトウェア開発者です。CodeRabbitからのフィードバックを分析し、実用的な改善案を提供してください。

## 指示
1. 提供されたCodeRabbitコメントを分析
2. 問題を重要度順に優先付け
3. コード例を含む具体的な解決策を提供
4. 推奨事項の根拠を説明

## 出力形式
- 明確な見出しと箇条書きを使用
- ファイル参照と行番号を含める
- 有用な場合は修正前後のコード例を提供
"""

        self.invalid_short_persona = "Too short"

        self.invalid_empty_persona = ""

    def test_load_default_persona(self):
        """Test loading default persona when no file specified."""
        persona = self.manager.load_persona()

        assert isinstance(persona, str)
        assert len(persona) > 100  # Should be substantial
        assert "CodeRabbit" in persona
        assert "software engineer" in persona.lower()
        assert "# " in persona  # Should have markdown headers

    def test_load_persona_from_valid_file(self):
        """Test loading persona from valid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(self.valid_persona)
            f.flush()
            temp_path = f.name

        try:
            persona = self.manager.load_persona(temp_path)
            assert persona == self.valid_persona
        finally:
            os.unlink(temp_path)

    def test_load_persona_from_nonexistent_file(self):
        """Test loading persona from nonexistent file."""
        with pytest.raises(PersonaLoadError) as exc_info:
            self.manager.load_persona("/nonexistent/file.md")

        assert "not found" in str(exc_info.value)

    def test_load_persona_from_directory(self):
        """Test loading persona when path is directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(PersonaLoadError) as exc_info:
                self.manager.load_persona(temp_dir)

            assert "not a file" in str(exc_info.value)

    def test_load_persona_empty_file(self):
        """Test loading persona from empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(self.invalid_empty_persona)
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(PersonaLoadError) as exc_info:
                self.manager.load_persona(temp_path)

            assert "empty" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_load_persona_too_short(self):
        """Test loading persona with content too short."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(self.invalid_short_persona)
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(PersonaLoadError) as exc_info:
                self.manager.load_persona(temp_path)

            assert "too short" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_load_persona_minimal_valid(self):
        """Test loading minimal but valid persona."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(self.minimal_persona)
            f.flush()
            temp_path = f.name

        try:
            persona = self.manager.load_persona(temp_path)
            assert persona == self.minimal_persona
        finally:
            os.unlink(temp_path)

    def test_load_persona_japanese_content(self):
        """Test loading persona with Japanese content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(self.japanese_persona)
            f.flush()
            temp_path = f.name

        try:
            persona = self.manager.load_persona(temp_path)
            assert persona == self.japanese_persona
            assert "あなたは" in persona
            assert "CodeRabbit" in persona
        finally:
            os.unlink(temp_path)

    def test_persona_caching(self):
        """Test persona file caching functionality."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(self.valid_persona)
            f.flush()
            temp_path = f.name

        try:
            # First load
            persona1 = self.manager.load_persona(temp_path)

            # Check cache
            cache_info = self.manager.get_cache_info()
            assert temp_path in cache_info["cached_files"]
            assert cache_info["cache_size"] == 1

            # Second load should use cache
            persona2 = self.manager.load_persona(temp_path)
            assert persona1 == persona2

            # Cache should still have one entry
            cache_info = self.manager.get_cache_info()
            assert cache_info["cache_size"] == 1
        finally:
            os.unlink(temp_path)

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(self.valid_persona)
            f.flush()
            temp_path = f.name

        try:
            # Load and cache
            self.manager.load_persona(temp_path)
            assert self.manager.get_cache_info()["cache_size"] == 1

            # Clear cache
            self.manager.clear_cache()
            assert self.manager.get_cache_info()["cache_size"] == 0
        finally:
            os.unlink(temp_path)

    def test_load_persona_encoding_error(self):
        """Test loading persona with invalid encoding."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".md", delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b"\x80\x81\x82\x83")
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(PersonaLoadError) as exc_info:
                self.manager.load_persona(temp_path)

            assert "encoding" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_load_persona_permission_error(self):
        """Test loading persona with permission error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(self.valid_persona)
            f.flush()
            temp_path = f.name

        try:
            # Remove read permissions
            os.chmod(temp_path, 0o000)

            with pytest.raises(PersonaLoadError) as exc_info:
                self.manager.load_persona(temp_path)

            assert "Failed to read" in str(exc_info.value)
        finally:
            # Restore permissions and clean up
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)

    def test_get_cache_info(self):
        """Test cache information retrieval."""
        # Initial cache should be empty
        cache_info = self.manager.get_cache_info()
        assert cache_info["cached_files"] == []
        assert cache_info["cache_size"] == 0
        assert cache_info["total_characters"] == 0

        # Load a few personas
        personas = []
        for i, content in enumerate([self.valid_persona, self.minimal_persona]):
            with tempfile.NamedTemporaryFile(mode="w", suffix=f"_{i}.md", delete=False) as f:
                f.write(content)
                f.flush()  # Ensure content is written to disk
                personas.append(f.name)
            self.manager.load_persona(f.name)

        try:
            cache_info = self.manager.get_cache_info()
            assert cache_info["cache_size"] == 2
            assert len(cache_info["cached_files"]) == 2
            assert cache_info["total_characters"] > 0
        finally:
            for path in personas:
                os.unlink(path)


class TestDefaultPersonaGenerator:
    """Test cases for DefaultPersonaGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = DefaultPersonaGenerator()

    def test_generate_default_persona(self):
        """Test generation of default persona."""
        persona = self.generator.generate()

        assert isinstance(persona, str)
        assert len(persona) > 500  # Should be comprehensive

        # Check for Claude 4 best practices elements
        assert "# " in persona  # Should have headers
        assert "Role Definition" in persona or "役割" in persona
        assert "Task Instructions" in persona or "指示" in persona
        assert "Output Format" in persona or "出力形式" in persona

        # Check for CodeRabbit-specific content
        assert "CodeRabbit" in persona
        assert "code review" in persona.lower() or "コードレビュー" in persona
        assert "software engineer" in persona.lower() or "ソフトウェア開発者" in persona

    def test_generate_specialized_security_persona(self):
        """Test generation of security-specialized persona."""
        persona = self.generator.generate_specialized_persona("security")

        assert isinstance(persona, str)
        assert len(persona) > 500

        # Should contain base persona
        assert "CodeRabbit" in persona

        # Should contain security specialization
        assert "Security Specialization" in persona
        assert "OWASP" in persona
        assert "vulnerability" in persona.lower()
        assert "encryption" in persona.lower()

    def test_generate_specialized_performance_persona(self):
        """Test generation of performance-specialized persona."""
        persona = self.generator.generate_specialized_persona("performance")

        assert isinstance(persona, str)
        assert "Performance Specialization" in persona
        assert "optimization" in persona.lower()
        assert "scalability" in persona.lower()
        assert "algorithm" in persona.lower()

    def test_generate_specialized_frontend_persona(self):
        """Test generation of frontend-specialized persona."""
        persona = self.generator.generate_specialized_persona("frontend")

        assert isinstance(persona, str)
        assert "Frontend Specialization" in persona
        assert "React" in persona or "Vue" in persona or "Angular" in persona
        assert "accessibility" in persona.lower()
        assert "user experience" in persona.lower()

    def test_generate_specialized_backend_persona(self):
        """Test generation of backend-specialized persona."""
        persona = self.generator.generate_specialized_persona("backend")

        assert isinstance(persona, str)
        assert "Backend Specialization" in persona
        assert "API" in persona
        assert "database" in persona.lower()
        assert "microservices" in persona.lower()

    def test_generate_specialized_testing_persona(self):
        """Test generation of testing-specialized persona."""
        persona = self.generator.generate_specialized_persona("testing")

        assert isinstance(persona, str)
        assert "Testing Specialization" in persona
        assert "unit test" in persona.lower()
        assert "integration" in persona.lower()
        assert "automation" in persona.lower()

    def test_generate_specialized_unknown_specialization(self):
        """Test generation with unknown specialization falls back to default."""
        persona = self.generator.generate_specialized_persona("unknown")

        # Should return base persona without specialization
        assert isinstance(persona, str)
        assert "CodeRabbit" in persona
        assert "unknown Specialization" not in persona

    def test_generate_specialized_case_insensitive(self):
        """Test specialized persona generation is case insensitive."""
        persona_lower = self.generator.generate_specialized_persona("security")
        persona_upper = self.generator.generate_specialized_persona("SECURITY")
        persona_mixed = self.generator.generate_specialized_persona("Security")

        assert persona_lower == persona_upper == persona_mixed

    def test_get_available_specializations(self):
        """Test getting list of available specializations."""
        specializations = self.generator.get_available_specializations()

        assert isinstance(specializations, list)
        assert len(specializations) > 0

        expected = ["security", "performance", "frontend", "backend", "testing"]
        for spec in expected:
            assert spec in specializations

    def test_persona_structure_validation(self):
        """Test that generated personas follow proper structure."""
        persona = self.generator.generate()

        # Should start with a header
        assert persona.strip().startswith("#")

        # Should have multiple sections
        sections = persona.split("\n##")
        assert len(sections) > 3

        # Should end with a clear conclusion or ready statement
        assert "Ready" in persona or "ready" in persona

    def test_persona_length_consistency(self):
        """Test that persona length is consistent across generations."""
        persona1 = self.generator.generate()
        persona2 = self.generator.generate()

        # Should generate identical content (deterministic)
        assert persona1 == persona2

        # Should be substantial but not excessive
        assert 1000 <= len(persona1) <= 10000

    def test_persona_professional_tone(self):
        """Test that persona maintains professional tone."""
        persona = self.generator.generate()

        # Should not contain casual language
        casual_words = ["awesome", "cool", "super", "amazing", "fantastic"]
        persona_lower = persona.lower()

        for word in casual_words:
            assert word not in persona_lower

        # Should contain professional language
        professional_indicators = [
            "experienced",
            "expertise",
            "professional",
            "analysis",
            "recommendations",
            "best practices",
            "guidelines",
        ]

        found_professional = sum(1 for word in professional_indicators if word in persona_lower)
        assert found_professional >= 3  # Should have multiple professional indicators

    def test_all_specializations_valid(self):
        """Test that all available specializations generate valid personas."""
        available = self.generator.get_available_specializations()

        for specialization in available:
            persona = self.generator.generate_specialized_persona(specialization)

            # Basic validation
            assert isinstance(persona, str)
            assert len(persona) > 500
            assert "CodeRabbit" in persona
            assert f"{specialization.title()} Specialization" in persona

    def test_persona_claude4_compliance(self):
        """Test that persona follows Claude 4 best practices."""
        persona = self.generator.generate()

        # Should have clear role definition
        assert "Role Definition" in persona or "role" in persona.lower()

        # Should have specific task instructions
        assert "Task Instructions" in persona or "instructions" in persona.lower()

        # Should have clear output format
        assert "Output Format" in persona or "format" in persona.lower()

        # Should be structured with headers
        header_count = persona.count("#")
        assert header_count >= 5  # Multiple levels of organization

        # Should have actionable guidelines
        assert "Guidelines" in persona or "Approach" in persona
