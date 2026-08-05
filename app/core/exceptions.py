"""Custom exceptions for the application."""


class AgenticRAGException(Exception):
    """Base exception."""
    pass


class DocumentProcessingError(AgenticRAGException):
    """Raised when document parsing fails."""
    pass


class VectorStoreError(AgenticRAGException):
    """Raised when vector DB operation fails."""
    pass


class LLMProviderError(AgenticRAGException):
    """Raised when LLM call fails."""
    pass


class HumanApprovalTimeoutError(AgenticRAGException):
    """Raised when human approval times out."""
    pass


class MaxIterationsExceededError(AgenticRAGException):
    """Raised when max retry loops exceeded."""
    pass