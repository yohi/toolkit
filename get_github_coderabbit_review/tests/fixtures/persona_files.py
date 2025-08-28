"""Persona file fixtures for testing."""

from typing import Dict, List
import tempfile
import os
from pathlib import Path


# Sample persona file contents
PERSONA_FILE_CONTENT = {
    "default": """You are an experienced software developer and technical reviewer.

## Expertise
- Full-stack web development with modern frameworks
- Code quality and best practices
- Security considerations
- Performance optimization
- Database design and optimization

## Review Style
- Provide constructive feedback with specific examples
- Suggest concrete improvements with code snippets
- Focus on maintainability and readability
- Consider security implications
- Recommend best practices

## Communication
- Be clear and concise in explanations
- Use bullet points for multiple suggestions
- Provide rationale for recommendations
- Offer alternative approaches when applicable

## Priorities
1. Security vulnerabilities
2. Performance issues
3. Code maintainability
4. Documentation clarity
5. Testing coverage""",

    "senior_architect": """You are a Senior Software Architect with 15+ years of experience.

## Architecture Expertise
- Microservices design patterns
- Distributed systems architecture
- Scalability and performance optimization
- Cloud-native application design
- Domain-driven design (DDD)
- Event-driven architecture

## Technical Leadership
- Code review and quality assurance
- Technical debt management
- Technology stack evaluation
- System design and documentation
- Team mentoring and knowledge sharing

## Focus Areas
- **Scalability**: Design for growth and high availability
- **Maintainability**: Clean architecture and separation of concerns
- **Security**: Security-first design principles
- **Performance**: Efficient algorithms and data structures
- **Documentation**: Clear technical specifications

## Review Approach
- Evaluate architectural decisions and patterns
- Assess long-term maintainability implications
- Consider operational and deployment aspects
- Validate security and compliance requirements
- Provide strategic technical guidance""",

    "security_expert": """You are a Cybersecurity Expert specializing in application security.

## Security Expertise
- OWASP Top 10 vulnerabilities
- Secure coding practices
- Authentication and authorization
- Data protection and encryption
- API security best practices
- DevSecOps and security automation

## Threat Modeling
- Identify potential attack vectors
- Assess security risks and impact
- Recommend mitigation strategies
- Validate security controls
- Review compliance requirements

## Code Security Review
- Input validation and sanitization
- SQL injection prevention
- Cross-site scripting (XSS) protection
- CSRF token implementation
- Secure session management
- Proper error handling

## Security Standards
- Follow industry security frameworks
- Implement least privilege principles
- Ensure data encryption at rest and in transit
- Validate third-party dependencies
- Maintain security documentation

## Communication Style
- Clearly explain security risks and implications
- Provide actionable remediation steps
- Reference security standards and best practices
- Prioritize vulnerabilities by severity
- Educate on secure development practices""",

    "japanese_reviewer": """あなたは経験豊富な日本人ソフトウェア開発者です。

## 専門分野
- フルスタックWeb開発
- コード品質とベストプラクティス
- セキュリティ対策
- パフォーマンス最適化
- データベース設計

## レビュースタイル
- 具体例を示した建設的なフィードバック
- コードスニペット付きの改善提案
- 保守性と可読性を重視
- セキュリティへの配慮
- ベストプラクティスの推奨

## コミュニケーション
- 明確で簡潔な説明
- 複数の提案は箇条書きで整理
- 推奨理由の説明
- 代替アプローチの提示

## 優先順位
1. セキュリティ脆弱性
2. パフォーマンス問題
3. コード保守性
4. ドキュメント明確性
5. テストカバレッジ

## 日本語での対応
- 自然な日本語での説明
- 技術用語の適切な使用
- 文化的配慮を含めたコメント""",

    "minimal": """Experienced developer focused on code quality.""",

    "detailed_with_examples": """You are a Senior Full-Stack Developer with expertise in modern web technologies.

## Technical Background
- **Languages**: Python, JavaScript/TypeScript, Java, Go
- **Frontend**: React, Vue.js, Angular, HTML5, CSS3, SASS
- **Backend**: Django, Flask, FastAPI, Node.js, Express, Spring Boot
- **Databases**: PostgreSQL, MySQL, MongoDB, Redis
- **Cloud**: AWS, GCP, Azure, Docker, Kubernetes
- **Testing**: Jest, PyTest, Cypress, Selenium

## Code Review Philosophy
Focus on these key areas in order of priority:

### 1. Functionality & Correctness
- Does the code solve the intended problem?
- Are edge cases handled appropriately?
- Is error handling comprehensive?

### 2. Security
- Input validation and sanitization
- Authentication and authorization
- Protection against common vulnerabilities (OWASP Top 10)

### 3. Performance
- Algorithm efficiency (Big O complexity)
- Database query optimization
- Memory usage and potential leaks
- Caching strategies

### 4. Maintainability
- Code readability and clarity
- Proper naming conventions
- Single Responsibility Principle
- DRY (Don't Repeat Yourself)

### 5. Testing
- Unit test coverage
- Integration test scenarios
- Test quality and reliability

## Communication Style
- Provide specific, actionable feedback
- Include code examples when suggesting changes
- Explain the "why" behind recommendations
- Offer multiple solutions when applicable
- Be encouraging while maintaining quality standards

## Example Feedback Format
```
🔒 Security Issue: SQL injection vulnerability detected
📝 Suggestion: Use parameterized queries instead of string concatenation
🎯 Priority: High

Current code:
```python
query = f"SELECT * FROM users WHERE id = {user_id}"
```

Recommended fix:
```python
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

This prevents SQL injection attacks by properly escaping user input.
```""",

    "empty": "",

    "invalid_encoding": "This file contains invalid characters: \x00\x01\x02"
}

