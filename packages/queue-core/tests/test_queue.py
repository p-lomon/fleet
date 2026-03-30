import pytest
import tempfile
import shutil
from pathlib import Path
from queue_core.job import Job, JobStatus
from queue_core.queue import FileQueue


@pytest.fixture
def queue_dir():
    """Create a temporary directory for queue tests"""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    shutil.rmtree(tmpdir)


@pytest.fixture
def file_queue(queue_dir):
    """Create a FileQueue instance"""
    return FileQueue(queue_dir)


class TestFileQueueInit:
    def test_creates_queue_directories(self, queue_dir):
        """Test that FileQueue creates required directories"""
        queue = FileQueue(queue_dir)
        assert Path(queue.pending_dir).exists()
        assert Path(queue.processing_dir).exists()
        assert Path(queue.completed_dir).exists()
        assert Path(queue.failed_dir).exists()


class TestFileQueueEnqueue:
    def test_enqueue_adds_job_to_pending(self, file_queue):
        """Test that enqueue adds job to pending directory"""
        job = Job(id="test-job-1", template_name="test", payload={})
        file_queue.enqueue(job)
        
        pending_jobs = list(file_queue.pending_dir.glob("*.json"))
        assert len(pending_jobs) == 1
        assert pending_jobs[0].name == "test-job-1.json"

    def test_enqueue_multiple_jobs(self, file_queue):
        """Test enqueueing multiple jobs"""
        job1 = Job(id="job-1", template_name="test", payload={})
        job2 = Job(id="job-2", template_name="test", payload={})
        job3 = Job(id="job-3", template_name="test", payload={})
        
        file_queue.enqueue(job1)
        file_queue.enqueue(job2)
        file_queue.enqueue(job3)
        
        pending_jobs = list(file_queue.pending_dir.glob("*.json"))
        assert len(pending_jobs) == 3


class TestFileQueueDequeue:
    def test_dequeue_returns_oldest_pending_job(self, file_queue):
        """Test that dequeue returns the oldest pending job"""
        job1 = Job(id="job-1", template_name="test", payload={"order": 1})
        job2 = Job(id="job-2", template_name="test", payload={"order": 2})
        
        file_queue.enqueue(job1)
        file_queue.enqueue(job2)
        
        dequeued = file_queue.dequeue()
        assert dequeued is not None
        assert dequeued.id == "job-1"
        assert dequeued.status == JobStatus.PROCESSING

    def test_dequeue_moves_job_to_processing(self, file_queue):
        """Test that dequeue moves job from pending to processing"""
        job = Job(id="test-job", template_name="test", payload={})
        file_queue.enqueue(job)
        
        file_queue.dequeue()
        
        pending_jobs = list(file_queue.pending_dir.glob("*.json"))
        processing_jobs = list(file_queue.processing_dir.glob("*.json"))
        assert len(pending_jobs) == 0
        assert len(processing_jobs) == 1
        assert processing_jobs[0].name == "test-job.json"

    def test_dequeue_empty_queue(self, file_queue):
        """Test that dequeue returns None when queue is empty"""
        result = file_queue.dequeue()
        assert result is None

    def test_dequeue_updates_job_status(self, file_queue):
        """Test that dequeue updates job status to PROCESSING"""
        job = Job(id="test-job", template_name="test", payload={})
        file_queue.enqueue(job)
        
        dequeued = file_queue.dequeue()
        assert dequeued is not None
        assert dequeued.status == JobStatus.PROCESSING


class TestFileQueueComplete:
    def test_complete_moves_job_to_completed(self, file_queue):
        """Test that complete moves job to completed directory"""
        job = Job(id="test-job", template_name="test", payload={})
        file_queue.enqueue(job)
        job = file_queue.dequeue()
        
        assert job is not None
        file_queue.complete(job)
        
        processing_jobs = list(file_queue.processing_dir.glob("*.json"))
        completed_jobs = list(file_queue.completed_dir.glob("*.json"))
        assert len(processing_jobs) == 0
        assert len(completed_jobs) == 1

    def test_complete_updates_job_status(self, file_queue):
        """Test that complete updates job status to COMPLETED"""
        job = Job(id="test-job", template_name="test", payload={})
        file_queue.enqueue(job)
        job = file_queue.dequeue()
        
        assert job is not None
        file_queue.complete(job)
        
        completed_jobs = list(file_queue.completed_dir.glob("*.json"))
        assert len(completed_jobs) == 1


class TestFileQueueFail:
    def test_fail_moves_job_to_failed(self, file_queue):
        """Test that fail moves job to failed directory"""
        job = Job(id="test-job", template_name="test", payload={})
        file_queue.enqueue(job)
        job = file_queue.dequeue()
        
        assert job is not None
        file_queue.fail(job, "Test error")
        
        processing_jobs = list(file_queue.processing_dir.glob("*.json"))
        failed_jobs = list(file_queue.failed_dir.glob("*.json"))
        assert len(processing_jobs) == 0
        assert len(failed_jobs) == 1

    def test_fail_updates_job_status_and_error(self, file_queue):
        """Test that fail updates job status and error message"""
        job = Job(id="test-job", template_name="test", payload={})
        file_queue.enqueue(job)
        job = file_queue.dequeue()
        
        assert job is not None
        file_queue.fail(job, "Something went wrong")
        
        failed_jobs = list(file_queue.failed_dir.glob("*.json"))
        assert len(failed_jobs) == 1


class TestFileQueueGetPending:
    def test_get_pending_returns_all_pending_jobs(self, file_queue):
        """Test that get_pending returns all pending jobs"""
        job1 = Job(id="job-1", template_name="test", payload={})
        job2 = Job(id="job-2", template_name="test", payload={})
        
        file_queue.enqueue(job1)
        file_queue.enqueue(job2)
        
        pending = file_queue.get_pending()
        assert len(pending) == 2
        assert pending[0].id == "job-1"
        assert pending[1].id == "job-2"

    def test_get_pending_empty_queue(self, file_queue):
        """Test that get_pending returns empty list for empty queue"""
        pending = file_queue.get_pending()
        assert len(pending) == 0

    def test_get_pending_ordered_by_creation_time(self, file_queue):
        """Test that get_pending returns jobs ordered by creation time"""
        job1 = Job(id="job-1", template_name="test", payload={})
        job2 = Job(id="job-2", template_name="test", payload={})
        
        file_queue.enqueue(job1)
        file_queue.enqueue(job2)
        
        pending = file_queue.get_pending()
        assert pending[0].id == "job-1"
        assert pending[1].id == "job-2"
