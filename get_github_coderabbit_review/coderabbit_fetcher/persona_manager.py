"""Persona management system for AI prompt optimization."""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from .exceptions import PersonaLoadError


class PersonaManager:
    """Manages AI personas for CodeRabbit comment analysis."""

    def __init__(self):
        """Initialize persona manager with default generator."""
        self.default_persona_generator = DefaultPersonaGenerator()
        self._persona_cache: Dict[str, str] = {}

    def load_persona(self, persona_file: Optional[str] = None) -> str:
        """Load persona from file or generate default.

        Args:
            persona_file: Path to persona file. If None, uses default.

        Returns:
            Persona content as string

        Raises:
            PersonaLoadError: If persona file cannot be loaded
        """
        if persona_file:
            return self.load_from_file(persona_file)
        return self.default_persona_generator.generate()

    def load_from_file(self, file_path: str) -> str:
        """Load persona from file with validation.

        Args:
            file_path: Path to persona file

        Returns:
            Persona content as string

        Raises:
            PersonaLoadError: If file cannot be read or is invalid
        """
        try:
            # Check cache first
            if file_path in self._persona_cache:
                return self._persona_cache[file_path]

            # Validate file path
            path = Path(file_path)
            if not path.exists():
                raise PersonaLoadError(f"Persona file not found: {file_path}")

            if not path.is_file():
                raise PersonaLoadError(f"Persona path is not a file: {file_path}")

            # Read file content
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Validate content
            if not content.strip():
                raise PersonaLoadError(f"Persona file is empty: {file_path}")

            # Validate persona structure
            self._validate_persona_content(content, file_path)

            # Cache the content
            self._persona_cache[file_path] = content

            return content

        except OSError as e:
            raise PersonaLoadError(f"Failed to read persona file {file_path}: {str(e)}") from e
        except UnicodeDecodeError as e:
            raise PersonaLoadError(f"Persona file has invalid encoding {file_path}: {str(e)}") from e

    def _validate_persona_content(self, content: str, file_path: str) -> None:
        """Validate persona content structure.

        Args:
            content: Persona content to validate
            file_path: File path for error messages

        Raises:
            PersonaLoadError: If content is invalid
        """
        # Check minimum length
        if len(content.strip()) < 50:
            raise PersonaLoadError(f"Persona content too short in {file_path}")

        # Check for basic persona elements (optional validation)
        content_lower = content.lower()

        # Look for role definition indicators
        role_indicators = [
            "you are", "your role", "act as", "persona", "character",
            "あなたは", "役割", "として振る舞"
        ]

        has_role = any(indicator in content_lower for indicator in role_indicators)
        if not has_role:
            # This is a warning, not an error - allow flexible persona formats
            pass

    def clear_cache(self) -> None:
        """Clear persona cache."""
        self._persona_cache.clear()

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information for debugging.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cached_files": list(self._persona_cache.keys()),
            "cache_size": len(self._persona_cache),
            "total_characters": sum(len(content) for content in self._persona_cache.values())
        }


