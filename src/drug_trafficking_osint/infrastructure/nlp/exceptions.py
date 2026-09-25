"""Exception hierarchy for predictable preprocessing failures."""


class PreprocessingError(ValueError):
    """Base error raised when text cannot be prepared safely."""


class EmptyTextError(PreprocessingError):
    """Raised when input is absent or contains no meaningful text."""


class TextLengthError(PreprocessingError):
    """Raised when input violates configured minimum or maximum length limits."""


class UnsupportedLanguageError(PreprocessingError):
    """Raised when language detection returns a language outside policy."""


class InvalidConfigurationError(PreprocessingError):
    """Raised when environment-derived preprocessing configuration is invalid."""
