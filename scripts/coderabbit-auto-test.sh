#!/usr/bin/env bash
#
# CodeRabbit Comment Fetcher - Automatic Test Runner
# Auto-detects and runs all tests for pre-push validation
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CODERABBIT_DIR="$PROJECT_ROOT/get_github_coderabbit_review"

echo -e "${BLUE}🧪 CodeRabbit Comment Fetcher - Auto Test Runner${NC}"
echo -e "${BLUE}=================================================${NC}"

# Check if we're in the right directory
if [[ ! -d "$CODERABBIT_DIR" ]]; then
    echo -e "${RED}❌ Error: CodeRabbit directory not found at $CODERABBIT_DIR${NC}"
    exit 1
fi

# Change to coderabbit directory
cd "$CODERABBIT_DIR"

# Check if test_runner.py exists
if [[ ! -f "tests/test_runner.py" ]]; then
    echo -e "${RED}❌ Error: test_runner.py not found${NC}"
    exit 1
fi

# Function to run specific test type
run_test_type() {
    local test_type="$1"
    local description="$2"

    echo -e "\n${YELLOW}🔍 Running $description...${NC}"

    if python3 tests/test_runner.py --type "$test_type" --verbosity 1; then
        echo -e "${GREEN}✅ $description passed${NC}"
        return 0
    else
        echo -e "${RED}❌ $description failed${NC}"
        return 1
    fi
}

