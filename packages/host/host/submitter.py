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
