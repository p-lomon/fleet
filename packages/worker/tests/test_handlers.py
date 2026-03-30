"""Tests for worker handlers module."""

from worker.handlers import ExampleHandler, PrintHandler, EchoHandler


class TestExampleHandler:
    def test_handle_with_message(self):
        handler = ExampleHandler()
        result = handler.handle({"message": "hello"})
        assert result == "Processed: hello"

    def test_handle_without_message(self):
        handler = ExampleHandler()
        result = handler.handle({})
        assert result == "Processed: no message"

    def test_handle_with_extra_fields(self):
        handler = ExampleHandler()
        result = handler.handle({"message": "test", "extra": "data"})
        assert result == "Processed: test"


class TestPrintHandler:
    def test_handle_prints_payload(self, capsys):
        handler = PrintHandler()
        payload = {"key": "value", "number": 42}
        result = handler.handle(payload)
        captured = capsys.readouterr()
        assert "Job payload:" in captured.out
        assert "key" in captured.out
        assert "value" in captured.out
        assert result is None


class TestEchoHandler:
    def test_handle_returns_same_payload(self):
        handler = EchoHandler()
        payload = {"id": 123, "data": "test"}
        result = handler.handle(payload)
        assert result == payload
        assert result is payload  # EchoHandler returns the same reference

    def test_handle_empty_payload(self):
        handler = EchoHandler()
        result = handler.handle({})
        assert result == {}
