# 📋 CodeRabbit Comment Fetcher - Usage Examples

This document provides comprehensive examples of how to use CodeRabbit Comment Fetcher in various scenarios.

## 🚀 Basic Usage Examples

### 1. Simple Analysis

```bash
# Basic PR analysis with default settings
coderabbit-fetch https://github.com/microsoft/vscode/pull/12345

# Save output to file
coderabbit-fetch https://github.com/microsoft/vscode/pull/12345 \
    --output-file vscode_pr_analysis.md
```

### 2. Different Output Formats

```bash
# Markdown format (default) - best for human reading
coderabbit-fetch https://github.com/facebook/react/pull/67890 \
    --output-format markdown \
    --output-file react_analysis.md

# JSON format - best for programmatic processing
coderabbit-fetch https://github.com/facebook/react/pull/67890 \
    --output-format json \
    --output-file react_analysis.json

# Plain text format - simple and lightweight
coderabbit-fetch https://github.com/facebook/react/pull/67890 \
    --output-format plain \
    --output-file react_analysis.txt
```

## 🎭 Persona-Based Analysis

### 3. Using Custom Personas

```bash
# Security-focused review
coderabbit-fetch https://github.com/django/django/pull/54321 \
    --persona-file examples/personas/security_expert.txt \
    --output-file security_review.md

# Architecture review
coderabbit-fetch https://github.com/kubernetes/kubernetes/pull/98765 \
    --persona-file examples/personas/senior_architect.txt \
    --output-format json \
    --output-file architecture_review.json

# Japanese language review
coderabbit-fetch https://github.com/owner/japanese-project/pull/123 \
    --persona-file examples/personas/japanese_reviewer.txt \
    --output-file japanese_review.md
```

### 4. Creating Custom Persona Files

Create a file named `my_custom_persona.txt`:

```text
You are a DevOps Engineer with expertise in CI/CD, infrastructure, and deployment automation.

## Focus Areas
- Deployment pipeline optimization
- Infrastructure as code
- Monitoring and observability
- Security in CI/CD
- Performance optimization

## Review Style
- Focus on operational implications
- Consider scalability and reliability
- Evaluate monitoring and alerting
- Assess infrastructure changes
```

Then use it:

```bash
coderabbit-fetch https://github.com/owner/repo/pull/456 \
    --persona-file my_custom_persona.txt
```

## 🔧 Advanced Configuration

### 5. Custom Resolved Markers

```bash
# Filter comments with custom resolved marker
coderabbit-fetch https://github.com/owner/repo/pull/789 \
    --resolved-marker "✅ FIXED" \
    --output-format json

# Use emoji-based marker
coderabbit-fetch https://github.com/owner/repo/pull/789 \
    --resolved-marker "🔒 RESOLVED 🔒"
```

### 6. Performance Optimization

```bash
# For large PRs with many comments
coderabbit-fetch https://github.com/large-project/repo/pull/1001 \
    --timeout 120 \
    --retry-attempts 5 \
    --output-format json \
    --show-stats

# With debug information for troubleshooting
coderabbit-fetch https://github.com/owner/repo/pull/1002 \
    --debug \
    --show-stats \
    --timeout 60
```

### 7. Comment Posting and Resolution

```bash
# Post resolution requests to unresolved comments
coderabbit-fetch https://github.com/owner/repo/pull/1003 \
    --post-resolution-request \
    --output-file analysis_with_requests.md

# Combined with custom persona and formatting
coderabbit-fetch https://github.com/owner/repo/pull/1004 \
    --persona-file examples/personas/senior_architect.txt \
    --post-resolution-request \
    --output-format json \
    --show-stats
```

## 🏢 Enterprise Scenarios

### 8. Automated Review Pipeline

Create a script `automated_review.sh`:

