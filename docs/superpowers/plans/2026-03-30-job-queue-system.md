# Job Queue System with Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a job queue system where jobs are submitted to workers using configurable templates, with separate Python environments for host (job submitter) and worker (job processor).

**Architecture:**
- Host environment submits jobs using templates to define job types
- Worker environment polls queue and processes jobs based on template type
- Templates define job payload structure, validation rules, and handler functions
- File-based queue backend for simplicity (can be extended to Redis later)

**Tech Stack:**
- Python 3.11+ with uv for package management
- Pydantic for job validation and templating
- JSON file-based queue with file locking
- Separate uv workspaces for host and worker

---

## File Structure

```
fleet/
├── pyproject.toml              # Root workspace
├── uv.lock
├── packages/
│   ├── queue-core/             # Shared queue infrastructure
│   │   ├── pyproject.toml
│   │   ├── queue_core/
│   │   │   ├── __init__.py
│   │   │   ├── queue.py        # Queue interface
│   │   │   ├── job.py          # Job model
│   │   │   └── template.py     # Template registry
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_queue.py
│   │       └── test_template.py
│   ├── host/                   # Job submission environment
│   │   ├── pyproject.toml
│   │   ├── host/
│   │   │   ├── __init__.py
│   │   │   └── submitter.py    # Job submission API
│   │   └── tests/
│   │       └── test_submitter.py
│   └── worker/                 # Job processing environment
│       ├── pyproject.toml
│       ├── worker/
│       │   ├── __init__.py
│       │   ├── processor.py    # Job processing loop
│       │   └── handlers.py     # Template handlers
│       └── tests/
│           └── test_processor.py
└── examples/
    └── basic_usage.py          # Demo script
```

---

### Task 1: Setup Root Workspace

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`

- [ ] **Step 1: Create root pyproject.toml**

```toml
[project]
name = "fleet"
version = "0.1.0"
description = "Job queue system with templated job types"
requires-python = ">=3.11"
dependencies = []

[tool.uv.workspace]
members = ["packages/queue-core", "packages/host", "packages/worker"]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]
```

- [ ] **Step 2: Create .python-version**

```
3.11
```

- [ ] **Step 3: Initialize uv workspace**

```bash
uv sync
```
Expected: Creates uv.lock and .venv

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml .python-version uv.lock
git commit -m "chore: setup root uv workspace"
```

---

### Task 2: Create Queue Core Package

**Files:**
- Create: `packages/queue-core/pyproject.toml`
- Create: `packages/queue-core/queue_core/__init__.py`
- Create: `packages/queue-core/queue_core/job.py`
- Create: `packages/queue-core/queue_core/queue.py`
- Create: `packages/queue-core/queue_core/template.py`

- [ ] **Step 1: Create queue-core pyproject.toml**

```toml
[project]
name = "queue-core"
version = "0.1.0"
description = "Core queue infrastructure for job processing"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["queue_core"]
```

- [ ] **Step 2: Create __init__.py**

```python
from queue_core.job import Job, JobStatus
from queue_core.queue import FileQueue, Queue
from queue_core.template import Template, TemplateRegistry

__all__ = [
    "Job",
    "JobStatus", 
    "Queue",
    "FileQueue",
    "Template",
    "TemplateRegistry",
]
```

- [ ] **Step 3: Create job.py**

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    template_name: str = ""
    payload: dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "template_name": self.template_name,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "result": self.result,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        return cls(
            id=data["id"],
            template_name=data["template_name"],
            payload=data["payload"],
            status=JobStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            error=data.get("error"),
            result=data.get("result"),
        )
```

- [ ] **Step 4: Create queue.py**

```python
import fcntl
import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from queue_core.job import Job, JobStatus


class Queue(Protocol):
    def enqueue(self, job: Job) -> None: ...
    def dequeue(self) -> Job | None: ...
    def complete(self, job: Job) -> None: ...
    def fail(self, job: Job, error: str) -> None: ...
    def get_pending(self) -> list[Job]: ...


