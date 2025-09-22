"""Configuration constants for CodeRabbit Comment Fetcher."""

# Default values for various components
DEFAULT_RESOLVED_MARKER = "🔒 CODERABBIT_RESOLVED 🔒"

# Role and principles for AI agent prompts
DEFAULT_AI_ROLE = "You are a senior software engineer with 10+ years of experience specializing in code review, quality improvement, security vulnerability identification, performance optimization, architecture design, and testing strategies. You follow industry best practices and prioritize code quality, maintainability, and security."

DEFAULT_CORE_PRINCIPLES = [
    "Prioritize code quality, maintainability, and readability",
    "Always consider security and performance implications",
    "Follow industry best practices and standards",
    "Provide specific, implementable solutions",
    "Clearly explain the impact scope of changes"
]

DEFAULT_ANALYSIS_METHODOLOGY = [
    "**Problem Understanding**: Identify the core issue in the comment",
    "**Impact Assessment**: Analyze how the fix affects other parts of the system",
    "**Solution Evaluation**: Compare multiple approaches",
    "**Implementation Strategy**: Develop specific modification steps",
    "**Verification Method**: Propose testing and review policies"
]

# Progress tracking configuration
DEFAULT_PROGRESS_STEPS = [
    "Initializing components",
    "Validating GitHub CLI authentication",
    "Parsing and validating PR URL",
    "Loading persona configuration",
    "Fetching PR data from GitHub",
    "Analyzing CodeRabbit comments",
    "Formatting output",
    "Writing results"
]

# Output format configuration
SUPPORTED_OUTPUT_FORMATS = ['markdown', 'json', 'plain', 'llm-instruction', 'ai-agent-prompt']

# Logging configuration for quiet mode
QUIET_MODE_LOG_MODULES = [
    'coderabbit_fetcher.orchestrator',
    'coderabbit_fetcher.github_client',
    'coderabbit_fetcher.comment_analyzer',
    'coderabbit_fetcher.formatters.markdown_formatter',
    'coderabbit_fetcher.formatters.ai_agent_prompt_formatter'
]

# Performance configuration
DEFAULT_TOTAL_OPERATIONS = 5
DEFAULT_TIMEOUT_SECONDS = 300
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1.0

# Validation configuration
MIN_TIMEOUT_WARNING_THRESHOLD = 30
ZERO_OR_NEGATIVE_ERROR_MSG = "Value must be positive"
