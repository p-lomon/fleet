from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException

from queue_core import FileQueue, Job


def create_router(queue_dir: str | Path) -> APIRouter:
    router = APIRouter()
    queue = FileQueue(queue_dir)

    @router.get("/stats")
    def get_stats() -> dict[str, Any]:
        """Get queue statistics."""
        pending = len(queue.get_pending())
        processing = len(list(queue.processing_dir.glob("*.json")))
        completed = len(list(queue.completed_dir.glob("*.json")))
        failed = len(list(queue.failed_dir.glob("*.json")))
        
        return {
            "pending": pending,
            "processing": processing,
            "completed": completed,
            "failed": failed,
            "total": pending + processing + completed + failed,
        }

    @router.get("/jobs")
    def get_jobs(status: str | None = None) -> list[dict[str, Any]]:
        """Get list of jobs, optionally filtered by status."""
        jobs = []
        
        # Pending jobs
        if status is None or status == "pending":
            for job in queue.get_pending():
                jobs.append(job.to_dict())
        
        # Processing jobs
        if status is None or status == "processing":
            for path in queue.processing_dir.glob("*.json"):
                jobs.append(queue._read_job(path))
        
        # Completed jobs
        if status is None or status == "completed":
            for path in queue.completed_dir.glob("*.json"):
                jobs.append(queue._read_job(path))
        
        # Failed jobs
        if status is None or status == "failed":
            for path in queue.failed_dir.glob("*.json"):
                jobs.append(queue._read_job(path))
        
        # Sort by created_at descending
        jobs.sort(key=lambda j: j["created_at"], reverse=True)
        return jobs

    @router.get("/jobs/{job_id}")
    def get_job(job_id: str) -> dict[str, Any]:
        """Get a specific job by ID."""
        # Search all directories
        for subdir in [queue.pending_dir, queue.processing_dir, queue.completed_dir, queue.failed_dir]:
            path = subdir / f"{job_id}.json"
            if path.exists():
                return queue._read_job(path).to_dict()
        
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return router
