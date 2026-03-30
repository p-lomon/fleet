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
