# CodeRabbit Comment Fetcher

A Python tool for fetching and formatting CodeRabbit comments from GitHub pull requests. This tool efficiently collects and organizes automatic review comments from CodeRabbit, making it easier for developers to understand and act on review feedback.

## Features

- 🤖 **CodeRabbit Integration**: Automatically identifies and extracts CodeRabbit comments
- 📊 **Multiple Output Formats**: Supports Markdown, JSON, and plain text output
- 🎯 **AI-Optimized**: Structured output designed for AI agent consumption
- 🔍 **Smart Filtering**: Distinguishes between resolved and unresolved comments
- 📝 **Persona Support**: Custom persona files for AI context
- 🔐 **GitHub CLI Integration**: Secure authentication through GitHub CLI
- ⚡ **uvx Compatible**: Run directly with uvx without installation

## Requirements

- Python 3.13 or higher
- GitHub CLI (`gh`) installed and authenticated
- Access to the target GitHub repository

## Installation

### From Source (Local Development)

```bash
git clone https://github.com/yohi/toolkit.git
cd toolkit
python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/owner/repo/pull/123
```

**Note**: Always run commands from the repository root (`toolkit` directory) to ensure proper module resolution.

## Quick Start

**Prerequisites**: Ensure you're in the repository root directory (`toolkit`).

1. **Authenticate with GitHub CLI**:
   ```bash
   gh auth login
   ```

2. **Fetch CodeRabbit comments**:
   ```bash
   python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/owner/repo/pull/123
   ```

3. **Generate JSON output**:
   ```bash
   python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/owner/repo/pull/123 --output-format json
   ```

4. **Use custom persona**:
   ```bash
   python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/owner/repo/pull/123 --persona-file my-persona.txt
   ```

## Usage

**Important**: All commands must be run from the repository root directory (`toolkit`).

### Basic Command

```bash
python -m get_github_coderabbit_review.coderabbit_fetcher <PR_URL> [OPTIONS]
```

### Options

- `--persona-file, -p`: Path to persona file for AI context
- `--output-format, -f`: Output format (markdown, json, plain) [default: markdown]
- `--resolved-marker, -m`: Custom resolved marker string
- `--request-resolution, -r`: Post resolution request to CodeRabbit
- `--output-file, -o`: Save output to file instead of stdout
- `--verbose, -v`: Enable verbose output
- `--help, -h`: Show help message

### Examples

**Note**: Ensure you're in the `toolkit` directory before running these commands.

**Basic usage**:
```bash
python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/microsoft/vscode/pull/12345
```

**JSON output with custom persona**:
```bash
python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/microsoft/vscode/pull/12345 \
  --output-format json \
  --persona-file reviewer-persona.txt \
  --output-file review-summary.json
```

**Request resolution from CodeRabbit**:
```bash
python -m get_github_coderabbit_review.coderabbit_fetcher https://github.com/microsoft/vscode/pull/12345 \
  --request-resolution \
  --resolved-marker "✅ RESOLVED"
```

## Output Formats

### Markdown (Default)
Human-readable format with proper headings, lists, and code blocks:

```markdown
# CodeRabbit Review Summary

## Summary by CodeRabbit
- **New Features**: Added authentication system
- **Documentation**: Updated API documentation

## Actionable Comments (5)
### src/auth.py:23-25
**Issue**: Missing error handling for invalid credentials
...
```

### JSON
Structured data format for programmatic consumption:

```json
{
  "summary": {
    "new_features": ["Added authentication system"],
    "documentation": ["Updated API documentation"]
  },
  "actionable_comments": [
    {
      "file_path": "src/auth.py",
      "line_range": "23-25",
      "issue": "Missing error handling for invalid credentials"
    }
  ]
}
```

### Plain Text
Simple text format for basic consumption:

```
CodeRabbit Review Summary
========================

Summary:
- New Features: Added authentication system
- Documentation: Updated API documentation

Actionable Comments:
1. src/auth.py:23-25 - Missing error handling for invalid credentials
```

## Persona Files

Persona files provide context for AI agents processing the output. Create a text file with instructions:

```
You are an experienced software developer reviewing CodeRabbit feedback.

Focus on:
- Security vulnerabilities (highest priority)
- Performance issues
- Code maintainability
- Best practices compliance

Provide specific, actionable recommendations for each issue.
```

## Configuration

The tool can be configured through:

1. **Command line arguments** (highest priority)
2. **Environment variables**
3. **Default values**

### Environment Variables

- `CODERABBIT_RESOLVED_MARKER`: Default resolved marker
- `CODERABBIT_OUTPUT_FORMAT`: Default output format
- `CODERABBIT_PERSONA_FILE`: Default persona file path

## Error Handling

The tool provides clear error messages for common issues:

- **Authentication**: GitHub CLI not authenticated
- **Access**: Insufficient repository permissions
- **Network**: API rate limits or connectivity issues
- **Format**: Invalid PR URLs or file paths

## Development

### Setup Development Environment

```bash
git clone https://github.com/yohi/toolkit.git
cd toolkit
pip install -e "./get_github_coderabbit_review[dev]"
```

### Run Tests

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

```bash
black .
isort .
mypy .
flake8 .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📖 **Documentation**: [GitHub Wiki](https://github.com/yohi/coderabbit-comment-fetcher/wiki)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/yohi/coderabbit-comment-fetcher/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yohi/coderabbit-comment-fetcher/discussions)

## Acknowledgments

- [CodeRabbit](https://coderabbit.ai) for providing AI-powered code reviews
- [GitHub CLI](https://cli.github.com) for authentication and API access
- [Rich](https://rich.readthedocs.io) for beautiful terminal output
