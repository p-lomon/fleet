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