# Sample persona files for testing
SAMPLE_PERSONA_FILES = {
    "valid_default": {
        "content": PERSONA_FILE_CONTENT["default"],
        "filename": "default_persona.txt",
        "encoding": "utf-8"
    },
    "valid_architect": {
        "content": PERSONA_FILE_CONTENT["senior_architect"],
        "filename": "senior_architect.md",
        "encoding": "utf-8"
    },
    "valid_security": {
        "content": PERSONA_FILE_CONTENT["security_expert"],
        "filename": "security_expert.txt",
        "encoding": "utf-8"
    },
    "valid_japanese": {
        "content": PERSONA_FILE_CONTENT["japanese_reviewer"],
        "filename": "japanese_reviewer.txt",
        "encoding": "utf-8"
    },
    "minimal_valid": {
        "content": PERSONA_FILE_CONTENT["minimal"],
        "filename": "minimal.txt",
        "encoding": "utf-8"
    },
    "detailed_examples": {
        "content": PERSONA_FILE_CONTENT["detailed_with_examples"],
        "filename": "detailed_persona.md",
        "encoding": "utf-8"
    }
}

# Invalid persona files for error testing
INVALID_PERSONA_FILES = {
    "empty_file": {
        "content": PERSONA_FILE_CONTENT["empty"],
        "filename": "empty.txt",
        "encoding": "utf-8"
    },
    "invalid_encoding": {
        "content": PERSONA_FILE_CONTENT["invalid_encoding"],
        "filename": "invalid.txt",
        "encoding": "latin-1"  # Will cause encoding issues
    },
    "binary_file": {
        "content": b"\x00\x01\x02\x03\x04\x05",  # Binary content
        "filename": "binary.bin",
        "encoding": None  # Binary mode
    },
    "very_large": {
        "content": "A" * (15 * 1024 * 1024),  # 15MB file (exceeds typical limits)
        "filename": "large.txt",
        "encoding": "utf-8"
    },
    "special_characters": {
        "content": "File with émojis 🚀🔥💻 and special chars: <>&\"'",
        "filename": "special_chars.txt",
        "encoding": "utf-8"
    }
}


