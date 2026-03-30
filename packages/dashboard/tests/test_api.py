import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient

from queue_core import Job, FileQueue
from dashboard.app import create_app


@pytest.fixture
def queue_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def client(queue_dir):
    app = create_app(queue_dir)
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_job(queue_dir):
    queue = FileQueue(queue_dir)
    job = Job(template_name="test", payload={"key": "value"})
    queue.enqueue(job)
    return job


def test_get_stats_empty(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] == 0
    assert data["total"] == 0


def test_get_stats_with_jobs(client, sample_job):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["pending"] == 1
    assert data["total"] == 1


def test_get_jobs(client, sample_job):
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == sample_job.id


def test_get_jobs_filtered(client, sample_job):
    response = client.get("/api/jobs?status=pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_job_by_id(client, sample_job):
    response = client.get(f"/api/jobs/{sample_job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_job.id


def test_get_job_not_found(client):
    response = client.get("/api/jobs/nonexistent-id")
    assert response.status_code == 404


def test_root_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
