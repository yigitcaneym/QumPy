"""Friendly error type used everywhere in QumPy."""


class QumError(Exception):
    """An error with a plain-language explanation and (optionally) a hint."""

    def __init__(self, message, hint=None):
        self.hint = hint
        text = message if not hint else f"{message}\n  Hint: {hint}"
        super().__init__(text)


class QumAttributeError(QumError, AttributeError):
    """A missing attribute / gate. Also an AttributeError, so hasattr() works."""
