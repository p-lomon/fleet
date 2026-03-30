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

## Dashboard

Start the web dashboard to monitor jobs in real-time:

```bash
# Start with default queue directory
uv run python dashboard-cli.py

# Start with custom queue directory
uv run python dashboard-cli.py /path/to/queue

# Start on different host/port
uv run python dashboard-cli.py --host 0.0.0.0 --port 8080
```

Then open http://127.0.0.1:8000 in your browser.

The dashboard shows:
- Real-time queue statistics (pending, processing, completed, failed)
- List of all jobs with status filtering
- Job details including payload and results
- Auto-refresh every 3 seconds

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
