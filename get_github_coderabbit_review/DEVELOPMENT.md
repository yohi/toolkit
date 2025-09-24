# Development Guide

## Quick Push Commands

### For Development
```bash
# Quick push without pre-commit (fastest)
git push --no-verify

# Or use Makefile
make -f Makefile.push quick-push
```

### For Production
```bash
# Full validation (slower but thorough)
git push

# Safe push with minimal checks
make -f Makefile.push safe-push
```

## Pre-commit Configuration

This project uses a **staged approach** to code quality:

### Current Stage: Minimal Quality Gates
- ✅ Basic formatting (black)
- ✅ Essential file checks
- ✅ Critical-only ruff checks
- ⚠️ Mypy disabled (620 errors to fix)
- ⚠️ Comprehensive tests in CI only

### Quality Improvement Roadmap

1. **Phase 1** (Current): Essential checks only
2. **Phase 2**: Enable mypy for new files
3. **Phase 3**: Full ruff compliance
4. **Phase 4**: 100% test coverage
5. **Phase 5**: Full mypy compliance

## Bypass Options

### Emergency Push
```bash
# Skip all checks (emergency only)
git push --no-verify

# Force push (very dangerous)
make -f Makefile.push force-push
```

### Selective Checks
```bash
# Run only on specific files
pre-commit run --files coderabbit_fetcher/cli/*.py

# Skip specific hooks
SKIP=mypy git push
```

## Troubleshooting

### Common Issues

1. **push rejected by pre-commit**
   - Use `git push --no-verify`
   - Or fix the specific errors

2. **Ruff errors**
   - Most are auto-fixable: `ruff check --fix`
   - Critical errors are configured to be ignored

3. **Mypy errors**
   - Currently disabled in CI
   - Will be addressed in Phase 5

4. **Test failures**
   - Check dependencies: `pip install -e ".[dev]"`
   - Run specific test: `python -m pytest tests/pr38/`

### Development Workflow

```bash
# 1. Make changes
git add .
git commit -m "your message"

# 2. Quick development push
git push --no-verify

# 3. Before merge to main
make -f Makefile.push safe-push
```
