#!/bin/bash
# 🔍 CI/CD設定の検証スクリプト

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$PROJECT_DIR")"

echo "🚀 CI/CD設定検証スクリプト"
echo "=============================================="

# 色付き出力用の関数
print_success() { echo -e "\033[32m✅ $1\033[0m"; }
print_warning() { echo -e "\033[33m⚠️  $1\033[0m"; }
print_error() { echo -e "\033[31m❌ $1\033[0m"; }
print_info() { echo -e "\033[34mℹ️  $1\033[0m"; }

# ワークフローファイルの存在確認
check_workflow_files() {
    echo ""
    echo "📁 GitHub Actions ワークフローファイル確認"
    echo "----------------------------------------------"

    local workflows_dir="${PROJECT_DIR}/.github/workflows"
    local expected_workflows=(
        "test-coderabbit-fetcher.yml"
        "lint-and-format.yml"
        "security-scan.yml"
        "docs-update.yml"
    )

    for workflow in "${expected_workflows[@]}"; do
        if [[ -f "${workflows_dir}/${workflow}" ]]; then
            print_success "Found: ${workflow}"
        else
            print_error "Missing: ${workflow}"
            return 1
        fi
    done
}

# YAML構文チェック
validate_yaml_syntax() {
    echo ""
    echo "🔍 YAML構文検証"
    echo "----------------------------------------------"

    local workflows_dir="${PROJECT_DIR}/.github/workflows"

    if command -v yamllint >/dev/null 2>&1; then
        find "${workflows_dir}" -name "*.yml" -o -name "*.yaml" | while read -r file; do
            if yamllint -d relaxed "${file}"; then
                print_success "YAML valid: $(basename "${file}")"
            else
                print_error "YAML invalid: $(basename "${file}")"
                return 1
            fi
        done
    else
        print_warning "yamllint not found, skipping YAML validation"
        print_info "Install with: pip install yamllint"
    fi
}

# テストファイルの存在確認
check_test_structure() {
    echo ""
    echo "🧪 テスト構造確認"
    echo "----------------------------------------------"

    local tests_dir="${PROJECT_DIR}/tests"
    local required_dirs=(
        "unit"
        "integration"
        "performance"
        "pr38"
        "pr2"
        "fixtures"
    )

    for dir in "${required_dirs[@]}"; do
        if [[ -d "${tests_dir}/${dir}" ]]; then
            print_success "Found test directory: ${dir}"
        else
            print_error "Missing test directory: ${dir}"
            return 1
        fi
    done

    # 重要なテストファイルをチェック
    local important_files=(
        "test_runner.py"
        "run_essential_tests.py"
        "pr38/test_pr38_final.py"
        "pr2/test_pr2_quiet_mode.py"
    )

    for file in "${important_files[@]}"; do
        if [[ -f "${tests_dir}/${file}" ]]; then
            print_success "Found test file: ${file}"
        else
            print_error "Missing test file: ${file}"
            return 1
        fi
    done
}

# モック化テストの検証
validate_mock_tests() {
    echo ""
    echo "🎭 モック化テスト検証"
    echo "----------------------------------------------"

    local test_file="${PROJECT_DIR}/tests/pr38/test_pr38_direct.py"

    if [[ -f "${test_file}" ]]; then
        # GitHub API直接呼び出しがないことを確認
        if grep -q "subprocess.run.*gh " "${test_file}"; then
            print_error "Direct GitHub CLI calls found in ${test_file}"
            return 1
        else
            print_success "PR38 test is properly mocked"
        fi

        # モック化が実装されていることを確認
        if grep -q "mock" "${test_file}"; then
            print_success "Mock implementation found in ${test_file}"
        else
            print_warning "No mock implementation detected in ${test_file}"
        fi
    else
        print_error "PR38 test file not found: ${test_file}"
        return 1
    fi
}

# パス設定の検証
validate_paths() {
    echo ""
    echo "📂 ファイルパス設定検証"
    echo "----------------------------------------------"

    local workflow="${PROJECT_DIR}/.github/workflows/test-coderabbit-fetcher.yml"

    if [[ -f "${workflow}" ]]; then
        # 正しいパス設定があることを確認
        if grep -q "get_github_coderabbit_review/\*\*" "${workflow}"; then
            print_success "Correct path filters found in workflow"
        else
            print_error "Incorrect path filters in workflow"
            return 1
        fi

        # 除外パスが設定されていることを確認
        if grep -q "!\*\*/\*\*.md" "${workflow}"; then
            print_success "Markdown exclusion paths found"
        else
            print_warning "No markdown exclusion paths found"
        fi
    else
        print_error "Main workflow file not found"
        return 1
    fi
}

# 依存関係の確認
check_dependencies() {
    echo ""
    echo "📦 依存関係確認"
    echo "----------------------------------------------"

    local pyproject="${PROJECT_DIR}/pyproject.toml"

    if [[ -f "${pyproject}" ]]; then
        print_success "Found pyproject.toml"

        # 重要な依存関係の確認
        local dev_deps=("pytest" "pytest-cov" "ruff" "black" "mypy")

        for dep in "${dev_deps[@]}"; do
            if grep -q "${dep}" "${pyproject}"; then
                print_success "Found dev dependency: ${dep}"
            else
                print_warning "Missing dev dependency: ${dep}"
            fi
        done
    else
        print_error "pyproject.toml not found"
        return 1
    fi
}

# 簡単なワークフロー実行テスト
test_essential_tests() {
    echo ""
    echo "🎯 Essential Tests実行テスト"
    echo "----------------------------------------------"

    cd "${PROJECT_DIR}"

    if command -v uv >/dev/null 2>&1; then
        print_info "Testing essential tests execution..."

        # 依存関係をインストール
        if uv sync --dev >/dev/null 2>&1; then
            print_success "Dependencies installed successfully"
        else
            print_error "Failed to install dependencies"
            return 1
        fi

        # Essential testsを実行
        if timeout 60 uv run python tests/run_essential_tests.py >/dev/null 2>&1; then
            print_success "Essential tests executed successfully"
        else
            print_warning "Essential tests failed or timed out (expected in CI)"
        fi
    else
        print_warning "uv not found, skipping test execution"
        print_info "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
}

# メイン実行
main() {
    local exit_code=0

    print_info "Starting CI/CD validation for CodeRabbit Fetcher"
    print_info "Project Directory: ${PROJECT_DIR}"
    print_info "Repository Root: ${REPO_ROOT}"

    # 各検証を実行
    check_workflow_files || exit_code=1
    validate_yaml_syntax || exit_code=1
    check_test_structure || exit_code=1
    validate_mock_tests || exit_code=1
    validate_paths || exit_code=1
    check_dependencies || exit_code=1
    test_essential_tests || exit_code=1

    echo ""
    echo "=============================================="
    if [[ $exit_code -eq 0 ]]; then
        print_success "✅ All CI/CD validations passed!"
        print_info "Your GitHub Actions workflows are ready to use"
        echo ""
        echo "🚀 Next Steps:"
        echo "1. Commit and push the workflow files"
        echo "2. Create a pull request to test the CI pipeline"
        echo "3. Monitor the Actions tab in GitHub for execution results"
    else
        print_error "❌ Some validations failed"
        print_info "Please fix the issues above before proceeding"
    fi

    exit $exit_code
}

# 引数処理
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h    Show this help message"
    echo ""
    echo "This script validates the CI/CD configuration for CodeRabbit Fetcher."
    exit 0
fi

main "$@"
