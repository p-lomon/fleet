import tempfile
from pathlib import Path

import pytest

from host.submitter import JobSubmitter
from queue_core import Template, TemplateRegistry, PydanticValidator
from pydantic import BaseModel


class ExamplePayload(BaseModel):
    name: str
    value: int


class TestJobSubmitter:
    def test_submit_valid_job(self):
        """Test submitting a valid job with template validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = TemplateRegistry()
            registry.register(Template("test", PydanticValidator(ExamplePayload)))
            submitter = JobSubmitter(tmpdir, registry)

            job = submitter.submit("test", {"name": "test", "value": 42})

            assert job.template_name == "test"
            assert job.payload == {"name": "test", "value": 42}
            assert job.id is not None

    def test_submit_unknown_template(self):
        """Test that submitting with unknown template raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            submitter = JobSubmitter(tmpdir)

            with pytest.raises(ValueError, match="Unknown template: unknown"):
                submitter.submit("unknown", {"data": "test"})

    def test_submit_invalid_payload(self):
        """Test that submitting invalid payload raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = TemplateRegistry()
            registry.register(Template("test", PydanticValidator(ExamplePayload)))
            submitter = JobSubmitter(tmpdir, registry)

            with pytest.raises(ValueError, match="Invalid payload"):
                submitter.submit("test", {"name": "test"})  # missing 'value'

    def test_submit_raw_bypasses_validation(self):
        """Test that submit_raw does not validate against template."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = TemplateRegistry()
            registry.register(Template("test", PydanticValidator(ExamplePayload)))
            submitter = JobSubmitter(tmpdir, registry)

            job = submitter.submit_raw("test", {"invalid": "data"})

            assert job.template_name == "test"
            assert job.payload == {"invalid": "data"}

    def test_get_pending_jobs(self):
        """Test retrieving pending jobs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = TemplateRegistry()
            registry.register(Template("test", PydanticValidator(ExamplePayload)))
            submitter = JobSubmitter(tmpdir, registry)

            submitter.submit("test", {"name": "job1", "value": 1})
            submitter.submit("test", {"name": "job2", "value": 2})

            pending = submitter.get_pending_jobs()

            assert len(pending) == 2
            # Sort by job ID for deterministic ordering
            pending_sorted = sorted(pending, key=lambda j: j.id)
            names = {j.payload["name"] for j in pending_sorted}
            assert names == {"job1", "job2"}

    def test_default_registry(self):
        """Test that JobSubmitter creates default registry if none provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            submitter = JobSubmitter(tmpdir)

            assert submitter.registry is not None
            assert isinstance(submitter.registry, TemplateRegistry)
