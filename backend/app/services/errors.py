class AppError(Exception):
    status_code = 500


class NotFoundError(AppError):
    status_code = 404


class BadRequestError(AppError):
    status_code = 400


class AuthError(AppError):
    status_code = 401
