# 🔧 CodeRabbit Comment Fetcher - Troubleshooting Guide

This comprehensive guide helps you diagnose and resolve common issues with CodeRabbit Comment Fetcher.

## 📋 Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Authentication Problems](#authentication-problems)
- [Permission Errors](#permission-errors)
- [Performance Issues](#performance-issues)
- [Output Problems](#output-problems)
- [Network and API Issues](#network-and-api-issues)
- [Configuration Problems](#configuration-problems)
- [Platform-Specific Issues](#platform-specific-issues)
- [Advanced Debugging](#advanced-debugging)

## 🩺 Quick Diagnostics

### System Health Check

Run this command to check your system setup:

```bash
# Quick system check
python scripts/test_uvx_installation.py
```

This will verify:
- ✅ Python 3.13+ availability
- ✅ uvx compatibility
- ✅ GitHub CLI installation
- ✅ Authentication status
- ✅ Package import compatibility

### Basic Troubleshooting Commands

```bash
# Check version
coderabbit-fetch --version

# Test with help (no authentication required)
coderabbit-fetch --help

# Debug mode for detailed logging
coderabbit-fetch <PR_URL> --debug

# Show execution statistics
coderabbit-fetch <PR_URL> --show-stats
```

## 📦 Installation Issues

### Issue: "Command not found: coderabbit-fetch"

**Symptoms:**
```bash
$ coderabbit-fetch --help
bash: coderabbit-fetch: command not found
```

**Solutions:**

1. **Check installation method:**
   ```bash
   # If using uvx
   uvx coderabbit-comment-fetcher --help

   # If using pip
   pip show coderabbit-comment-fetcher
   ```

2. **Reinstall package:**
   ```bash
   # With uvx (recommended)
   uvx install coderabbit-comment-fetcher

   # With pip
   pip install --upgrade coderabbit-comment-fetcher
   ```

3. **Check PATH:**
   ```bash
   # Find where pip installs scripts
   python -m site --user-base

   # Add to PATH if needed
   export PATH="$PATH:$(python -m site --user-base)/bin"
   ```

### Issue: "ModuleNotFoundError"

**Symptoms:**
```bash
ModuleNotFoundError: No module named 'coderabbit_fetcher'
```

**Solutions:**

1. **Verify installation:**
   ```bash
   pip list | grep coderabbit
   python -c "import coderabbit_fetcher; print(coderabbit_fetcher.__version__)"
   ```

2. **Install with dependencies:**
   ```bash
   pip install "coderabbit-comment-fetcher[full]"
   ```

3. **Check Python environment:**
   ```bash
   which python
   python --version
   pip --version
   ```

### Issue: "Python 3.13+ required"

**Symptoms:**
```bash
RuntimeWarning: CodeRabbit Comment Fetcher requires Python 3.13+
```

**Solutions:**

1. **Install Python 3.13+:**
   ```bash
   # macOS with Homebrew
   brew install python@3.13

   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.13

   # Windows - download from python.org
   ```

2. **Use virtual environment:**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   pip install coderabbit-comment-fetcher
   ```

## 🔐 Authentication Problems

### Issue: "GitHub CLI not found"

**Symptoms:**
```bash
❌ GitHub CLI not found: gh: command not found
```

**Solutions:**

1. **Install GitHub CLI:**
   ```bash
   # macOS
   brew install gh

   # Ubuntu/Debian
   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
   sudo apt update && sudo apt install gh

   # Windows with Chocolatey
   choco install gh

   # Windows with Scoop
   scoop install gh
   ```

2. **Verify installation:**
   ```bash
   gh --version
   which gh
   ```

### Issue: "Authentication required"

**Symptoms:**
```bash
❌ GitHub authentication required. Run: gh auth login
```

**Solutions:**

1. **Authenticate with GitHub:**
   ```bash
   gh auth login
   ```

   Follow the prompts to:
   - Choose authentication method (web browser recommended)
   - Select protocol (HTTPS recommended)
   - Grant permissions

2. **Check authentication status:**
   ```bash
   gh auth status
   ```

3. **Refresh authentication:**
   ```bash
   gh auth refresh
   ```

### Issue: "Permission denied"

**Symptoms:**
```bash
❌ Permission denied: repository access required
```

**Solutions:**

1. **Check repository access:**
   ```bash
   # Test repository access
   gh repo view owner/repository

   # Check if you can view the PR
   gh pr view 123 --repo owner/repository
   ```

2. **Request repository access:**
   - Contact repository owner
   - Check if repository is private
   - Verify you have at least read permissions

3. **Re-authenticate with correct scopes:**
   ```bash
   gh auth login --scopes "repo,read:org"
   ```

## 🚫 Permission Errors

### Issue: "PR not found" or "404 Not Found"

**Symptoms:**
```bash
❌ PR not found: Invalid URL or private repo
```

**Solutions:**

1. **Verify PR URL format:**
   ```bash
   # Correct format
   https://github.com/owner/repository/pull/123

   # Common mistakes to avoid
   https://github.com/owner/repository/pulls/123  # Wrong: "pulls" should be "pull"
   https://github.com/owner/repository/pull/123/ # Extra trailing slash might cause issues
   ```

2. **Check PR exists:**
   ```bash
   # Manual verification
   gh pr view 123 --repo owner/repository

   # Or visit in browser
   ```

3. **Check repository access:**
   ```bash
   # Test repository access
   gh repo view owner/repository

   # Check if repository is private
   gh api repos/owner/repository | jq .private
   ```

### Issue: "Rate limit exceeded"

**Symptoms:**
```bash
❌ API rate limit exceeded. Try again later
```

**Solutions:**

1. **Wait for rate limit reset:**
   ```bash
   # Check rate limit status
   gh api rate_limit

   # Wait for reset time
   ```

2. **Use authenticated requests:**
   ```bash
   # Ensure you're authenticated (higher rate limits)
   gh auth status

   # Re-authenticate if needed
   gh auth login
   ```

3. **Reduce API calls:**
   ```bash
   # Use longer timeout to reduce retries
   coderabbit-fetch <URL> --timeout 120

   # Reduce retry attempts
   coderabbit-fetch <URL> --retry-attempts 1
   ```

## ⚡ Performance Issues

### Issue: "Timeout exceeded"

**Symptoms:**
```bash
❌ Request timed out after 30 seconds
```

**Solutions:**

1. **Increase timeout:**
   ```bash
   # For large PRs with many comments
   coderabbit-fetch <URL> --timeout 120

   # For very large PRs
   coderabbit-fetch <URL> --timeout 300
   ```

2. **Check network connectivity:**
   ```bash
   # Test GitHub connectivity
   ping github.com

   # Test GitHub API
   curl -I https://api.github.com
   ```

3. **Use JSON format for better performance:**
   ```bash
   coderabbit-fetch <URL> --output-format json --timeout 90
   ```

### Issue: "Memory usage too high"

**Symptoms:**
- System becomes slow
- Out of memory errors
- High memory usage in task manager

**Solutions:**

1. **Monitor memory usage:**
   ```bash
   # Enable debug mode to see memory usage
   coderabbit-fetch <URL> --debug --show-stats
   ```

2. **Use streaming approach:**
   ```bash
   # Output to file instead of memory
   coderabbit-fetch <URL> --output-file results.json --output-format json
   ```

3. **Process smaller batches:**
   ```bash
   # For very large PRs, consider breaking into smaller requests
   # This may require custom scripting
   ```

### Issue: "Processing very slow"

**Symptoms:**
- Takes longer than 5 minutes for normal PR
- No progress for extended periods

**Solutions:**

1. **Enable debug mode:**
   ```bash
   coderabbit-fetch <URL> --debug --show-stats
   ```

2. **Check PR size:**
   ```bash
   # Check PR metadata
   gh pr view 123 --repo owner/repository --json additions,deletions,changedFiles
   ```

3. **Optimize settings:**
   ```bash
   # Use JSON format (faster)
   coderabbit-fetch <URL> --output-format json

   # Increase timeout but reduce retries
   coderabbit-fetch <URL> --timeout 180 --retry-attempts 2
   ```

## 📄 Output Problems

### Issue: "Empty output" or "No comments found"

**Symptoms:**
```bash
No CodeRabbit comments found in this PR
```

**Solutions:**

1. **Verify CodeRabbit comments exist:**
   ```bash
   # Check PR manually in browser
   # Look for comments from "coderabbitai[bot]"

   # Or use GitHub CLI
   gh pr view 123 --repo owner/repository --comments
   ```

2. **Check resolved marker configuration:**
   ```bash
   # Try with different resolved marker
   coderabbit-fetch <URL> --resolved-marker "✅ RESOLVED"

   # Or disable resolved filtering
   coderabbit-fetch <URL> --resolved-marker ""
   ```

3. **Enable debug mode:**
   ```bash
   coderabbit-fetch <URL> --debug
   ```

### Issue: "Malformed output"

**Symptoms:**
- JSON syntax errors
- Markdown formatting issues
- Truncated output

**Solutions:**

1. **Check output format:**
   ```bash
   # Try different format
   coderabbit-fetch <URL> --output-format plain

   # Save to file to avoid terminal issues
   coderabbit-fetch <URL> --output-file output.json --output-format json
   ```

2. **Check for special characters:**
   ```bash
   # Use debug mode to see processing details
   coderabbit-fetch <URL> --debug --output-file debug_output.json
   ```

3. **Validate output:**
   ```bash
   # For JSON output
   cat output.json | jq .

   # For Markdown output
   pandoc -f markdown -t html output.md > /dev/null
   ```

## 🌐 Network and API Issues

### Issue: "Connection failed"

**Symptoms:**
```bash
❌ Failed to connect to GitHub API
```

**Solutions:**

1. **Check internet connectivity:**
   ```bash
   ping github.com
   curl -I https://api.github.com
   ```

2. **Check proxy settings:**
   ```bash
   # If behind corporate proxy
   export https_proxy=http://proxy.company.com:8080
   export http_proxy=http://proxy.company.com:8080

   # Or configure git proxy
   git config --global http.proxy http://proxy.company.com:8080
   ```

3. **Check firewall settings:**
   - Ensure GitHub.com and api.github.com are accessible
   - Check if HTTPS traffic on port 443 is allowed

### Issue: "SSL certificate errors"

**Symptoms:**
```bash
SSL: CERTIFICATE_VERIFY_FAILED
```

**Solutions:**

1. **Update certificates:**
   ```bash
   # macOS
   brew upgrade ca-certificates

   # Ubuntu/Debian
   sudo apt update && sudo apt upgrade ca-certificates
   ```

2. **Check system time:**
   ```bash
   # Ensure system time is correct
   date

   # Sync time if needed (Linux)
   sudo ntpdate -s time.nist.gov
   ```

3. **Corporate proxy issues:**
   ```bash
   # If behind corporate firewall, may need to configure certificates
   # Contact your IT department for proper certificate setup
   ```

## ⚙️ Configuration Problems

### Issue: "Invalid persona file"

**Symptoms:**
```bash
❌ Persona file not found: /path/to/persona.txt
```

**Solutions:**

1. **Check file path:**
   ```bash
   # Verify file exists
   ls -la /path/to/persona.txt

   # Use absolute path
   coderabbit-fetch <URL> --persona-file /absolute/path/to/persona.txt

   # Or relative path
   coderabbit-fetch <URL> --persona-file ./examples/personas/default_reviewer.txt
   ```

2. **Check file permissions:**
   ```bash
   # Make file readable
   chmod 644 persona.txt

   # Check permissions
   ls -la persona.txt
   ```

3. **Use built-in personas:**
   ```bash
   # Use provided example personas
   coderabbit-fetch <URL> --persona-file examples/personas/default_reviewer.txt
   coderabbit-fetch <URL> --persona-file examples/personas/security_expert.txt
   ```

### Issue: "Invalid output format"

**Symptoms:**
```bash
❌ Invalid output format: xml
```

**Solutions:**

1. **Use supported formats:**
   ```bash
   # Supported formats
   coderabbit-fetch <URL> --output-format markdown
   coderabbit-fetch <URL> --output-format json
   coderabbit-fetch <URL> --output-format plain
   ```

2. **Check typos:**
   ```bash
   # Common typos
   --output-format json    # ✅ Correct
   --output-format JSON    # ❌ Wrong (case sensitive)
   --output-format md      # ❌ Wrong (use "markdown")
   ```

## 🖥️ Platform-Specific Issues

### macOS Issues

**Issue: "Permission denied" on macOS**

**Solutions:**
```bash
# Give terminal full disk access in System Preferences > Security & Privacy
# Or install via Homebrew
brew install coderabbit-comment-fetcher
```

**Issue: "xcrun: error" when installing**

**Solutions:**
```bash
# Install Xcode command line tools
xcode-select --install
```

### Windows Issues

**Issue: "GitHub CLI not found" on Windows**

**Solutions:**
```powershell
# Install via Chocolatey
choco install gh

# Or via Scoop
scoop install gh

# Or download from https://cli.github.com/
```

**Issue: "PowerShell execution policy"**

**Solutions:**
```powershell
# Set execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux Issues

**Issue: "Permission denied" on Linux**

**Solutions:**
```bash
# Install in user space
pip install --user coderabbit-comment-fetcher

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install coderabbit-comment-fetcher
```

**Issue: "GitHub CLI installation issues"**

**Solutions:**
```bash
# Ubuntu/Debian - official repository
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# CentOS/RHEL/Fedora
sudo dnf install gh
```

## 🔍 Advanced Debugging

### Enable Comprehensive Logging

```bash
# Create debug session
export CODERABBIT_DEBUG=1
export CODERABBIT_LOG_LEVEL=DEBUG

coderabbit-fetch <URL> --debug --show-stats --output-file debug_output.json 2>&1 | tee debug.log
```

### Collect System Information

```bash
# System information script
cat << 'EOF' > collect_debug_info.sh
#!/bin/bash
echo "=== CodeRabbit Comment Fetcher Debug Information ==="
echo "Date: $(date)"
echo "OS: $(uname -a)"
echo "Python: $(python --version 2>&1)"
echo "pip: $(pip --version 2>&1)"
echo "GitHub CLI: $(gh --version 2>&1)"
echo "Environment:"
env | grep -E "(PATH|PYTHON|PIP|GH)" | sort
echo ""
echo "=== Package Information ==="
pip show coderabbit-comment-fetcher 2>&1 || echo "Package not installed"
echo ""
echo "=== Test Import ==="
python -c "import coderabbit_fetcher; print(f'Version: {coderabbit_fetcher.__version__}')" 2>&1
echo ""
echo "=== GitHub Auth Status ==="
gh auth status 2>&1
EOF

chmod +x collect_debug_info.sh
./collect_debug_info.sh > debug_info.txt
```

### Test with Minimal Example

```bash
# Create minimal test
cat << 'EOF' > minimal_test.py
#!/usr/bin/env python3
from coderabbit_fetcher import CodeRabbitOrchestrator, ExecutionConfig

config = ExecutionConfig(
    pr_url="https://github.com/microsoft/vscode/pull/12345",  # Use known public PR
    output_format="json",
    timeout=60,
    debug=True
)

try:
    orchestrator = CodeRabbitOrchestrator(config)
    results = orchestrator.execute()
    print(f"Success: {results['success']}")
    if not results['success']:
        print(f"Error: {results['error']}")
except Exception as e:
    print(f"Exception: {e}")
    import traceback
    traceback.print_exc()
EOF

python minimal_test.py
```

### Performance Profiling

```bash
# Install profiling tools
pip install memory-profiler psutil

# Profile memory usage
mprof run python -c "
from coderabbit_fetcher import CodeRabbitOrchestrator, ExecutionConfig
config = ExecutionConfig(pr_url='<URL>', output_format='json')
orchestrator = CodeRabbitOrchestrator(config)
results = orchestrator.execute()
"

# Generate memory profile plot
mprof plot
```

## 🆘 Getting Help

### Before Reporting Issues

1. **Run system check:**
   ```bash
   python scripts/test_uvx_installation.py > system_check.txt
   ```

2. **Collect debug information:**
   ```bash
   ./collect_debug_info.sh > debug_info.txt
   ```

3. **Try minimal reproduction:**
   ```bash
   python minimal_test.py > minimal_test.log 2>&1
   ```

### Where to Get Help

1. **GitHub Issues:** [Report bugs and feature requests](https://github.com/yohi/coderabbit-comment-fetcher/issues)
2. **GitHub Discussions:** [Community support and questions](https://github.com/yohi/coderabbit-comment-fetcher/discussions)
3. **Documentation:** [Full documentation](https://github.com/yohi/coderabbit-comment-fetcher#readme)

### When Reporting Issues

Include the following information:

```
**Environment:**
- OS: [e.g., macOS 14.0, Ubuntu 22.04, Windows 11]
- Python version: [e.g., 3.13.1]
- Package version: [e.g., 1.0.0]
- Installation method: [e.g., uvx, pip]

**Command:**
```bash
coderabbit-fetch <command> --debug
```

**Expected behavior:**
[What you expected to happen]

**Actual behavior:**
[What actually happened]

**Error output:**
```
[Full error output with --debug flag]
```

**System check:**
[Output from system_check.txt]
```

This troubleshooting guide should help you resolve most common issues. If you're still experiencing problems, don't hesitate to reach out for help!