class FileQueue:
    def __init__(self, queue_dir: str | Path):
        self.queue_dir = Path(queue_dir)
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.pending_dir = self.queue_dir / "pending"
        self.processing_dir = self.queue_dir / "processing"
        self.completed_dir = self.queue_dir / "completed"
        self.failed_dir = self.queue_dir / "failed"
        
        for d in [self.pending_dir, self.processing_dir, self.completed_dir, self.failed_dir]:
            d.mkdir(exist_ok=True)

    def _job_path(self, job: Job, subdir: Path) -> Path:
        return subdir / f"{job.id}.json"

    def _write_job(self, job: Job, subdir: Path) -> None:
        path = self._job_path(job, subdir)
        with open(path, "w") as f:
            json.dump(job.to_dict(), f, indent=2)

    def _read_job(self, path: Path) -> Job:
        with open(path) as f:
            return Job.from_dict(json.load(f))

    def enqueue(self, job: Job) -> None:
        self._write_job(job, self.pending_dir)

    def dequeue(self) -> Job | None:
        pending_jobs = sorted(self.pending_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        if not pending_jobs:
            return None
        
        path = pending_jobs[0]
        lock_path = path.with_suffix(".lock")
        
        try:
            with open(lock_path, "w") as lock_file:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                try:
                    if not path.exists():
                        return None
                    job = self._read_job(path)
                    job.status = JobStatus.PROCESSING
                    path.unlink()
                    self._write_job(job, self.processing_dir)
                    return job
                finally:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        except (IOError, OSError):
            return None

    def complete(self, job: Job) -> None:
        job.status = JobStatus.COMPLETED
        src = self._job_path(job, self.processing_dir)
        if src.exists():
            src.unlink()
        self._write_job(job, self.completed_dir)

    def fail(self, job: Job, error: str) -> None:
        job.status = JobStatus.FAILED
        job.error = error
        src = self._job_path(job, self.processing_dir)
        if src.exists():
            src.unlink()
        self._write_job(job, self.failed_dir)

    def get_pending(self) -> list[Job]:
        jobs = []
        for path in sorted(self.pending_dir.glob("*.json"), key=lambda p: p.stat().st_mtime):
            jobs.append(self._read_job(path))
        return jobs
```

- [ ] **Step 5: Create template.py**

```python
from typing import Any, Callable, Protocol
from pydantic import BaseModel, ValidationError


class JobValidator(Protocol):
    def validate(self, payload: dict[str, Any]) -> tuple[bool, str | None]: ...


class TemplateHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> Any: ...


class Template:
    def __init__(
        self,
        name: str,
        validator: JobValidator | None = None,
        handler: TemplateHandler | None = None,
    ):
        self.name = name
        self._validator = validator
        self._handler = handler

    def validate(self, payload: dict[str, Any]) -> tuple[bool, str | None]:
        if self._validator is None:
            return True, None
        return self._validator.validate(payload)

    def handle(self, payload: dict[str, Any]) -> Any:
        if self._handler is None:
            raise ValueError(f"No handler registered for template '{self.name}'")
        return self._handler.handle(payload)


class PydanticValidator:
    def __init__(self, model: type[BaseModel]):
        self.model = model

    def validate(self, payload: dict[str, Any]) -> tuple[bool, str | None]:
        try:
            self.model(**payload)
            return True, None
        except ValidationError as e:
            return False, str(e)


class TemplateRegistry:
    def __init__(self):
        self._templates: dict[str, Template] = {}

    def register(self, template: Template) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> Template | None:
        return self._templates.get(name)

    def list_templates(self) -> list[str]:
        return list(self._templates.keys())
```

- [ ] **Step 6: Commit**

```bash
git add packages/queue-core/
git commit -m "feat: create queue-core package with job, queue, and template"
```

---

### Task 3: Add Queue Core Tests

**Files:**
- Create: `packages/queue-core/tests/__init__.py`
- Create: `packages/queue-core/tests/test_job.py`
- Create: `packages/queue-core/tests/test_queue.py`
- Create: `packages/queue-core/tests/test_template.py`

- [ ] **Step 1: Create __init__.py**

```python
```

- [ ] **Step 2: Create test_job.py**

```python
import pytest
from queue_core.job import Job, JobStatus


def test_job_creation():
    job = Job(template_name="test", payload={"key": "value"})
    assert job.template_name == "test"
    assert job.payload == {"key": "value"}
    assert job.status == JobStatus.PENDING
    assert job.id is not None


def test_job_serialization():
    job = Job(template_name="test", payload={"key": "value"})
    data = job.to_dict()
    
    restored = Job.from_dict(data)
    assert restored.id == job.id
    assert restored.template_name == job.template_name
    assert restored.payload == job.payload
    assert restored.status == job.status
```

- [ ] **Step 3: Create test_queue.py**

```python
import pytest
import tempfile
from pathlib import Path
from queue_core.job import Job, JobStatus
from queue_core.queue import FileQueue


@pytest.fixture
def queue_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def queue(queue_dir):
    return FileQueue(queue_dir)


def test_enqueue_dequeue(queue):
    job = Job(template_name="test", payload={"data": 123})
    queue.enqueue(job)
    
    dequeued = queue.dequeue()
    assert dequeued is not None
    assert dequeued.id == job.id
    assert dequeued.status == JobStatus.PROCESSING


def test_dequeue_empty(queue):
    assert queue.dequeue() is None


def test_complete_job(queue):
    job = Job(template_name="test", payload={})
    queue.enqueue(job)
    dequeued = queue.dequeue()
    
    queue.complete(dequeued)
    
    completed_path = queue.queue_dir / "completed" / f"{job.id}.json"
    assert completed_path.exists()


def test_fail_job(queue):
    job = Job(template_name="test", payload={})
    queue.enqueue(job)
    dequeued = queue.dequeue()
    
    queue.fail(dequeued, "test error")
    
    failed_path = queue.queue_dir / "failed" / f"{job.id}.json"
    assert failed_path.exists()
```

- [ ] **Step 4: Create test_template.py**

```python
import pytest
from pydantic import BaseModel
from queue_core.template import Template, TemplateRegistry, PydanticValidator


class TestPayload(BaseModel):
    name: str
    count: int


class TestHandler:
    def handle(self, payload: dict) -> str:
        return f"Processed {payload['name']} {payload['count']} times"


def test_template_validation():
    validator = PydanticValidator(TestPayload)
    template = Template("test", validator=validator)
    
    valid, error = template.validate({"name": "foo", "count": 5})
    assert valid is True
    assert error is None
    
    valid, error = template.validate({"name": "foo"})
    assert valid is False
    assert error is not None


def test_template_handler():
    handler = TestHandler()
    template = Template("test", handler=handler)
    
    result = template.handle({"name": "bar", "count": 3})
    assert result == "Processed bar 3 times"


def test_registry():
    registry = TemplateRegistry()
    template = Template("my_template")
    
    registry.register(template)
    
    assert registry.get("my_template") == template
    assert "my_template" in registry.list_templates()
```

- [ ] **Step 5: Run tests**

```bash
cd packages/queue-core && uv run pytest tests/ -v
```
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add packages/queue-core/tests/
git commit -m "test: add tests for queue-core package"
```

---

### Task 4: Create Host Package

**Files:**
- Create: `packages/host/pyproject.toml`
- Create: `packages/host/host/__init__.py`
- Create: `packages/host/host/submitter.py`

- [ ] **Step 1: Create host pyproject.toml**

```toml
[project]
name = "host"
version = "0.1.0"
description = "Job submission host environment"
requires-python = ">=3.11"
dependencies = [
    "queue-core",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["host"]
```

- [ ] **Step 2: Create __init__.py**

```python
from host.submitter import JobSubmitter

__all__ = ["JobSubmitter"]
```

- [ ] **Step 3: Create submitter.py**

```python
from pathlib import Path
from typing import Any

from queue_core import Job, TemplateRegistry


class JobSubmitter:
    def __init__(self, queue_dir: str | Path, registry: TemplateRegistry | None = None):
        from queue_core import FileQueue
        
        self.queue = FileQueue(queue_dir)
        self.registry = registry or TemplateRegistry()

    def submit(self, template_name: str, payload: dict[str, Any]) -> Job:
        template = self.registry.get(template_name)
        
        if template is None:
            raise ValueError(f"Unknown template: {template_name}")
        
        valid, error = template.validate(payload)
        if not valid:
            raise ValueError(f"Invalid payload for template '{template_name}': {error}")
        
        job = Job(template_name=template_name, payload=payload)
        self.queue.enqueue(job)
        return job

    def submit_raw(self, template_name: str, payload: dict[str, Any]) -> Job:
        job = Job(template_name=template_name, payload=payload)
        self.queue.enqueue(job)
        return job

    def get_pending_jobs(self) -> list[Job]:
        return self.queue.get_pending()
```

- [ ] **Step 4: Commit**

```bash
git add packages/host/
git commit -m "feat: create host package for job submission"
```

---

### Task 5: Add Host Tests

**Files:**
- Create: `packages/host/tests/__init__.py`
- Create: `packages/host/tests/test_submitter.py`

- [ ] **Step 1: Create __init__.py**

```python
```

- [ ] **Step 2: Create test_submitter.py**

```python
import pytest
import tempfile
from pathlib import Path
from queue_core import Template, TemplateRegistry, PydanticValidator
from pydantic import BaseModel
from host.submitter import JobSubmitter


class TestPayload(BaseModel):
    message: str


def test_submit_job():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = TemplateRegistry()
        registry.register(Template("test", validator=PydanticValidator(TestPayload)))
        
        submitter = JobSubmitter(tmpdir, registry)
        job = submitter.submit("test", {"message": "hello"})
        
        assert job.template_name == "test"
        assert job.payload == {"message": "hello"}


def test_submit_unknown_template():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = TemplateRegistry()
        submitter = JobSubmitter(tmpdir, registry)
        
        with pytest.raises(ValueError, match="Unknown template"):
            submitter.submit("unknown", {})


def test_submit_invalid_payload():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = TemplateRegistry()
        registry.register(Template("test", validator=PydanticValidator(TestPayload)))
        
        submitter = JobSubmitter(tmpdir, registry)
        
        with pytest.raises(ValueError, match="Invalid payload"):
            submitter.submit("test", {})


def test_submit_raw():
    with tempfile.TemporaryDirectory() as tmpdir:
        registry = TemplateRegistry()
        submitter = JobSubmitter(tmpdir, registry)
        
        job = submitter.submit_raw("any_template", {"data": 123})
        
        assert job.template_name == "any_template"
        assert job.payload == {"data": 123}
```

- [ ] **Step 3: Run tests**

```bash
cd packages/host && uv run pytest tests/ -v
```
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add packages/host/tests/
git commit -m "test: add tests for host package"
```

---

### Task 6: Create Worker Package

**Files:**
- Create: `packages/worker/pyproject.toml`
- Create: `packages/worker/worker/__init__.py`
- Create: `packages/worker/worker/processor.py`
- Create: `packages/worker/worker/handlers.py`

- [ ] **Step 1: Create worker pyproject.toml**

```toml
[project]
name = "worker"
version = "0.1.0"
description = "Job processing worker environment"
requires-python = ">=3.11"
dependencies = [
    "queue-core",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["worker"]
```

- [ ] **Step 2: Create __init__.py**

```python
from worker.processor import JobProcessor
from worker.handlers import ExampleHandler

__all__ = ["JobProcessor", "ExampleHandler"]
```

- [ ] **Step 3: Create handlers.py**

```python
from typing import Any, Protocol


class JobHandler(Protocol):
    def handle(self, payload: dict[str, Any]) -> Any: ...


class ExampleHandler:
    def handle(self, payload: dict[str, Any]) -> str:
        message = payload.get("message", "no message")
        return f"Processed: {message}"


class PrintHandler:
    def handle(self, payload: dict[str, Any]) -> None:
        print(f"Job payload: {payload}")


class EchoHandler:
    def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        return payload
```

- [ ] **Step 4: Create processor.py**

```python
import time
from pathlib import Path
from typing import Any, Callable

from queue_core import FileQueue, Job, Template, TemplateRegistry


class JobProcessor:
    def __init__(
        self,
        queue_dir: str | Path,
        registry: TemplateRegistry | None = None,
        poll_interval: float = 1.0,
    ):
        self.queue = FileQueue(queue_dir)
        self.registry = registry or TemplateRegistry()
        self.poll_interval = poll_interval
        self._running = False
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {}

    def register_handler(self, template_name: str, handler: Callable[[dict[str, Any]], Any]) -> None:
        self._handlers[template_name] = handler

    def process_job(self, job: Job) -> bool:
        handler = self._handlers.get(job.template_name)
        
        if handler is None:
            self.queue.fail(job, f"No handler registered for template '{job.template_name}'")
            return False
        
        try:
            result = handler(job.payload)
            job.result = result
            self.queue.complete(job)
            return True
        except Exception as e:
            self.queue.fail(job, str(e))
            return False

    def process_one(self) -> bool:
        job = self.queue.dequeue()
        if job is None:
            return False
        return self.process_job(job)

    def run(self) -> None:
        self._running = True
        while self._running:
            if not self.process_one():
                time.sleep(self.poll_interval)

    def stop(self) -> None:
        self._running = False
```

- [ ] **Step 5: Commit**

```bash
git add packages/worker/
git commit -m "feat: create worker package for job processing"
```

---

### Task 7: Add Worker Tests

**Files:**
- Create: `packages/worker/tests/__init__.py`
- Create: `packages/worker/tests/test_processor.py`
- Create: `packages/worker/tests/test_handlers.py`

- [ ] **Step 1: Create __init__.py**

```python
```

- [ ] **Step 2: Create test_handlers.py**

```python
import pytest
from worker.handlers import ExampleHandler, PrintHandler, EchoHandler


def test_example_handler():
    handler = ExampleHandler()
    result = handler.handle({"message": "hello"})
    assert result == "Processed: hello"


def test_example_handler_default():
    handler = ExampleHandler()
    result = handler.handle({})
    assert result == "Processed: no message"


def test_echo_handler():
    handler = EchoHandler()
    payload = {"key": "value", "num": 42}
    result = handler.handle(payload)
    assert result == payload
```

- [ ] **Step 3: Create test_processor.py**

```python
import pytest
import tempfile
from pathlib import Path
from queue_core import Job, TemplateRegistry
from worker.processor import JobProcessor


def handler(payload: dict) -> str:
    return f"result: {payload.get('data', 'none')}"


def test_process_job_success():
    with tempfile.TemporaryDirectory() as tmpdir:
        processor = JobProcessor(tmpdir)
        processor.register_handler("test", handler)
        
        job = Job(template_name="test", payload={"data": 123})
        processor.queue.enqueue(job)
        
        result = processor.process_one()
        assert result is True
        
        completed = processor.queue.get_pending()
        assert len(completed) == 0


def test_process_job_no_handler():
    with tempfile.TemporaryDirectory() as tmpdir:
        processor = JobProcessor(tmpdir)
        
        job = Job(template_name="unknown", payload={})
        processor.queue.enqueue(job)
        
        result = processor.process_one()
        assert result is False


def test_process_empty_queue():
    with tempfile.TemporaryDirectory() as tmpdir:
        processor = JobProcessor(tmpdir)
        result = processor.process_one()
        assert result is False
```

- [ ] **Step 4: Run tests**

```bash
cd packages/worker && uv run pytest tests/ -v
```
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add packages/worker/tests/
git commit -m "test: add tests for worker package"
```

---

### Task 8: Create Example Usage Script

**Files:**
- Create: `examples/basic_usage.py`

- [ ] **Step 1: Create example script**

```python
#!/usr/bin/env python3
"""
Basic usage example of the job queue system.

This demonstrates:
1. Setting up templates with validation
2. Submitting jobs from the host
3. Processing jobs with the worker
"""

import tempfile
from pathlib import Path

from pydantic import BaseModel
from queue_core import Template, TemplateRegistry, PydanticValidator
from host import JobSubmitter
from worker import JobProcessor


class EmailPayload(BaseModel):
    to: str
    subject: str
    body: str


class EmailHandler:
    def handle(self, payload: dict) -> str:
        print(f"Sending email to: {payload['to']}")
        print(f"Subject: {payload['subject']}")
        print(f"Body: {payload['body']}")
        return "email_sent"


def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        queue_dir = Path(tmpdir) / "queue"
        
        # Setup registry with templates
        registry = TemplateRegistry()
        registry.register(
            Template("email", validator=PydanticValidator(EmailPayload))
        )
        
        # Host: Submit jobs
        submitter = JobSubmitter(queue_dir, registry)
        
        job1 = submitter.submit("email", {
            "to": "user@example.com",
            "subject": "Hello",
            "body": "This is a test email"
        })
        print(f"Submitted job: {job1.id}")
        
        job2 = submitter.submit("email", {
            "to": "admin@example.com",
            "subject": "Alert",
            "body": "System alert message"
        })
        print(f"Submitted job: {job2.id}")
        
        # Worker: Process jobs
        processor = JobProcessor(queue_dir, registry)
        processor.register_handler("email", EmailHandler().handle)
        
        print("\nProcessing jobs...")
        while processor.process_one():
            pass
        
        print("All jobs processed!")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run example**

```bash
uv run python examples/basic_usage.py
```
Expected: Script runs and shows job submission/processing

- [ ] **Step 3: Commit**

```bash
git add examples/
git commit -m "docs: add basic usage example"
```

---

### Task 9: Create README Documentation

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create README**

```markdown
# Fleet - Job Queue System with Templates

A Python job queue system where jobs are submitted to workers using configurable templates, with separate environments for host (job submitter) and worker (job processor).

## Features

- **Template-based jobs**: Define job types with validation schemas
- **Separate environments**: Host and worker run in isolated Python environments
- **File-based queue**: Simple, persistent queue with file locking
- **Pydantic validation**: Type-safe job payload validation

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Sync all packages
uv sync
```

## Project Structure

```
fleet/
├── packages/
│   ├── queue-core/    # Shared queue infrastructure
│   ├── host/          # Job submission environment
│   └── worker/        # Job processing environment
└── examples/          # Usage examples
```

## Quick Start

```python
from pydantic import BaseModel
from queue_core import Template, TemplateRegistry, PydanticValidator
from host import JobSubmitter
from worker import JobProcessor

# Define job schema
class EmailPayload(BaseModel):
    to: str
    subject: str
    body: str

# Setup
registry = TemplateRegistry()
registry.register(Template("email", validator=PydanticValidator(EmailPayload)))

# Host: Submit job
submitter = JobSubmitter("./queue", registry)
job = submitter.submit("email", {
    "to": "user@example.com",
    "subject": "Hello",
    "body": "Test email"
})

# Worker: Process jobs
processor = JobProcessor("./queue", registry)
processor.register_handler("email", lambda p: print(f"Sending to {p['to']}"))
processor.run()  # Runs indefinitely
```

## Running the Example

```bash
uv run python examples/basic_usage.py
```

## Architecture

### Host Environment
- Submits jobs to the queue
- Validates jobs against templates before submission
- Can query pending jobs

### Worker Environment  
- Polls queue for pending jobs
- Processes jobs using registered handlers
- Updates job status (completed/failed)

### Templates
- Define job payload structure (via Pydantic)
- Optional validation logic
- Associated with handler functions in worker

## Development

```bash
# Run tests for all packages
uv run pytest packages/*/tests/ -v

# Run tests for specific package
cd packages/host && uv run pytest tests/ -v
```

## License

MIT
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage instructions"
```

---

### Task 10: Final Verification

**Files:**
- All packages

- [ ] **Step 1: Run all tests**

```bash
uv run pytest packages/*/tests/ -v
```
Expected: All tests pass

- [ ] **Step 2: Verify example runs**

```bash
uv run python examples/basic_usage.py
```
Expected: Example completes successfully

- [ ] **Step 3: Final commit**

```bash
git status
```
Expected: Clean working tree

---

## Self-Review Checklist

**1. Spec coverage:**
- ✅ Job queue system with file-based backend
- ✅ Template system for job types
- ✅ Pydantic validation for job payloads
- ✅ Separate host and worker environments
- ✅ uv workspace management

**2. No placeholders:**
- All steps contain actual code
- All file paths are explicit
- All commands are complete

**3. Type consistency:**
- Job, JobStatus, Template, TemplateRegistry used consistently
- Handler signatures match across packages
- File paths use str | Path consistently

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-30-job-queue-system.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
