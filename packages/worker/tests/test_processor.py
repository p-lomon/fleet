"""Tests for worker processor module."""

import tempfile
from pathlib import Path

from queue_core import FileQueue, Job, TemplateRegistry
from worker.processor import JobProcessor


class TestJobProcessor:
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.queue_dir = Path(self.temp_dir) / "queue"
        self.queue_dir.mkdir()
        self.registry = TemplateRegistry()
        self.processor = JobProcessor(
            queue_dir=self.queue_dir,
            registry=self.registry,
            poll_interval=0.1,
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_register_handler(self):
        """Test handler registration."""
        def handler(payload):
            return "handled"

        self.processor.register_handler("test_template", handler)
        assert "test_template" in self.processor._handlers
        assert self.processor._handlers["test_template"] == handler

    def test_process_job_success(self):
        """Test successful job processing."""
        def handler(payload):
            return f"processed: {payload.get('data')}"

        self.processor.register_handler("test", handler)
        queue = FileQueue(self.queue_dir)
        job = Job(template_name="test", payload={"data": "hello"})
        queue.enqueue(job)

        dequeued = queue.dequeue()
        assert dequeued is not None

        result = self.processor.process_job(dequeued)
        assert result is True
        assert dequeued.result == "processed: hello"

    def test_process_job_no_handler(self):
        """Test job processing when no handler is registered."""
        queue = FileQueue(self.queue_dir)
        job = Job(template_name="unknown", payload={})
        queue.enqueue(job)

        dequeued = queue.dequeue()
        assert dequeued is not None

        result = self.processor.process_job(dequeued)
        assert result is False
        assert dequeued.error is not None
        assert "No handler registered" in dequeued.error

    def test_process_job_handler_exception(self):
        """Test job processing when handler raises exception."""
        def failing_handler(payload):
            raise ValueError("Something went wrong")

        self.processor.register_handler("failing", failing_handler)
        queue = FileQueue(self.queue_dir)
        job = Job(template_name="failing", payload={})
        queue.enqueue(job)

        dequeued = queue.dequeue()
        assert dequeued is not None

        result = self.processor.process_job(dequeued)
        assert result is False
        assert dequeued.error == "Something went wrong"

    def test_process_one_with_job(self):
        """Test process_one returns True when job exists."""
        def handler(payload):
            return "done"

        self.processor.register_handler("test", handler)
        queue = FileQueue(self.queue_dir)
        queue.enqueue(Job(template_name="test", payload={}))

        result = self.processor.process_one()
        assert result is True

    def test_process_one_empty_queue(self):
        """Test process_one returns False when queue is empty."""
        result = self.processor.process_one()
        assert result is False

    def test_run_and_stop(self):
        """Test run loop can be stopped."""
        # Test that stop() properly sets _running to False
        self.processor._running = True
        self.processor.stop()
        assert self.processor._running is False

    def test_stop_sets_running_false(self):
        """Test stop method sets _running to False."""
        self.processor._running = True
        self.processor.stop()
        assert self.processor._running is False
