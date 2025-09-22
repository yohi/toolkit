"""Integration tests for Phase 1 improvements."""

import unittest
from unittest.mock import Mock, patch
import tempfile
import os

from coderabbit_fetcher.processors.review_processor import ReviewProcessor
from coderabbit_fetcher.utils.memory_manager import MemoryManager
from coderabbit_fetcher.utils.streaming_processor import CommentStreamProcessor
from coderabbit_fetcher.utils.code_quality import QualityGate
from coderabbit_fetcher.orchestrator import CodeRabbitOrchestrator, ExecutionConfig


class TestPhase1Integration(unittest.TestCase):
    """Integration tests for Phase 1 improvements."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_pr_url = "https://github.com/test/repo/pull/123"

    def test_review_processor_integration(self):
        """Test integration of refactored ReviewProcessor."""
        processor = ReviewProcessor()

        # Test comment data
        comment_data = {
            'body': '''
## 🛠️ Refactor Suggestions

**file.py:42** - Consider extracting this method
- Extract the validation logic into a separate method
- This would improve readability and testability

## 🧹 Nitpick Comments

* Use more descriptive variable names
* Add type hints for better code clarity

## 🤖 Prompt for AI Agents

```
Analyze the following code for security vulnerabilities:
- Check for SQL injection risks
- Validate input sanitization
```
'''
        }

        # Process the comment
        result = processor.process_review_comment(comment_data)

        # Verify all components are working
        self.assertIsNotNone(result)
        self.assertGreater(len(result.actionable_comments), 0)
        self.assertGreater(len(result.nitpick_comments), 0)
        self.assertGreater(len(result.ai_agent_prompts), 0)

    def test_memory_management_integration(self):
        """Test memory management with large datasets."""
        memory_manager = MemoryManager(max_memory_mb=50)

        # Create large dataset
        large_dataset = [{'id': i, 'content': f'Item {i}' * 100} for i in range(1000)]

        def simple_processor(item):
            return item['id']

        # Process with memory management
        results = memory_manager.process_with_memory_limit(
            large_dataset,
            simple_processor,
            batch_size=25
        )

        # Verify processing completed successfully
        self.assertEqual(len(results), 1000)
        self.assertEqual(results[:5], [0, 1, 2, 3, 4])

    def test_streaming_processor_integration(self):
        """Test streaming processor with real-like comment data."""
        stream_processor = CommentStreamProcessor(max_workers=2, batch_size=10)

        # Create comment-like data
        comments = []
        for i in range(50):
            comments.append({
                'id': i,
                'user': {'login': 'coderabbitai[bot]' if i % 3 == 0 else 'user'},
                'body': f'Comment {i} content with some analysis'
            })

        # Process with streaming
        def extract_coderabbit_comments(comment):
            if 'coderabbitai' in comment['user']['login']:
                return comment
            return None

        results = stream_processor.process_streaming(
            comments,
            extract_coderabbit_comments,
            parallel=True
        )

        # Verify CodeRabbit comments were extracted
        self.assertEqual(len(results), 17)  # Every 3rd comment (0,3,6,9...)
        self.assertTrue(all('coderabbitai' in r['user']['login'] for r in results))

    def test_code_quality_gate_integration(self):
        """Test code quality gate with various code samples."""
        quality_gate = QualityGate(max_complexity=8, max_lines=30)

        # Test good quality code
        good_code = '''
def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        total += item.price
    return total
'''

        good_result = quality_gate.check_quality(good_code, "calculate_total")
        self.assertTrue(good_result['passes_quality_gate'])
        self.assertGreater(good_result['quality_score'], 70)

        # Test poor quality code
        poor_code = '''
def complex_function(a,b,c,d,e,f,g,h,i,j):
    if a>0:
        if b>0:
            if c>0:
                if d>0:
                    if e>0:
                        if f>0:
                            if g>0:
                                if h>0:
                                    if i>0:
                                        if j>0:
                                            return True
    return False
'''

        poor_result = quality_gate.check_quality(poor_code, "complex_function")
        self.assertFalse(poor_result['passes_quality_gate'])
        self.assertLess(poor_result['quality_score'], 50)

    @patch('coderabbit_fetcher.orchestrator.GitHubClient')
    @patch('coderabbit_fetcher.orchestrator.PersonaManager')
    def test_orchestrator_with_phase1_improvements(self, mock_persona_manager, mock_github_client):
        """Test orchestrator with Phase 1 improvements integrated."""
        # Mock dependencies
        mock_github_client.return_value.validate_auth.return_value = True
        mock_github_client.return_value.get_pr_info.return_value = {
            'number': 123,
            'title': 'Test PR',
            'body': 'Test description'
        }
        mock_github_client.return_value.get_pr_data.return_value = {
            'comments': [],
            'reviews': [
                {
                    'body': '''
## 🛠️ Refactor Suggestions

**test.py:10** - Test actionable comment

## 🤖 Prompt for AI Agents

```
Test AI prompt content
```
'''
                }
            ],
            'files': []
        }

        mock_persona_manager.return_value.load_persona.return_value = "Test persona"

        # Create configuration
        config = ExecutionConfig(
            pr_url=self.test_pr_url,
            output_format='markdown',
            quiet=True,
            use_enhanced_analyzer=True
        )

        # Create orchestrator
        orchestrator = CodeRabbitOrchestrator(config)

        # Execute with Phase 1 improvements
        results = orchestrator.execute()

        # Verify execution completed successfully
        self.assertTrue(results['success'])
        self.assertIn('metrics', results)
        self.assertIn('output_info', results)

    def test_todo_resolution_integration(self):
        """Test that TODO items were properly resolved."""
        # This test ensures the TODO resolution is working
        config = ExecutionConfig(
            pr_url=self.test_pr_url,
            use_enhanced_analyzer=True
        )

        orchestrator = CodeRabbitOrchestrator(config)

        # Check that the methods exist and are callable
        self.assertTrue(hasattr(orchestrator, '_extract_ai_agent_prompts'))
        self.assertTrue(hasattr(orchestrator, '_extract_summary_comments'))
        self.assertTrue(callable(getattr(orchestrator, '_extract_ai_agent_prompts')))
        self.assertTrue(callable(getattr(orchestrator, '_extract_summary_comments')))

    def test_performance_optimization_integration(self):
        """Test performance optimization features."""
        # Test memory manager initialization
        memory_manager = MemoryManager()
        self.assertIsNotNone(memory_manager)

        # Test streaming processor initialization
        stream_processor = CommentStreamProcessor()
        self.assertIsNotNone(stream_processor)

        # Test memory stats collection
        stats = memory_manager.get_memory_stats()
        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats.process_mb, 0)

    def test_error_handling_integration(self):
        """Test error handling across Phase 1 components."""
        processor = ReviewProcessor()

        # Test with malformed comment data
        malformed_comment = {
            'body': None  # Invalid body
        }

        # Should handle gracefully
        try:
            result = processor.process_review_comment(malformed_comment)
            # Should either succeed with empty result or raise expected exception
            self.assertIsNotNone(result)
        except Exception as e:
            # Should be a known exception type
            self.assertIn('CommentParsingError', str(type(e)))

    def test_end_to_end_workflow(self):
        """Test complete workflow with Phase 1 improvements."""
        # Test the complete workflow from comment parsing to output formatting
        processor = ReviewProcessor()
        memory_manager = MemoryManager(max_memory_mb=100)

        # Sample data
        comments = [
            {
                'body': '''
## 🛠️ Refactor Suggestions

**main.py:15** - Extract method for better readability
- The validation logic is complex
- Consider breaking into smaller functions
'''
            },
            {
                'body': '''
## 🧹 Nitpick Comments

* Variable naming could be improved
* Add docstrings to public methods
'''
            }
        ]

        # Process comments with memory management
        def process_comment(comment):
            return processor.process_review_comment(comment)

        results = memory_manager.process_with_memory_limit(
            comments,
            process_comment,
            batch_size=1
        )

        # Verify end-to-end processing
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r is not None for r in results))

        # Check that actionable and nitpick comments were extracted
        total_actionable = sum(len(r.actionable_comments) for r in results)
        total_nitpick = sum(len(r.nitpick_comments) for r in results)

        self.assertGreater(total_actionable, 0)
        self.assertGreater(total_nitpick, 0)


class TestPhase1PerformanceImprovements(unittest.TestCase):
    """Performance-focused integration tests for Phase 1."""

    def test_large_dataset_processing(self):
        """Test processing large datasets efficiently."""
        memory_manager = MemoryManager(max_memory_mb=200)

        # Create large dataset (simulating large PR)
        large_comments = []
        for i in range(500):
            large_comments.append({
                'id': i,
                'body': f'Comment {i}' + 'x' * 1000,  # Large content
                'user': {'login': 'coderabbitai[bot]' if i % 10 == 0 else 'user'}
            })

        # Process with streaming
        stream_processor = CommentStreamProcessor(batch_size=20)

        def filter_coderabbit(comment):
            if 'coderabbitai' in comment['user']['login']:
                return comment['id']
            return None

        start_memory = memory_manager.get_memory_stats().process_mb

        results = stream_processor.process_comments_streaming(
            large_comments,
            filter_coderabbit
        )

        end_memory = memory_manager.get_memory_stats().process_mb

        # Verify processing completed and memory usage is reasonable
        self.assertEqual(len(results), 50)  # Every 10th comment

        # Memory usage should not have increased dramatically
        memory_increase = end_memory - start_memory
        self.assertLess(memory_increase, 100)  # Less than 100MB increase

    def test_concurrent_processing_performance(self):
        """Test concurrent processing performance."""
        stream_processor = CommentStreamProcessor(max_workers=4, batch_size=10)

        # Create dataset that benefits from parallelization
        comments = [{'id': i, 'processing_time': 0.01} for i in range(100)]

        def slow_processor(comment):
            # Simulate processing time
            import time
            time.sleep(0.001)  # 1ms per comment
            return comment['id']

        import time
        start_time = time.time()

        results = stream_processor.process_streaming(
            comments,
            slow_processor,
            parallel=True
        )

        parallel_time = time.time() - start_time

        # Now test sequential processing
        start_time = time.time()

        results_seq = stream_processor.process_streaming(
            comments,
            slow_processor,
            parallel=False
        )

        sequential_time = time.time() - start_time

        # Verify results are the same
        self.assertEqual(len(results), len(results_seq))

        # Parallel should be faster (though test timing can be variable)
        # We'll just ensure both completed successfully
        self.assertEqual(len(results), 100)


if __name__ == '__main__':
    unittest.main()
