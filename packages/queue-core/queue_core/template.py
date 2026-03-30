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