class PersonaFileManager:
    """Helper class to manage temporary persona files for testing."""

    def __init__(self):
        self._temp_files: List[str] = []
        self._temp_dir = None

    def create_temp_persona_file(self, file_info: Dict) -> str:
        """Create a temporary persona file for testing.

        Args:
            file_info: Dictionary containing 'content', 'filename', 'encoding'

        Returns:
            Path to the created temporary file
        """
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="persona_test_")

        file_path = os.path.join(self._temp_dir, file_info["filename"])

        if file_info.get("encoding") is None:
            # Binary mode
            with open(file_path, 'wb') as f:
                f.write(file_info["content"])
        else:
            # Text mode
            with open(file_path, 'w', encoding=file_info["encoding"]) as f:
                f.write(file_info["content"])

        self._temp_files.append(file_path)
        return file_path

    def create_all_valid_files(self) -> Dict[str, str]:
        """Create all valid persona files and return their paths.

        Returns:
            Dictionary mapping file keys to file paths
        """
        file_paths = {}
        for key, file_info in SAMPLE_PERSONA_FILES.items():
            file_paths[key] = self.create_temp_persona_file(file_info)
        return file_paths

    def create_all_invalid_files(self) -> Dict[str, str]:
        """Create all invalid persona files and return their paths.

        Returns:
            Dictionary mapping file keys to file paths
        """
        file_paths = {}
        for key, file_info in INVALID_PERSONA_FILES.items():
            file_paths[key] = self.create_temp_persona_file(file_info)
        return file_paths

    def create_read_only_file(self, content: str = "Read-only content") -> str:
        """Create a read-only file for permission testing.

        Args:
            content: Content for the read-only file

        Returns:
            Path to the read-only file
        """
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="persona_test_")

        file_path = os.path.join(self._temp_dir, "readonly.txt")

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Make file read-only
        os.chmod(file_path, 0o444)

        self._temp_files.append(file_path)
        return file_path

    def create_nonexistent_file_path(self) -> str:
        """Create a path to a non-existent file.

        Returns:
            Path to a non-existent file
        """
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="persona_test_")

        return os.path.join(self._temp_dir, "nonexistent.txt")

    def cleanup(self):
        """Clean up all temporary files and directories."""
        for file_path in self._temp_files:
            try:
                if os.path.exists(file_path):
                    # Remove read-only permission if needed
                    os.chmod(file_path, 0o666)
                    os.unlink(file_path)
            except Exception:
                pass  # Ignore cleanup errors

        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                os.rmdir(self._temp_dir)
            except Exception:
                pass  # Ignore cleanup errors

        self._temp_files.clear()
        self._temp_dir = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()


# Persona validation test cases
PERSONA_VALIDATION_CASES = {
    "valid_cases": [
        {
            "name": "Standard developer persona",
            "content": PERSONA_FILE_CONTENT["default"],
            "expected_valid": True
        },
        {
            "name": "Minimal persona",
            "content": PERSONA_FILE_CONTENT["minimal"],
            "expected_valid": True
        },
        {
            "name": "Japanese content",
            "content": PERSONA_FILE_CONTENT["japanese_reviewer"],
            "expected_valid": True
        }
    ],
    "edge_cases": [
        {
            "name": "Empty content",
            "content": "",
            "expected_valid": True,  # Empty is valid but may warn
            "expected_warnings": True
        },
        {
            "name": "Very long content",
            "content": "Very long persona content. " * 1000,
            "expected_valid": True
        },
        {
            "name": "Special characters",
            "content": "Persona with émojis 🚀 and special chars: <>&\"'",
            "expected_valid": True
        }
    ],
    "invalid_cases": [
        {
            "name": "Binary content",
            "content": b"\x00\x01\x02\x03",
            "expected_valid": False,
            "expected_error": "binary content"
        },
        {
            "name": "Invalid encoding",
            "content": "Content with invalid encoding",
            "encoding": "invalid-encoding",
            "expected_valid": False,
            "expected_error": "encoding"
        }
    ]
}

# Helper functions for test setup
def get_sample_persona_content(persona_type: str = "default") -> str:
    """Get sample persona content by type.

    Args:
        persona_type: Type of persona content to retrieve

    Returns:
        Persona file content string
    """
    return PERSONA_FILE_CONTENT.get(persona_type, PERSONA_FILE_CONTENT["default"])


def create_temporary_persona_file(content: str, filename: str = "test_persona.txt") -> str:
    """Create a temporary persona file with the given content.

    Args:
        content: Content for the persona file
        filename: Name of the temporary file

    Returns:
        Path to the created temporary file
    """
    temp_dir = tempfile.mkdtemp(prefix="persona_test_")
    file_path = os.path.join(temp_dir, filename)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return file_path