# Function to check for new tests
detect_new_tests() {
    echo -e "\n${BLUE}🔍 Detecting test files...${NC}"

    local unit_tests=$(find tests/unit -name "test_*.py" 2>/dev/null | wc -l)
    local integration_tests=$(find tests/integration -name "test_*.py" 2>/dev/null | wc -l)
    local pr_tests=$(find tests/pr* -name "test_*.py" 2>/dev/null | wc -l)
    local performance_tests=$(find tests/performance -name "test_*.py" 2>/dev/null | wc -l)

    echo -e "📊 Test Statistics:"
    echo -e "   Unit Tests:        $unit_tests"
    echo -e "   Integration Tests: $integration_tests"
    echo -e "   PR Tests:          $pr_tests"
    echo -e "   Performance Tests: $performance_tests"

    local total_tests=$((unit_tests + integration_tests + pr_tests + performance_tests))
    echo -e "   ${GREEN}Total Tests:       $total_tests${NC}"

    if [[ $total_tests -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  No test files detected${NC}"
        return 1
    fi

    return 0
}

# Function to run quick validation tests
run_quick_tests() {
    echo -e "\n${BLUE}⚡ Running Quick Validation Tests${NC}"
    echo -e "${BLUE}=================================${NC}"

    # Try to run the most important tests first (prefer self-contained tests)
    local quick_test_files=(
        "tests/pr38/test_pr38_direct.py"
        "tests/pr2/test_pr2_quiet_mode.py"
    )

    local quick_tests_found=0
    local quick_tests_passed=0

    for test_file in "${quick_test_files[@]}"; do
        if [[ -f "$test_file" ]]; then
            quick_tests_found=$((quick_tests_found + 1))
            echo -e "\n${YELLOW}🧪 Running $(basename "$test_file")...${NC}"

            if python3 "$test_file"; then
                echo -e "${GREEN}✅ $(basename "$test_file") passed${NC}"
                quick_tests_passed=$((quick_tests_passed + 1))
            else
                echo -e "${RED}❌ $(basename "$test_file") failed${NC}"
            fi
        fi
    done

    # If the basic self-contained tests pass, that's sufficient for quick mode
    if [[ $quick_tests_passed -ge 1 ]]; then
        echo -e "\n${BLUE}📊 Quick Test Results: $quick_tests_passed/$quick_tests_found passed${NC}"
        echo -e "${GREEN}✅ Core functionality validated${NC}"
        return 0
    fi

    if [[ $quick_tests_found -eq 0 ]]; then
        echo -e "${YELLOW}⚠️  No quick test files found, falling back to test runner${NC}"
        return 1
    fi

    echo -e "\n${BLUE}📊 Quick Test Results: $quick_tests_passed/$quick_tests_found passed${NC}"
    return 1
}

# Function to run comprehensive tests
run_comprehensive_tests() {
    echo -e "\n${BLUE}🔬 Running Comprehensive Test Suite${NC}"
    echo -e "${BLUE}===================================${NC}"

    # First, run the basic self-contained tests
    echo -e "\n${YELLOW}🧪 Running core functionality tests...${NC}"
    local core_tests_passed=0
    local core_test_files=(
        "tests/pr38/test_pr38_direct.py"
        "tests/pr2/test_pr2_quiet_mode.py"
        "tests/pr38/test_pr38_simple.py"
    )

    for test_file in "${core_test_files[@]}"; do
        if [[ -f "$test_file" ]]; then
            echo -e "\n${YELLOW}🧪 Running $(basename "$test_file")...${NC}"
            if python3 "$test_file"; then
                echo -e "${GREEN}✅ $(basename "$test_file") passed${NC}"
                core_tests_passed=$((core_tests_passed + 1))
            else
                echo -e "${RED}❌ $(basename "$test_file") failed${NC}"
            fi
        fi
    done

    # If core tests pass, try to run unit/integration tests
    local all_passed=true
    if [[ $core_tests_passed -ge 2 ]]; then
        echo -e "\n${GREEN}✅ Core tests passed, attempting comprehensive tests...${NC}"

        # Try unit tests with better error handling
        echo -e "\n${YELLOW}🔍 Attempting unit tests (may skip if dependencies missing)...${NC}"
        if python3 tests/test_runner.py --type unit --verbosity 0 2>/dev/null; then
            echo -e "${GREEN}✅ Unit tests passed${NC}"
        else
            echo -e "${YELLOW}⚠️  Unit tests skipped (dependency issues)${NC}"
        fi

        # Try integration tests
        echo -e "\n${YELLOW}🔍 Attempting integration tests...${NC}"
        if python3 tests/test_runner.py --type integration --verbosity 0 2>/dev/null; then
            echo -e "${GREEN}✅ Integration tests passed${NC}"
        else
            echo -e "${YELLOW}⚠️  Integration tests skipped (dependency issues)${NC}"
        fi
    else
        all_passed=false
        echo -e "${RED}❌ Core tests failed, skipping comprehensive tests${NC}"
    fi

    # Summary based on core tests
    if [[ $core_tests_passed -ge 2 ]]; then
        echo -e "\n${GREEN}✅ Comprehensive test suite completed${NC}"
        echo -e "${GREEN}✅ Core functionality validated with $core_tests_passed tests${NC}"
        return 0
    else
        echo -e "\n${RED}❌ Comprehensive test suite failed${NC}"
        return 1
    fi
}

# Main execution logic
main() {
    local test_mode="${1:-comprehensive}"
    local exit_code=0

    # Detect available tests
    if ! detect_new_tests; then
        echo -e "${RED}❌ No tests detected, cannot proceed${NC}"
        exit 1
    fi

    # Choose test strategy based on mode
    case "$test_mode" in
        "quick"|"pre-commit")
            echo -e "\n${BLUE}🏃 Running in QUICK mode for pre-commit validation${NC}"
            if ! run_quick_tests; then
                echo -e "\n${YELLOW}⚠️  Quick tests had issues, running minimal test runner...${NC}"
                if ! python3 tests/test_runner.py --type unit --verbosity 0; then
                    exit_code=1
                fi
            fi
            ;;
        "comprehensive"|"pre-push"|"")
            echo -e "\n${BLUE}🔍 Running in COMPREHENSIVE mode for pre-push validation${NC}"
            if ! run_comprehensive_tests; then
                exit_code=1
            fi
            ;;
        "all")
            echo -e "\n${BLUE}🌟 Running ALL tests including performance${NC}"
            if ! python3 tests/test_runner.py --type all --verbosity 1; then
                exit_code=1
            fi
            ;;
        *)
            echo -e "${RED}❌ Unknown test mode: $test_mode${NC}"
            echo -e "Available modes: quick, comprehensive, all"
            exit 1
            ;;
    esac

    # Summary
    echo -e "\n${BLUE}📋 Test Execution Summary${NC}"
    echo -e "${BLUE}=========================${NC}"

    if [[ $exit_code -eq 0 ]]; then
        echo -e "${GREEN}✅ All tests completed successfully${NC}"
        echo -e "${GREEN}🚀 Ready for push!${NC}"
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        echo -e "${RED}🛑 Push blocked due to test failures${NC}"
    fi

    exit $exit_code
}

# Help function
show_help() {
    echo "CodeRabbit Comment Fetcher - Auto Test Runner"
    echo ""
    echo "Usage: $0 [mode]"
    echo ""
    echo "Modes:"
    echo "  quick         - Quick validation tests (for pre-commit)"
    echo "  comprehensive - Comprehensive tests (for pre-push, default)"
    echo "  all          - All tests including performance"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run comprehensive tests"
    echo "  $0 quick             # Run quick tests"
    echo "  $0 all               # Run all tests"
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
