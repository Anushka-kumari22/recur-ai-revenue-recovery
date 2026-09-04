class RecurApplicationError(Exception):
    """
    Base exception for all application-specific errors.
    """

    status_code = 500
    default_message = (
        "An internal application error occurred."
    )

    def __init__(
        self,
        message: str | None = None,
    ) -> None:
        self.message = (
            message
            if message is not None
            else self.default_message
        )

        super().__init__(
            self.message
        )


class PipelineProcessingError(
    RecurApplicationError,
):
    """
    Raised when the revenue recovery pipeline
    cannot process a payment failure.
    """

    status_code = 500

    default_message = (
        "The payment recovery pipeline "
        "could not process the request."
    )


class PersistenceError(
    RecurApplicationError,
):
    """
    Raised when application data cannot be
    persisted or retrieved.
    """

    status_code = 500

    default_message = (
        "The recovery result could not be "
        "stored successfully."
    )


class ResourceNotFoundError(
    RecurApplicationError,
):
    """
    Raised when a requested application resource
    does not exist.
    """

    status_code = 404

    default_message = (
        "The requested resource was not found."
    )

class RecurApplicationError(Exception):
    """
    Base exception for all expected application errors.
    """

    status_code = 500

    def __init__(
        self,
        message: str,
    ) -> None:
        self.message = message

        super().__init__(message)


class ResourceNotFoundError(RecurApplicationError):
    """
    Raised when a requested application resource
    cannot be found.
    """

    status_code = 404


class PersistenceError(RecurApplicationError):
    """
    Raised when a database persistence operation fails.
    """

    status_code = 500


class PipelineProcessingError(RecurApplicationError):
    """
    Raised when the revenue recovery pipeline
    cannot process a payment failure.
    """

    status_code = 500