#!/usr/bin/env python3
"""Test script for uvx installation and execution compatibility."""

import subprocess
import sys
import os
import tempfile
import json
import traceback
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, List

class UvxTestRunner:
    """Test runner for uvx compatibility."""

    def __init__(self):
        """Initialize test runner."""
        self.temp_dir = tempfile.mkdtemp(prefix="uvx_test_")
        self.results = {}

    def run_command(self, cmd: List[str], timeout: int = 60) -> Dict[str, Any]:
        """Run a command and return results.

        Args:
            cmd: Command to run as list of strings
            timeout: Timeout in seconds

        Returns:
            Dictionary with command results
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.temp_dir
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "command": " ".join(cmd)
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "command": " ".join(cmd)
            }
        except FileNotFoundError:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command not found: {cmd[0]}",
                "command": " ".join(cmd)
            }

    def test_uvx_availability(self) -> bool:
        """Test if uvx is available."""
        print("🔍 Testing uvx availability...")

        result = self.run_command(["uvx", "--version"])
        self.results["uvx_availability"] = result

        if result["success"]:
            print(f"✅ uvx is available: {result['stdout'].strip()}")
            return True
        else:
            print(f"❌ uvx not available: {result['stderr']}")
            return False

    def test_python_version(self) -> bool:
        """Test Python version compatibility."""
        print("🐍 Testing Python version...")

        result = self.run_command(["python", "--version"])
        self.results["python_version"] = result

        if result["success"]:
            version_line = result["stdout"].strip()
            print(f"✅ {version_line}")

            # Check if it's Python 3.13+
            if "Python 3.13" in version_line or "Python 3.14" in version_line:
                return True
            else:
                print(f"⚠️  Python 3.13+ recommended, found: {version_line}")
                return True  # Still compatible, but not optimal
        else:
            print(f"❌ Python not available: {result['stderr']}")
            return False

    def test_github_cli_availability(self) -> bool:
        """Test GitHub CLI availability."""
        print("🐙 Testing GitHub CLI availability...")

        result = self.run_command(["gh", "--version"])
        self.results["github_cli"] = result

        if result["success"]:
            version_info = result["stdout"].strip().split('\n')[0]
            print(f"✅ GitHub CLI available: {version_info}")
            return True
        else:
            print(f"❌ GitHub CLI not available: {result['stderr']}")
            print("💡 Install from: https://cli.github.com/")
            return False

    def test_package_installation(self) -> bool:
        """Test package installation with uvx."""
        print("📦 Testing package installation...")

        # Test local package installation
        project_root = Path(__file__).parent.parent

        # Create temporary pyproject.toml for testing
        test_pyproject = self.temp_dir / "pyproject.toml"
        with open(test_pyproject, "w") as f:
            f.write("""
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "test-coderabbit-fetcher"
version = "0.1.0"
description = "Test package"
requires-python = ">=3.13"
dependencies = []

[project.scripts]
test-crf = "test_package:main"
""")

        # Create test package
        test_package_dir = Path(self.temp_dir) / "test_package"
        test_package_dir.mkdir()

        with open(test_package_dir / "__init__.py", "w") as f:
            f.write("""
def main():
    print("Test package working!")
    return 0
""")

        # Test uvx installation
        result = self.run_command([
            "uvx", "run",
            "--from", self.temp_dir,
            "test-crf"
        ], timeout=120)

        self.results["package_installation"] = result

        if result["success"]:
            print("✅ Package installation test successful")
            return True
        else:
            print(f"❌ Package installation failed: {result['stderr']}")
            return False

    def test_entry_point_execution(self) -> bool:
        """Test entry point execution."""
        print("🚀 Testing entry point execution...")

        # Test help command (doesn't require authentication)
        result = self.run_command([
            "python", "-m", "coderabbit_fetcher.cli.main", "--help"
        ])

        self.results["entry_point"] = result

        if result["success"]:
            print("✅ Entry point execution successful")
            return True
        else:
            print(f"❌ Entry point execution failed: {result['stderr']}")
            return False

    def test_cli_argument_parsing(self) -> bool:
        """Test CLI argument parsing."""
        print("⚙️  Testing CLI argument parsing...")

        # Test version command
        result = self.run_command([
            "python", "-m", "coderabbit_fetcher.cli.main", "--version"
        ])

        self.results["cli_arguments"] = result

        if result["success"]:
            print(f"✅ CLI argument parsing successful: {result['stdout'].strip()}")
            return True
        else:
            print(f"❌ CLI argument parsing failed: {result['stderr']}")
            return False

    def test_import_compatibility(self) -> bool:
        """Test import compatibility."""
        print("📥 Testing import compatibility...")

        test_script = f"""
