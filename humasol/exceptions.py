"""Module providing system exceptions."""


class HumasolException(Exception):
    """Base system exception."""


class AppConfigError(HumasolException):
    """Exception specific to the AppConfig class."""


class ModelException(HumasolException):
    """Exception class raised by the models modules."""


class AbstractClassException(HumasolException):
    """Exception class raised by an abstract class when it is instantiated."""


class IllegalArgumentException(ModelException):
    """Exception raised when invalid parameters are passed to a model."""


class IllegalOperationException(ModelException):
    """Exception raised when an illegal operation is performed on a model."""


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


class RepositoryException(HumasolException):
    """Raised when an error occurs in the repository."""


class FileNotFoundException(RepositoryException):
    """Raised when the requested file cannot be found."""


class NotDatamodelClassException(RepositoryException):
    """Raised when a wrong class is used for database access.

    Only ORM mapped classes have database capabilities. These are considered
    datamodels. When a class without such capabilities is used for database
    functionality it will raise this error.
    """


class InvalidRequestException(RepositoryException):
    """Raised on an invalid database request."""


class IntegrityException(RepositoryException):
    """Raised when a database request compromises its integrity."""


class IllegalFileContent(RepositoryException):
    """Raised when a file loaded from disk has ill-formatted content."""


class ObjectNotFoundException(RepositoryException):
    """Raised when there is no project with the requested ID."""


class WebException(HumasolException):
    """Raised by the UI module."""


class FormError(WebException):
    """Raised when a problem occurs with form content."""


class Error404(WebException):
    """HTTP 404 error."""


class Error500(WebException):
    """HTTP 500 error."""
