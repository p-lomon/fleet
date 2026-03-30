from dataclasses import dataclass, field
from datetime import datetime, timezone
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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
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
