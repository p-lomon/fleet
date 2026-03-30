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
