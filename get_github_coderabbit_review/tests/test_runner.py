"""Test runner for CodeRabbit Comment Fetcher tests."""

import unittest
import sys
import os
import time
import argparse
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CodeRabbitTestRunner:
    """Custom test runner for CodeRabbit Comment Fetcher."""
    
    def __init__(self, verbosity: int = 2):
        """Initialize test runner.
        
        Args:
            verbosity: Test output verbosity level
        """
        self.verbosity = verbosity
        self.results = {}
    
    def discover_tests(self, test_type: str = "all") -> unittest.TestSuite:
        """Discover tests based on type.
        
        Args:
            test_type: Type of tests to discover ('unit', 'integration', 'performance', 'all')
            
        Returns:
            Test suite containing discovered tests
        """
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        if test_type in ("unit", "all"):
            # Discover unit tests
            unit_tests = loader.discover(
                start_dir="tests/unit",
                pattern="test_*.py",
                top_level_dir="tests"
            )
            suite.addTest(unit_tests)
        
        if test_type in ("integration", "all"):
            # Discover integration tests
            integration_tests = loader.discover(
                start_dir="tests/integration",
                pattern="test_*.py",
                top_level_dir="tests"
            )
            suite.addTest(integration_tests)
        
        if test_type in ("performance", "all"):
            # Discover performance tests
            performance_tests = loader.discover(
                start_dir="tests/performance",
                pattern="test_*.py",
                top_level_dir="tests"
            )
            suite.addTest(performance_tests)
        
        return suite
    
    def run_tests(self, test_type: str = "all", pattern: Optional[str] = None) -> Dict[str, Any]:
        """Run tests and return results.
        
        Args:
            test_type: Type of tests to run
            pattern: Optional pattern to filter tests
            
        Returns:
            Dictionary containing test results and metrics
        """
        print(f"🧪 Running {test_type} tests for CodeRabbit Comment Fetcher")
        print("=" * 60)
        
        suite = self.discover_tests(test_type)
        
        if pattern:
            # Filter tests by pattern
            filtered_suite = unittest.TestSuite()
            for test_group in suite:
                for test_case in test_group:
                    if pattern.lower() in str(test_case).lower():
                        filtered_suite.addTest(test_case)
            suite = filtered_suite
        
        # Run tests with custom result collector
        runner = unittest.TextTestRunner(
            verbosity=self.verbosity,
            stream=sys.stdout,
            resultclass=DetailedTestResult
        )
        
        start_time = time.time()
        result = runner.run(suite)
        end_time = time.time()
        
        # Collect results
        test_results = {
            "total_tests": result.testsRun,
            "successes": result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
            "failures": len(result.failures),
            "errors": len(result.errors),
            "skipped": len(result.skipped),
            "execution_time": end_time - start_time,
            "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / max(result.testsRun, 1) * 100,
            "failure_details": result.failures,
            "error_details": result.errors,
            "skipped_details": result.skipped
        }
        
        self.results[test_type] = test_results
        
        # Print summary
        self.print_summary(test_results, test_type)
        
        return test_results
    
    def print_summary(self, results: Dict[str, Any], test_type: str):
        """Print test results summary.
        
        Args:
            results: Test results dictionary
            test_type: Type of tests that were run
        """
        print("\n" + "=" * 60)
        print(f"📊 {test_type.upper()} TEST SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests:    {results['total_tests']}")
        print(f"✅ Passed:      {results['successes']}")
        print(f"❌ Failed:      {results['failures']}")
        print(f"💥 Errors:      {results['errors']}")
        print(f"⏭️  Skipped:     {results['skipped']}")
        print(f"⏱️  Time:        {results['execution_time']:.2f}s")
        print(f"📈 Success Rate: {results['success_rate']:.1f}%")
        
        if results['failures'] > 0:
            print(f"\n❌ FAILURES ({results['failures']}):")
            for i, (test, traceback) in enumerate(results['failure_details'], 1):
                print(f"  {i}. {test}")
                if self.verbosity >= 2:
                    print(f"     {traceback.split('AssertionError:')[-1].strip()}")
        
        if results['errors'] > 0:
            print(f"\n💥 ERRORS ({results['errors']}):")
            for i, (test, traceback) in enumerate(results['error_details'], 1):
                print(f"  {i}. {test}")
                if self.verbosity >= 2:
                    error_line = traceback.split('\n')[-2] if '\n' in traceback else traceback
                    print(f"     {error_line.strip()}")
        
        if results['skipped'] > 0:
            print(f"\n⏭️  SKIPPED ({results['skipped']}):")
            for i, (test, reason) in enumerate(results['skipped_details'], 1):
                print(f"  {i}. {test}")
                if reason and self.verbosity >= 2:
                    print(f"     Reason: {reason}")
    
    def run_coverage_analysis(self) -> Optional[Dict[str, Any]]:
        """Run coverage analysis if coverage.py is available.
        
        Returns:
            Coverage results dictionary or None if coverage not available
        """
        try:
            import coverage
        except ImportError:
            print("⚠️  Coverage analysis not available (install coverage.py)")
            return None
        
        print("\n📊 Running coverage analysis...")
        
        # Start coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Run all tests
        self.run_tests("all")
        
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        # Generate coverage report
        print("\n📋 Coverage Report:")
        cov.report(show_missing=True)
        
        # Get coverage data
        coverage_data = {}
        for filename in cov.get_data().measured_files():
            if 'coderabbit_fetcher' in filename:
                analysis = cov.analysis(filename)
                coverage_data[filename] = {
                    "statements": len(analysis[1]),
                    "missing": len(analysis[3]),
                    "coverage": (len(analysis[1]) - len(analysis[3])) / len(analysis[1]) * 100
                }
        
        return coverage_data
    
    def generate_test_report(self, output_file: str = "test_report.html"):
        """Generate HTML test report.
        
        Args:
            output_file: Output file path for the report
        """
        html_content = self._generate_html_report()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 Test report generated: {output_file}")
    
    def _generate_html_report(self) -> str:
        """Generate HTML report content.
        
        Returns:
            HTML report as string
        """
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>CodeRabbit Comment Fetcher - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .summary { margin: 20px 0; }
        .metric { display: inline-block; margin: 10px; padding: 10px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; }
        .failure { background: #f8d7da; color: #721c24; }
        .warning { background: #fff3cd; color: #856404; }
        .details { margin: 20px 0; }
        .test-case { margin: 10px 0; padding: 10px; border-left: 3px solid #ccc; }
        .passed { border-color: #28a745; }
        .failed { border-color: #dc3545; }
        .skipped { border-color: #ffc107; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 CodeRabbit Comment Fetcher - Test Report</h1>
        <p>Generated on: {timestamp}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Test Summary</h2>
        {summary_metrics}
    </div>
    
    <div class="details">
        <h2>📋 Test Details</h2>
        {test_details}
    </div>
</body>
</html>
        """
        
        # Generate content
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        summary_metrics = self._generate_summary_metrics()
        test_details = self._generate_test_details()
        
        return html.format(
            timestamp=timestamp,
            summary_metrics=summary_metrics,
            test_details=test_details
        )
    
    def _generate_summary_metrics(self) -> str:
        """Generate summary metrics HTML."""
        metrics_html = ""
        for test_type, results in self.results.items():
            metrics_html += f"""
            <div class="metric {'success' if results['failures'] == 0 and results['errors'] == 0 else 'failure'}">
                <h3>{test_type.upper()} Tests</h3>
                <p>Passed: {results['successes']}/{results['total_tests']}</p>
                <p>Success Rate: {results['success_rate']:.1f}%</p>
                <p>Time: {results['execution_time']:.2f}s</p>
            </div>
            """
        return metrics_html
    
    def _generate_test_details(self) -> str:
        """Generate test details HTML."""
        details_html = ""
        for test_type, results in self.results.items():
            details_html += f"<h3>{test_type.upper()} Test Details</h3>"
            
            # Add failure details
            if results['failure_details']:
                details_html += "<h4>❌ Failures</h4>"
                for test, traceback in results['failure_details']:
                    details_html += f'<div class="test-case failed"><strong>{test}</strong><br>{traceback}</div>'
            
            # Add error details
            if results['error_details']:
                details_html += "<h4>💥 Errors</h4>"
                for test, traceback in results['error_details']:
                    details_html += f'<div class="test-case failed"><strong>{test}</strong><br>{traceback}</div>'
        
        return details_html


class DetailedTestResult(unittest.TextTestResult):
    """Custom test result class with detailed reporting."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_start_time = None
    
    def startTest(self, test):
        super().startTest(test)
        self.test_start_time = time.time()
    
    def stopTest(self, test):
        super().stopTest(test)
        if self.test_start_time:
            execution_time = time.time() - self.test_start_time
            if execution_time > 1.0:  # Log slow tests
                print(f"  ⏱️  Slow test: {test} ({execution_time:.2f}s)")


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Run CodeRabbit Comment Fetcher tests")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "performance", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--pattern",
        help="Pattern to filter tests"
    )
    parser.add_argument(
        "--verbosity", "-v",
        type=int,
        choices=[0, 1, 2],
        default=2,
        help="Test output verbosity"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run coverage analysis"
    )
    parser.add_argument(
        "--report",
        help="Generate HTML report to specified file"
    )
    
    args = parser.parse_args()
    
    # Create and run tests
    runner = CodeRabbitTestRunner(verbosity=args.verbosity)
    
    if args.coverage:
        runner.run_coverage_analysis()
    else:
        runner.run_tests(args.type, args.pattern)
    
    # Generate report if requested
    if args.report:
        runner.generate_test_report(args.report)
    
    # Exit with appropriate code
    if runner.results:
        total_failures = sum(r.get('failures', 0) + r.get('errors', 0) for r in runner.results.values())
        sys.exit(0 if total_failures == 0 else 1)


if __name__ == "__main__":
    main()
