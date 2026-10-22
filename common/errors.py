"""Errors that name the object, the field, and what was expected."""


class ModelError(ValueError):
    def __init__(self, object_name: str, field: str, expected: str):
        self.object_name = object_name
        self.field = field
        self.expected = expected
        super().__init__(f"{object_name}: field {field}: expected {expected}")


class SigningUnavailable(RuntimeError):
    """Raised when this process cannot create a real signature."""


class CheckError(ValueError):
    """A check id or its arguments cannot be run."""