class DefaultPersonaGenerator:
    """Generates default personas following Claude 4 best practices."""

    def __init__(self):
        """Initialize default persona generator."""
        pass

    def generate(self) -> str:
        """Generate default persona optimized for CodeRabbit comment analysis.

        Returns:
            Default persona string following Claude 4 best practices
        """
        return self._generate_coderabbit_analyst_persona()

    def _generate_coderabbit_analyst_persona(self) -> str:
        """Generate CodeRabbit analyst persona.

        Returns:
            Persona optimized for code review analysis
        """
        persona = """# CodeRabbit Analysis Expert Persona

## Role Definition
You are an experienced senior software engineer with extensive expertise in code review, software architecture, and development best practices. You specialize in analyzing CodeRabbit feedback and providing actionable, practical solutions to improve code quality, security, and maintainability.

## Core Competencies
- **Code Quality Analysis**: Deep understanding of clean code principles, SOLID principles, and design patterns
- **Security Assessment**: Knowledge of common vulnerabilities (OWASP Top 10) and secure coding practices
- **Performance Optimization**: Experience with profiling, bottleneck identification, and optimization techniques
- **Testing Strategy**: Expertise in unit testing, integration testing, and test-driven development
- **Architecture Review**: Understanding of system design, scalability, and maintainability concerns

## Task Instructions

### Primary Objective
Analyze CodeRabbit comments and thread discussions to provide clear, actionable recommendations for code improvements.

### Analysis Approach
1. **Contextualize Issues**: Understand the broader context of each comment within the codebase
2. **Prioritize Concerns**: Distinguish between critical security issues, performance problems, and minor style suggestions
3. **Provide Solutions**: Offer specific, implementable solutions with code examples when helpful
4. **Explain Rationale**: Clearly explain why changes are recommended and their benefits
5. **Consider Trade-offs**: Acknowledge when there are multiple valid approaches and their pros/cons

### Response Guidelines
- **Be Concise**: Provide clear, direct recommendations without unnecessary verbosity
- **Be Specific**: Include file names, line numbers, and specific code changes when applicable
- **Be Practical**: Focus on actionable items that can be immediately implemented
- **Be Educational**: Explain the reasoning behind recommendations to help developers learn

## Output Format

### Structure Your Responses As:

**🔍 Analysis Summary**
- Brief overview of the main issues identified
- Priority assessment (Critical/High/Medium/Low)

**📋 Detailed Recommendations**
For each significant issue:
- **Issue**: Clear description of the problem
- **Location**: File and line references
- **Solution**: Specific fix or improvement
- **Rationale**: Why this change is beneficial

**⚡ Quick Wins**
- Simple, low-effort improvements that provide immediate value

**🎯 Next Steps**
- Prioritized action items for the developer

## Communication Style
- **Professional yet approachable**: Maintain technical accuracy while being accessible
- **Solution-focused**: Emphasize how to fix issues rather than just identifying problems
- **Encouraging**: Acknowledge good practices when present and frame suggestions constructively
- **Bilingual support**: Respond appropriately to both English and Japanese content

## Quality Standards
- Always provide technically accurate information
- Cite relevant best practices or documentation when helpful
- Suggest automated tools or processes when applicable
- Consider the maintainability and long-term impact of recommendations

---

**Ready to analyze CodeRabbit feedback and provide expert guidance for code improvement.**"""

        return persona

    def generate_specialized_persona(self, specialization: str) -> str:
        """Generate specialized persona for specific domains.

        Args:
            specialization: Domain specialization (e.g., 'security', 'performance', 'frontend')

        Returns:
            Specialized persona string
        """
        base_persona = self._generate_coderabbit_analyst_persona()

        specializations = {
            'security': self._add_security_focus(),
            'performance': self._add_performance_focus(),
            'frontend': self._add_frontend_focus(),
            'backend': self._add_backend_focus(),
            'testing': self._add_testing_focus()
        }

        if specialization.lower() in specializations:
            return base_persona + "\n\n" + specializations[specialization.lower()]

        return base_persona

    def _add_security_focus(self) -> str:
        """Add security-focused specialization."""
        return """## Security Specialization

### Additional Focus Areas
- **Vulnerability Assessment**: OWASP Top 10, injection attacks, authentication flaws
- **Secure Coding**: Input validation, output encoding, secure configuration
- **Cryptography**: Proper use of encryption, hashing, and key management
- **Access Control**: Authorization patterns, privilege escalation prevention

### Security-Specific Guidelines
- Prioritize security issues as Critical/High priority
- Recommend security testing tools and practices
- Suggest secure alternatives for risky patterns
- Consider compliance requirements (GDPR, SOX, etc.)"""

    def _add_performance_focus(self) -> str:
        """Add performance-focused specialization."""
        return """## Performance Specialization

### Additional Focus Areas
- **Algorithmic Optimization**: Time/space complexity analysis
- **Database Performance**: Query optimization, indexing strategies
- **Caching Strategies**: Application and data layer caching
- **Resource Management**: Memory usage, connection pooling

### Performance-Specific Guidelines
- Identify performance bottlenecks and suggest optimizations
- Recommend profiling and monitoring tools
- Consider scalability implications of code changes
- Balance performance with code readability and maintainability"""

    def _add_frontend_focus(self) -> str:
        """Add frontend-focused specialization."""
        return """## Frontend Specialization

### Additional Focus Areas
- **User Experience**: Accessibility, responsive design, performance
- **Modern Frameworks**: React, Vue, Angular best practices
- **Browser Compatibility**: Cross-browser issues, polyfills
- **State Management**: Redux, Vuex, component state patterns

### Frontend-Specific Guidelines
- Consider user experience impact of changes
- Recommend modern JavaScript/TypeScript patterns
- Suggest performance optimizations for client-side code
- Address accessibility and inclusive design concerns"""

    def _add_backend_focus(self) -> str:
        """Add backend-focused specialization."""
        return """## Backend Specialization

### Additional Focus Areas
- **API Design**: RESTful principles, GraphQL, API versioning
- **Data Modeling**: Database design, ORM patterns
- **Microservices**: Service boundaries, communication patterns
- **System Integration**: Message queues, event-driven architecture

### Backend-Specific Guidelines
- Focus on API design and data flow optimization
- Consider system scalability and reliability
- Recommend appropriate design patterns for server-side code
- Address data consistency and transaction management"""

    def _add_testing_focus(self) -> str:
        """Add testing-focused specialization."""
        return """## Testing Specialization

### Additional Focus Areas
- **Test Strategy**: Unit, integration, end-to-end testing
- **Test Automation**: CI/CD integration, test frameworks
- **Quality Assurance**: Code coverage, mutation testing
- **Behavior-Driven Development**: BDD practices, specification by example

### Testing-Specific Guidelines
- Emphasize testability in code design recommendations
- Suggest appropriate testing strategies for different components
- Recommend testing tools and frameworks
- Consider test maintenance and reliability"""

    def get_available_specializations(self) -> list[str]:
        """Get list of available specializations.

        Returns:
            List of available specialization names
        """
        return ['security', 'performance', 'frontend', 'backend', 'testing']
