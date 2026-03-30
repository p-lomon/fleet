import pytest
from typing import Any
from pydantic import BaseModel, ValidationError
from queue_core.template import Template, TemplateRegistry, PydanticValidator


class TestTemplate:
    def test_template_creation_without_validator_or_handler(self):
        """Test template can be created without validator or handler"""
        template = Template(name="test_template")
        assert template.name == "test_template"

    def test_template_validate_without_validator(self):
        """Test validate returns True when no validator is set"""
        template = Template(name="test_template")
        valid, error = template.validate({"key": "value"})
        assert valid is True
        assert error is None

    def test_template_validate_with_validator(self):
        """Test validate calls validator when set"""
        class TestValidator:
            def validate(self, payload: dict[str, Any]) -> tuple[bool, str | None]:
                if "required" in payload:
                    return True, None
                return False, "Missing required field"

        template = Template(name="test_template", validator=TestValidator())
        
        valid, error = template.validate({"required": "value"})
        assert valid is True
        assert error is None
        
        valid, error = template.validate({})
        assert valid is False
        assert error == "Missing required field"

    def test_template_handle_without_handler_raises(self):
        """Test handle raises ValueError when no handler is set"""
        template = Template(name="test_template")
        with pytest.raises(ValueError, match="No handler registered"):
            template.handle({})

    def test_template_handle_with_handler(self):
        """Test handle calls handler when set"""
        class TestHandler:
            def handle(self, payload: dict[str, Any]) -> Any:
                return {"processed": True, "data": payload}

        template = Template(name="test_template", handler=TestHandler())
        result = template.handle({"key": "value"})
        assert result == {"processed": True, "data": {"key": "value"}}


class TestPydanticValidator:
    def test_pydantic_validator_validates_correct_payload(self):
        """Test PydanticValidator accepts valid payload"""
        class TestModel(BaseModel):
            name: str
            count: int

        validator = PydanticValidator(TestModel)
        valid, error = validator.validate({"name": "test", "count": 5})
        assert valid is True
        assert error is None

    def test_pydantic_validator_rejects_invalid_payload(self):
        """Test PydanticValidator rejects invalid payload"""
        class TestModel(BaseModel):
            name: str
            count: int

        validator = PydanticValidator(TestModel)
        valid, error = validator.validate({"name": "test"})  # missing count
        assert valid is False
        assert error is not None

    def test_pydantic_validator_rejects_wrong_types(self):
        """Test PydanticValidator rejects wrong types"""
        class TestModel(BaseModel):
            name: str
            count: int

        validator = PydanticValidator(TestModel)
        valid, error = validator.validate({"name": "test", "count": "not_an_int"})
        assert valid is False
        assert error is not None


class TestTemplateRegistry:
    def test_register_template(self):
        """Test registering a template"""
        registry = TemplateRegistry()
        template = Template(name="test_template")
        registry.register(template)
        
        retrieved = registry.get("test_template")
        assert retrieved is template

    def test_get_nonexistent_template(self):
        """Test getting a template that doesn't exist"""
        registry = TemplateRegistry()
        result = registry.get("nonexistent")
        assert result is None

    def test_list_templates(self):
        """Test listing all registered templates"""
        registry = TemplateRegistry()
        registry.register(Template(name="template1"))
        registry.register(Template(name="template2"))
        registry.register(Template(name="template3"))
        
        templates = registry.list_templates()
        assert len(templates) == 3
        assert "template1" in templates
        assert "template2" in templates
        assert "template3" in templates

    def test_overwrite_template(self):
        """Test that registering with same name overwrites"""
        registry = TemplateRegistry()
        template1 = Template(name="test")
        template2 = Template(name="test")
        
        registry.register(template1)
        registry.register(template2)
        
        retrieved = registry.get("test")
        assert retrieved is template2
