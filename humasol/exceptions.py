"""Module providing system exceptions."""


class HumasolException(Exception):
    """Base system exception."""


class ModelException(HumasolException):
    """Exception class raised by the models modules."""


class IllegalArgumentException(ModelException):
    """Exception raised when invalid parameters are passed to a model."""


class MissingArgumentException(ModelException):
    """Raised when a required argument is not found in the parameters."""


class RuntimeException(ModelException, RuntimeError):
    """Raised when an unexpected state occurs."""


class IllegalStateException(ModelException):
    """Raised when the model element is or would be put in an illegal state."""


class PassedPeriod(ModelException):
    """Exception raised when a period is given which has already passed."""


class GoogleException(HumasolException):
    """Exception raised by the google repository."""


class FormatException(HumasolException):
    """Invalid format."""


class FileNotFoundException(HumasolException):
    """Raised when the requested file cannot be found."""


class ProjectNotFoundException(HumasolException):
    """Raised when there is no project with the requested ID."""


class WebException(HumasolException):
    """Raised by the UI module."""


class FormError(WebException):
    """Raised when a problem occurs with form content."""


class Error404(WebException):
    """HTTP 404 error."""


class Error500(WebException):
    """HTTP 500 error."""
