import time
from pathlib import Path
from typing import Any, Callable

from queue_core import FileQueue, Job, TemplateRegistry


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