```bash
#!/bin/bash

PR_URL="$1"
REVIEW_TYPE="${2:-default}"
OUTPUT_DIR="${3:-./reviews}"

# Ensure output directory exists
mkdir -p "$OUTPUT_DIR"

# Select persona based on review type
case "$REVIEW_TYPE" in
    "security")
        PERSONA_FILE="examples/personas/security_expert.txt"
        ;;
    "architecture")
        PERSONA_FILE="examples/personas/senior_architect.txt"
        ;;
    "japanese")
        PERSONA_FILE="examples/personas/japanese_reviewer.txt"
        ;;
    *)
        PERSONA_FILE="examples/personas/default_reviewer.txt"
        ;;
esac

# Extract PR number for filename
PR_NUMBER=$(echo "$PR_URL" | grep -o 'pull/[0-9]*' | cut -d'/' -f2)
OUTPUT_FILE="$OUTPUT_DIR/pr_${PR_NUMBER}_${REVIEW_TYPE}_review.json"

# Run analysis
coderabbit-fetch "$PR_URL" \
    --persona-file "$PERSONA_FILE" \
    --output-format json \
    --output-file "$OUTPUT_FILE" \
    --show-stats \
    --timeout 120

echo "Review completed: $OUTPUT_FILE"
```

Usage:
```bash
# Default review
./automated_review.sh https://github.com/owner/repo/pull/123

# Security review
./automated_review.sh https://github.com/owner/repo/pull/123 security

# Architecture review
./automated_review.sh https://github.com/owner/repo/pull/123 architecture ./architecture_reviews
```

### 9. Batch Processing Multiple PRs

Create `batch_review.py`:

```python
#!/usr/bin/env python3

import subprocess
import sys
import json
from pathlib import Path

def analyze_pr(pr_url, persona_file=None, output_dir="./batch_reviews"):
    """Analyze a single PR and return results."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Extract PR info for filename
    parts = pr_url.split('/')
    owner, repo, pr_number = parts[-4], parts[-3], parts[-1]
    
    output_file = output_dir / f"{owner}_{repo}_pr_{pr_number}.json"
    
    cmd = [
        "coderabbit-fetch", pr_url,
        "--output-format", "json",
        "--output-file", str(output_file),
        "--show-stats"
    ]
    
    if persona_file:
        cmd.extend(["--persona-file", persona_file])
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {
            "pr_url": pr_url,
            "success": result.returncode == 0,
            "output_file": str(output_file),
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "pr_url": pr_url,
            "success": False,
            "error": "Timeout after 5 minutes"
        }

def main():
    pr_urls = [
        "https://github.com/owner/repo/pull/101",
        "https://github.com/owner/repo/pull/102", 
        "https://github.com/owner/repo/pull/103"
    ]
    
    results = []
    for pr_url in pr_urls:
        print(f"Analyzing {pr_url}...")
        result = analyze_pr(pr_url, "examples/personas/default_reviewer.txt")
        results.append(result)
        
        if result["success"]:
            print(f"✅ Completed: {result['output_file']}")
        else:
            print(f"❌ Failed: {result.get('error', 'Unknown error')}")
    
    # Summary report
    successful = [r for r in results if r["success"]]
    print(f"\n📊 Batch Summary: {len(successful)}/{len(results)} successful")

if __name__ == "__main__":
    main()
```

Usage:
```bash
python batch_review.py
```

## 🐳 Docker Integration

### 10. Docker Container Usage

Create `Dockerfile`:

```dockerfile
FROM python:3.13-slim

# Install GitHub CLI
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null && \
    apt-get update && apt-get install -y gh

# Install CodeRabbit Comment Fetcher
RUN pip install coderabbit-comment-fetcher[full]

# Set working directory
WORKDIR /app

# Copy persona files
COPY examples/personas/ /app/personas/

ENTRYPOINT ["coderabbit-fetch"]
```

Build and use:

```bash
# Build container
docker build -t coderabbit-fetcher .

# Run with GitHub authentication
docker run -it --rm \
    -v ~/.config/gh:/root/.config/gh:ro \
    -v $(pwd)/output:/app/output \
    coderabbit-fetcher \
    https://github.com/owner/repo/pull/123 \
    --persona-file /app/personas/default_reviewer.txt \
    --output-file /app/output/analysis.json \
    --output-format json
```

## 🔄 CI/CD Integration

### 11. GitHub Actions Workflow

Create `.github/workflows/coderabbit-analysis.yml`:

