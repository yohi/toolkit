# 🤖 CodeRabbit Comment Fetcher

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uvx Compatible](https://img.shields.io/badge/uvx-compatible-green)](https://github.com/astral-sh/uv)

Professional tool to fetch, analyze, and format CodeRabbit comments from GitHub Pull Requests with AI-agent optimization and Claude 4 best practices compliance.

## ✨ Features

### 🔍 **Advanced Comment Analysis**
- **Intelligent CodeRabbit Detection**: Automatically identifies and filters CodeRabbit comments
- **Thread Processing**: Analyzes comment threads and chronological relationships
- **Resolved Marker Management**: Detects and filters resolved comments with configurable markers
- **Comment Classification**: Categorizes comments by type (suggestions, issues, documentation, etc.)

### 🛡️ **Enterprise-Grade Security**
- **GitHub CLI Integration**: Secure API access using authenticated GitHub CLI
- **Input Validation**: Comprehensive URL and parameter validation
- **Command Injection Prevention**: Safe subprocess execution with proper sanitization
- **No Token Storage**: Relies on GitHub CLI authentication, never stores tokens

### 📊 **Multiple Output Formats**
- **Markdown**: Rich formatting with headers, code blocks, and organization
- **JSON**: Structured data for programmatic processing
- **Plain Text**: Simple, readable format for basic use cases

### 🎭 **AI-Agent Optimization**
- **Persona Support**: Custom AI persona files for tailored output
- **Claude 4 Best Practices**: Optimized prompts and formatting for Claude 4
- **AI Agent Prompts**: Extracts and formats "Prompt for AI Agents" sections
- **Contextual Analysis**: Provides rich context for AI processing

### ⚡ **Performance & Reliability**
- **Large Dataset Support**: Efficiently processes PRs with hundreds of comments
- **Retry Logic**: Automatic retry with exponential backoff for transient failures
- **Memory Optimization**: Streaming processing for large comment datasets
- **Parallel Processing**: Concurrent analysis for improved performance

### 🌍 **Multi-Language Support**
- **Unicode Handling**: Full support for Unicode characters and emojis
- **Japanese Support**: Native Japanese language support
- **Mixed Content**: Handles mixed-language content gracefully

## 🚀 Quick Start

### Installation with uvx (Recommended)

```bash
# Install and run directly with uvx
uvx coderabbit-comment-fetcher https://github.com/owner/repo/pull/123

# With custom options
uvx coderabbit-comment-fetcher https://github.com/owner/repo/pull/123 \
    --output-format json \
    --output-file results.json
```

### Installation with pip

```bash
# Install from PyPI
pip install coderabbit-comment-fetcher

# Basic usage
coderabbit-fetch https://github.com/owner/repo/pull/123

# With full features
pip install "coderabbit-comment-fetcher[full]"
```

### From Source (Local Development)

```bash
git clone https://github.com/yohi/toolkit.git
cd toolkit
python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/owner/repo/pull/123
```

**Note**: Always run commands from the repository root (`toolkit` directory) to ensure proper module resolution.

### Prerequisites

1. **Python 3.13+** - Required for all features
2. **GitHub CLI** - Install from [cli.github.com](https://cli.github.com/)
3. **GitHub Authentication** - Run `gh auth login` to authenticate

```bash
# Install GitHub CLI (macOS)
brew install gh

# Install GitHub CLI (Linux)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Authenticate with GitHub
gh auth login
```

## 📖 Usage

### Basic Usage

**Prerequisites**: Ensure you're in the repository root directory (`toolkit`) for local development, or use the installed package.

#### With Installed Package

```bash
# Analyze a pull request
coderabbit-fetch https://github.com/owner/repo/pull/123

# Save to file
coderabbit-fetch https://github.com/owner/repo/pull/123 --output-file analysis.md

# Use JSON format
coderabbit-fetch https://github.com/owner/repo/pull/123 --output-format json
```

#### From Source (Local Development)

```bash
# Authenticate with GitHub CLI
gh auth login

# Fetch CodeRabbit comments
python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/owner/repo/pull/123

# Generate JSON output
python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/owner/repo/pull/123 --output-format json

# Use custom persona
python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/owner/repo/pull/123 --persona-file my-persona.txt
```

### Advanced Usage

```bash
# With custom persona file
coderabbit-fetch https://github.com/owner/repo/pull/123 \
    --persona-file my_reviewer_persona.txt \
    --output-format markdown \
    --output-file detailed_analysis.md

# Filter resolved comments
coderabbit-fetch https://github.com/owner/repo/pull/123 \
    --resolved-marker "✅ RESOLVED" \
    --show-stats

# Post resolution requests
coderabbit-fetch https://github.com/owner/repo/pull/123 \
    --post-resolution-request \
    --timeout 60

# Debug mode with verbose output
coderabbit-fetch https://github.com/owner/repo/pull/123 \
    --debug \
    --show-stats
```

### Command Line Options

| Option                      | Description                                     | Default                   |
| --------------------------- | ----------------------------------------------- | ------------------------- |
| `pr_url`                    | GitHub pull request URL                         | Required                  |
| `--persona-file`            | Path to persona file for AI context             | None                      |
| `--output-format`           | Output format: `markdown`, `json`, `plain`      | `markdown`                |
| `--output-file`             | Output file path                                | stdout                    |
| `--resolved-marker`         | Custom resolved marker string                   | `🔒 CODERABBIT_RESOLVED 🔒` |
| `--post-resolution-request` | Post resolution requests to unresolved comments | False                     |
| `--timeout`                 | Network timeout in seconds                      | 30                        |
| `--retry-attempts`          | Number of retry attempts                        | 3                         |
| `--retry-delay`             | Delay between retries in seconds                | 1.0                       |
| `--show-stats`              | Show execution statistics                       | False                     |
| `--debug`                   | Enable debug mode                               | False                     |
| `--version`                 | Show version information                        | -                         |
| `--help`                    | Show help message                               | -                         |

## 🎭 Persona Files

Persona files allow you to customize the AI context and output style. Create a text file with your desired persona:

### Example Persona File

```text
You are a Senior Software Architect with 15+ years of experience.

## Expertise
- Microservices architecture design
- Performance optimization
- Security best practices
- Code review and quality assurance

## Review Style
- Focus on architectural implications
- Provide specific, actionable feedback
- Consider long-term maintainability
- Evaluate security and performance impact

## Communication
- Be direct and constructive
- Use technical terms appropriately
- Provide code examples when helpful
- Prioritize critical issues first
```

### Persona Best Practices

1. **Be Specific**: Define expertise areas and review focus
2. **Set Tone**: Establish communication style and approach
3. **Include Context**: Add relevant background and priorities
4. **Keep Concise**: Aim for 200-500 words for optimal results

## 📊 Output Examples

### Markdown Output

```markdown
# 🤖 CodeRabbit Comments Analysis

## 📋 Pull Request Information
- **Number**: 123
- **Title**: Refactor authentication system
- **Status**: Open

## 🎯 Summary
Found 15 CodeRabbit comments across 8 files, with 3 resolved and 12 requiring attention.

## 📝 Detailed Comments

### 🛠️ Refactor Suggestions (5)

#### `src/auth/login.py:45`
**Suggestion**: Extract authentication logic into separate service class...

### ⚠️ Potential Issues (7)

#### `src/auth/token.py:23`
**Issue**: Potential security vulnerability in token validation...
```

### JSON Output

```json
{
  "metadata": {
    "pr_number": 123,
    "title": "Refactor authentication system",
    "analyzed_at": "2025-01-28T12:00:00Z",
    "total_comments": 15,
    "resolved_comments": 3,
    "unresolved_comments": 12
  },
  "comments": [
    {
      "id": 123456,
      "type": "refactor_suggestion",
      "file": "src/auth/login.py",
      "line": 45,
      "body": "Extract authentication logic...",
      "resolved": false,
      "created_at": "2025-01-28T10:30:00Z"
    }
  ],
  "statistics": {
    "by_type": {
      "refactor_suggestion": 5,
      "potential_issue": 7,
      "documentation": 3
    },
    "by_file": {
      "src/auth/login.py": 3,
      "src/auth/token.py": 4
    }
  }
}
```

## 🧪 Development

### Development Setup

```bash
# Clone repository
git clone https://github.com/yohi/coderabbit-comment-fetcher.git
cd coderabbit-comment-fetcher

# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov=coderabbit_fetcher --cov-report=html

# Format code
black coderabbit_fetcher tests
isort coderabbit_fetcher tests

# Type checking
mypy coderabbit_fetcher

# Lint code
ruff check coderabbit_fetcher tests
```

### Running Tests

```bash
# Run all tests
python tests/test_runner.py

# Run specific test types
python tests/test_runner.py --type unit
python tests/test_runner.py --type integration
python tests/test_runner.py --type performance

# Generate test report
python tests/test_runner.py --report test_results.html

# Run with coverage
python tests/test_runner.py --coverage
```

### Project Structure

```
coderabbit_fetcher/
├── __init__.py              # Package initialization and metadata
├── cli/                     # Command-line interface
│   ├── __init__.py
│   └── main.py             # Main CLI entry point
├── comment_analyzer.py      # Comment analysis and filtering
├── github_client.py         # GitHub CLI integration
├── orchestrator.py          # Main workflow orchestration
├── validation.py            # Input validation and error handling
├── resolved_marker.py       # Resolved marker management
├── comment_poster.py        # Comment posting functionality
├── exceptions/              # Exception hierarchy
│   ├── __init__.py
│   ├── base.py
│   ├── auth.py
│   ├── network.py
│   └── ...
├── formatters/              # Output formatters
│   ├── __init__.py
│   ├── base.py
│   ├── markdown.py
│   ├── json.py
│   └── plain.py
└── models/                  # Data models
    ├── __init__.py
    └── comment.py
```

## 🔧 Advanced Configuration

### Environment Variables

```bash
# GitHub CLI path (if not in PATH)
export GITHUB_CLI_PATH="/usr/local/bin/gh"

# Default timeout
export CODERABBIT_TIMEOUT=60

# Default output format
export CODERABBIT_OUTPUT_FORMAT="json"

# Enable debug mode
export CODERABBIT_DEBUG=1
```

### Configuration File

Create `~/.coderabbit-fetcher.toml`:

```toml
[defaults]
output_format = "markdown"
timeout = 60
retry_attempts = 5
show_stats = true

[persona]
default_file = "~/.config/coderabbit/default_persona.txt"

[github]
cli_path = "/usr/local/bin/gh"
timeout = 30

[output]
include_metadata = true
include_statistics = true
```

### Testing

```bash
# Run all tests
pytest

# Run tests excluding slow performance tests
pytest -m "not slow"

# Run only unit tests
pytest tests/unit/

# Run CI-safe tests (no external dependencies)
pytest tests/test_github_client_safe.py

# Run legacy test suite (from get_github_coderabbit_review directory)
cd get_github_coderabbit_review && python test_github_api_refactor.py

# Run with coverage
pytest --cov=coderabbit_fetcher --cov-report=html
```

#### CI-Safe Testing

The project includes comprehensive CI-safe tests that work without external dependencies:

- **`tests/test_github_client_safe.py`**: Pytest-based test suite with full mocking
- **`test_github_api_refactor.py`**: Legacy test suite with enhanced mocking

Both test suites use extensive mocking to avoid:
- GitHub CLI (gh) installation requirements
- GitHub authentication dependencies
- Network connectivity requirements
- External service dependencies

**Key Features:**
- ✅ Works in Docker containers
- ✅ Works in GitHub Actions
- ✅ Works in restricted environments
- ✅ No authentication required
- ✅ No network access required

#### Performance Tests

Performance tests are marked with `@pytest.mark.slow` and `@pytest.mark.performance` and can be resource-intensive. They are designed to be robust in CI environments but can be controlled with environment variables:

**Skip performance tests in CI:**
```bash
export CI_LOW_RESOURCE=true
# or
export SKIP_PERF_TESTS=true
pytest  # Performance tests will be automatically skipped
```

**Run only performance tests:**
```bash
pytest -m "slow and performance"
```

**Run tests excluding performance tests:**
```bash
pytest -m "not performance"
```

**Configure performance test thresholds:**
```bash
# Set custom threshold (default: 3.0s local, 5.0s CI)
export PERF_TEST_THRESHOLD=2.0
pytest -m performance
```

Performance tests focus on functional correctness and log timing information rather than enforcing strict timing constraints to prevent flaky CI failures.

### API Refactoring Test

Run the comprehensive API refactoring test:

```bash
cd get_github_coderabbit_review
python test_github_api_refactor.py
```

This test suite includes:

#### 🧪 **Enhanced API Method Testing**
- **HTTP Layer Mocking**: All GitHub API calls are properly mocked
- **Real Method Calls**: Tests actually call `GitHubClient.post_comment()` and `GitHubClient.get_comment()`
- **Response Structure Validation**: Ensures all expected fields are present with correct types
- **API Endpoint Verification**: Confirms correct URLs, headers, and HTTP methods are used

#### 🔍 **Comprehensive Error Handling**
- **HTTP Error Responses**: Tests 401, 403, 404, 500 error scenarios
- **JSON Parsing Errors**: Malformed and empty response handling
- **Network Timeouts**: Command and network timeout scenarios
- **Authentication Failures**: Various auth failure modes during operations

#### ✅ **Assertion-Based Testing**
- **Field Existence**: Verifies all required fields are present in responses
- **Type Validation**: Ensures correct data types for each field
- **Value Verification**: Checks specific field values and structures
- **Regression Prevention**: Tests fail on missing fields or incorrect structures

### Code Quality

## 🚨 Troubleshooting

### Common Issues

#### GitHub Authentication

```bash
# Check authentication status
gh auth status

# Re-authenticate if needed
gh auth login --git-protocol https

# Check API limits
gh api rate_limit
```

#### Permission Issues

```bash
# Check repository access
gh repo view owner/repo

# Verify PR access
gh pr view 123 --repo owner/repo
```

#### Performance Issues

```bash
# Use JSON format for large PRs
coderabbit-fetch URL --output-format json

# Increase timeout for large datasets
coderabbit-fetch URL --timeout 120

# Enable parallel processing
coderabbit-fetch URL --show-stats
```

### Error Messages

| Error                     | Cause                         | Solution                           |
| ------------------------- | ----------------------------- | ---------------------------------- |
| `GitHub CLI not found`    | gh not installed              | Install GitHub CLI                 |
| `Authentication required` | Not logged in to GitHub       | Run `gh auth login`                |
| `Rate limit exceeded`     | Too many API calls            | Wait or use authenticated requests |
| `PR not found`            | Invalid URL or private repo   | Check URL and permissions          |
| `Timeout exceeded`        | Large dataset or slow network | Increase `--timeout` value         |

### Debug Mode

Enable debug mode for detailed logging:

```bash
coderabbit-fetch URL --debug
```

This provides:
- Detailed API call information
- Processing time metrics
- Memory usage statistics
- Error stack traces
- Validation details

## 📋 API Reference

### Programmatic Usage

```python
from coderabbit_fetcher import CodeRabbitOrchestrator, ExecutionConfig

# Create configuration
config = ExecutionConfig(
    pr_url="https://github.com/owner/repo/pull/123",
    output_format="json",
    persona_file="my_persona.txt"
)

# Execute analysis
orchestrator = CodeRabbitOrchestrator(config)
results = orchestrator.execute()

if results["success"]:
    print("Analysis completed successfully")
    print(f"Processed {results['metrics']['comments_processed']} comments")
else:
    print(f"Analysis failed: {results['error']}")
```

### Key Classes

- `CodeRabbitOrchestrator`: Main workflow orchestration
- `ExecutionConfig`: Configuration management
- `GitHubClient`: GitHub CLI integration
- `CommentAnalyzer`: Comment analysis and filtering
- `MarkdownFormatter`, `JsonFormatter`, `PlainFormatter`: Output formatting

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Run the test suite: `pytest`
5. Format code: `black . && isort .`
6. Submit a pull request

### Code Standards

- **Python 3.13+** compatibility
- **Type hints** for all functions
- **Comprehensive tests** with >90% coverage
- **Clear documentation** with examples
- **Follow PEP 8** with 100-character line limit

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [CodeRabbit](https://coderabbit.ai/) for the excellent AI code review platform
- [GitHub CLI](https://cli.github.com/) for secure API access
- [Anthropic Claude](https://www.anthropic.com/) for AI-agent optimization insights
- [Python community](https://www.python.org/) for the excellent ecosystem

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yohi/coderabbit-comment-fetcher/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yohi/coderabbit-comment-fetcher/discussions)
- **Email**: coderabbit-fetcher@example.com

---

**Made with ❤️ for the developer community**
