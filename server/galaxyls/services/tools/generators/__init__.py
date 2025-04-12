class DisplayableException(Exception):
    """Exception class for displaying error messages in the UI."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