```yaml
name: CodeRabbit Analysis

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
    
    - name: Install GitHub CLI
      run: |
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
        sudo apt update && sudo apt install gh
    
    - name: Install CodeRabbit Fetcher
      run: pip install coderabbit-comment-fetcher[full]
    
    - name: Authenticate with GitHub
      run: echo "${{ secrets.GITHUB_TOKEN }}" | gh auth login --with-token
    
    - name: Analyze CodeRabbit Comments
      run: |
        coderabbit-fetch ${{ github.event.pull_request.html_url }} \
          --output-format json \
          --output-file coderabbit-analysis.json \
          --show-stats
    
    - name: Upload Analysis Results
      uses: actions/upload-artifact@v3
      with:
        name: coderabbit-analysis
        path: coderabbit-analysis.json
```

### 12. GitLab CI Pipeline

Create `.gitlab-ci.yml`:

```yaml
stages:
  - analyze

coderabbit_analysis:
  stage: analyze
  image: python:3.13-slim
  
  before_script:
    # Install GitHub CLI
    - apt-get update && apt-get install -y curl
    - curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    - echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    - apt-get update && apt-get install -y gh
    
    # Install CodeRabbit Fetcher
    - pip install coderabbit-comment-fetcher[full]
    
    # Authenticate (requires GITHUB_TOKEN variable)
    - echo "$GITHUB_TOKEN" | gh auth login --with-token
  
  script:
    - |
      if [ "$CI_PIPELINE_SOURCE" = "merge_request_event" ]; then
        # Convert GitLab MR to GitHub PR URL (if mirrored)
        GITHUB_PR_URL="https://github.com/$CI_PROJECT_NAMESPACE/$CI_PROJECT_NAME/pull/$CI_MERGE_REQUEST_IID"
        
        coderabbit-fetch "$GITHUB_PR_URL" \
          --output-format json \
          --output-file coderabbit-analysis.json \
          --show-stats
      fi
  
  artifacts:
    paths:
      - coderabbit-analysis.json
    expire_in: 1 week
  
  only:
    - merge_requests
```

## 🧪 Testing and Development

### 13. Development Testing

```bash
# Test with different scenarios
coderabbit-fetch https://github.com/owner/small-repo/pull/1 \
    --debug --show-stats

coderabbit-fetch https://github.com/owner/large-repo/pull/999 \
    --timeout 180 --show-stats

# Test error handling
coderabbit-fetch https://github.com/nonexistent/repo/pull/1
coderabbit-fetch invalid-url
```

### 14. Performance Testing

```bash
# Test with large PR
time coderabbit-fetch https://github.com/microsoft/vscode/pull/12345 \
    --output-format json \
    --show-stats

# Memory usage monitoring
/usr/bin/time -v coderabbit-fetch https://github.com/large-project/repo/pull/999 \
    --output-format json
```

## 📊 Output Processing Examples

### 15. Processing JSON Output

Python script to process results:

```python
import json

# Load analysis results
with open('analysis.json', 'r') as f:
    data = json.load(f)

# Extract statistics
metadata = data['metadata']
comments = data['comments']

print(f"PR #{metadata['pr_number']}: {metadata['title']}")
print(f"Total comments: {len(comments)}")

# Group by type
by_type = {}
for comment in comments:
    comment_type = comment.get('type', 'unknown')
    by_type[comment_type] = by_type.get(comment_type, 0) + 1

print("\nComments by type:")
for comment_type, count in sorted(by_type.items()):
    print(f"  {comment_type}: {count}")

# Find unresolved issues
unresolved = [c for c in comments if not c.get('resolved', False)]
print(f"\nUnresolved issues: {len(unresolved)}")
```

### 16. Markdown Processing

```bash
# Convert to HTML
pandoc analysis.md -o analysis.html

# Extract specific sections
grep -A 10 "## 🛠️ Refactor Suggestions" analysis.md

# Count different comment types
grep -c "### ⚠️ Potential Issues" analysis.md
```

These examples demonstrate the flexibility and power of CodeRabbit Comment Fetcher across various use cases, from simple one-off analysis to complex enterprise automation workflows.
