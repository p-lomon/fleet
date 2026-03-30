import pytest
from datetime import datetime
from queue_core.job import Job, JobStatus


class TestJobStatus:
    def test_job_status_values(self):
        """Test that JobStatus enum has correct values"""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"


class TestJob:
    def test_job_creation_with_defaults(self):
        """Test job creation with default values"""
        job = Job()
        assert job.id is not None
        assert job.template_name == ""
        assert job.payload == {}
        assert job.status == JobStatus.PENDING
        assert job.created_at is not None
        assert job.started_at is None
        assert job.completed_at is None
        assert job.error is None
        assert job.result is None

    def test_job_creation_with_values(self):
        """Test job creation with custom values"""
        job = Job(
            template_name="test_template",
            payload={"key": "value"},
            status=JobStatus.PROCESSING,
        )
        assert job.template_name == "test_template"
        assert job.payload == {"key": "value"}
        assert job.status == JobStatus.PROCESSING

    def test_job_to_dict(self):
        """Test job serialization to dictionary"""
        job = Job(
            id="test-id",
            template_name="test_template",
            payload={"key": "value"},
            status=JobStatus.COMPLETED,
        )
        data = job.to_dict()
        assert data["id"] == "test-id"
        assert data["template_name"] == "test_template"
        assert data["payload"] == {"key": "value"}
        assert data["status"] == "completed"
        assert data["error"] is None
        assert data["result"] is None

    def test_job_from_dict(self):
        """Test job deserialization from dictionary"""
        data = {
            "id": "test-id",
            "template_name": "test_template",
            "payload": {"key": "value"},
            "status": "completed",
            "created_at": "2026-03-30T10:00:00",
            "started_at": "2026-03-30T10:01:00",
            "completed_at": "2026-03-30T10:02:00",
            "error": None,
            "result": {"output": "success"},
        }
        job = Job.from_dict(data)
        assert job.id == "test-id"
        assert job.template_name == "test_template"
        assert job.payload == {"key": "value"}
        assert job.status == JobStatus.COMPLETED
        assert job.result == {"output": "success"}

    def test_job_from_dict_with_nulls(self):
        """Test job deserialization with null optional fields"""
        data = {
            "id": "test-id",
            "template_name": "test_template",
            "payload": {},
            "status": "pending",
            "created_at": "2026-03-30T10:00:00",
            "started_at": None,
            "completed_at": None,
            "error": None,
            "result": None,
        }
        job = Job.from_dict(data)
        assert job.started_at is None
        assert job.completed_at is None
        assert job.error is None

    def test_job_roundtrip(self):
        """Test job serializes and deserializes correctly"""
        original = Job(
            id="test-id",
            template_name="test_template",
            payload={"key": "value"},
            status=JobStatus.FAILED,
            error="Something went wrong",
            result=None,
        )
        data = original.to_dict()
        restored = Job.from_dict(data)
        assert restored.id == original.id
        assert restored.template_name == original.template_name
        assert restored.payload == original.payload
        assert restored.status == original.status
        assert restored.error == original.error