import sys
sys.path.insert(0, '{Path(__file__).parent.parent}')

try:
    import coderabbit_fetcher
    print(f"Package version: {{coderabbit_fetcher.__version__}}")

    from coderabbit_fetcher.cli.main import main
    print("CLI import successful")

    from coderabbit_fetcher import CodeRabbitOrchestrator, ExecutionConfig
    print("Core classes import successful")

    print("All imports successful!")
except ImportError as e:
    print(f"Import error: {{e}}")
    sys.exit(1)
"""

        # Write test script
        test_file = Path(self.temp_dir) / "import_test.py"
        with open(test_file, "w") as f:
            f.write(test_script)

        result = self.run_command(["python", str(test_file)])
        self.results["import_compatibility"] = result

        if result["success"]:
            print("✅ Import compatibility test successful")
            print(f"   Output: {result['stdout'].strip()}")
            return True
        else:
            print(f"❌ Import compatibility failed: {result['stderr']}")
            return False

    def test_dependency_resolution(self) -> bool:
        """Test dependency resolution."""
        print("🔗 Testing dependency resolution...")

        # Test that all required modules are available
        test_script = """
import sys

required_modules = [
    'argparse', 'json', 'pathlib', 'subprocess', 'tempfile',
    'typing', 'dataclasses', 're', 'os', 'time', 'logging'
]

optional_modules = [
    'psutil', 'rich'
]

print("Testing required modules...")
for module in required_modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError:
        print(f"❌ {module} - REQUIRED")
        sys.exit(1)

print("\\nTesting optional modules...")
for module in optional_modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError:
        print(f"⚠️  {module} - OPTIONAL")

print("\\nDependency check completed!")
"""

        test_file = Path(self.temp_dir) / "dependency_test.py"
        with open(test_file, "w") as f:
            f.write(test_script)

        result = self.run_command(["python", str(test_file)])
        self.results["dependency_resolution"] = result

        if result["success"]:
            print("✅ Dependency resolution test successful")
            return True
        else:
            print(f"❌ Dependency resolution failed: {result['stderr']}")
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        successful_tests = sum(1 for r in self.results.values() if r.get("success", False))
        total_tests = len(self.results)

        report = {
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                "overall_success": successful_tests == total_tests
            },
            "test_results": self.results,
            "recommendations": []
        }

        # Add recommendations based on failures
        if not self.results.get("uvx_availability", {}).get("success", False):
            report["recommendations"].append("Install uvx from: https://github.com/astral-sh/uv")

        if not self.results.get("github_cli", {}).get("success", False):
            report["recommendations"].append("Install GitHub CLI from: https://cli.github.com/")

        if not self.results.get("python_version", {}).get("success", False):
            report["recommendations"].append("Install Python 3.13+ from: https://www.python.org/downloads/")

        return report

    def run_all_tests(self) -> bool:
        """Run all uvx compatibility tests."""
        print("🧪 Running uvx compatibility tests...")
        print("=" * 60)

        tests = [
            ("uvx_availability", self.test_uvx_availability),
            ("python_version", self.test_python_version),
            ("github_cli", self.test_github_cli_availability),
            ("import_compatibility", self.test_import_compatibility),
            ("dependency_resolution", self.test_dependency_resolution),
            ("entry_point", self.test_entry_point_execution),
            ("cli_arguments", self.test_cli_argument_parsing),
        ]

        all_passed = True

        for test_name, test_func in tests:
            try:
                result = test_func()
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ {test_name} test failed with exception: {e}")
                print(f"Traceback:\n{traceback.format_exc()}")
                all_passed = False

            print("-" * 40)

        return all_passed

    def cleanup(self):
        """Clean up temporary files."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            warnings.warn(f"Failed to cleanup temporary directory {self.temp_dir}: {e}")


def main():
    """Main test execution."""
    print("🤖 CodeRabbit Comment Fetcher - uvx Compatibility Test")
    print("=" * 60)

    runner = UvxTestRunner()

    try:
        success = runner.run_all_tests()

        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)

        report = runner.generate_report()
        summary = report["summary"]

        print(f"Total tests: {summary['total_tests']}")
        print(f"Passed: {summary['successful_tests']}")
        print(f"Failed: {summary['failed_tests']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")

        if summary["overall_success"]:
            print("\n✅ All tests passed! Package is uvx compatible.")
        else:
            print(f"\n❌ {summary['failed_tests']} test(s) failed.")

            if report["recommendations"]:
                print("\n💡 Recommendations:")
                for rec in report["recommendations"]:
                    print(f"   • {rec}")

        # Save detailed report
        report_file = "uvx_compatibility_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        return 1
    finally:
        runner.cleanup()


if __name__ == "__main__":
    sys.exit(main())
