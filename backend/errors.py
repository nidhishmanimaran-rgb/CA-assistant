"""User-safe errors: never expose provider exceptions or document contents."""
class AppError(Exception):
    def __init__(self, message: str, code: str = "application_error"):
        super().__init__(message)
        self.code = code
