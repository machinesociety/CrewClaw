from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import Type


@dataclass(slots=True)
class ErrorSpec:
    http_status: int
    code: str
    message: str


class AppError(Exception):
    """应用内部统一异常基类。"""

    spec: ErrorSpec

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            # 允许在默认 message 基础上覆盖说明
            self.spec = ErrorSpec(
                http_status=self.spec.http_status,
                code=self.spec.code,
                message=message,
            )
        super().__init__(self.spec.message)


class UnauthenticatedError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.UNAUTHORIZED,
        code="UNAUTHENTICATED",
        message="Authentication required.",
    )


class InvalidCredentialsError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.UNAUTHORIZED,
        code="INVALID_CREDENTIALS",
        message="Invalid username or password.",
    )


class PasswordChangeRequiredError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.FORBIDDEN,
        code="PASSWORD_CHANGE_REQUIRED",
        message="Password change required.",
    )


class SessionError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        code="SESSION_ERROR",
        message="Session error.",
    )


class CurrentPasswordIncorrectError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="CURRENT_PASSWORD_INCORRECT",
        message="Current password incorrect.",
    )


class PasswordChangeInvalidError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="PASSWORD_CHANGE_INVALID",
        message="Password change invalid.",
    )


class InvitationNotFoundError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.NOT_FOUND,
        code="INVITATION_NOT_FOUND",
        message="Invitation not found.",
    )


class InvitationExpiredError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.GONE,
        code="INVITATION_EXPIRED",
        message="Invitation expired.",
    )


class InvitationRevokedError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.CONFLICT,
        code="INVITATION_REVOKED",
        message="Invitation revoked.",
    )


class InvitationAlreadyConsumedError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.CONFLICT,
        code="INVITATION_ALREADY_CONSUMED",
        message="Invitation already consumed.",
    )


class InvitationUsernameMismatchError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="INVITATION_USERNAME_MISMATCH",
        message="Invitation username mismatch.",
    )


class InvitationPasswordInvalidError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="INVITATION_PASSWORD_INVALID",
        message="Invitation password invalid.",
    )


class InvitationError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.INTERNAL_SERVER_ERROR,
        code="INVITATION_ERROR",
        message="Invitation error.",
    )


class UserDisabledError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.FORBIDDEN,
        code="USER_DISABLED",
        message="User is disabled.",
    )


class AccessDeniedError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.FORBIDDEN,
        code="ACCESS_DENIED",
        message="Access denied.",
    )


class RuntimeNotFoundError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.NOT_FOUND,
        code="RUNTIME_NOT_FOUND",
        message="Runtime not found.",
    )


class UserNotFoundError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.NOT_FOUND,
        code="USER_NOT_FOUND",
        message="User not found.",
    )


class ModelNotFoundError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.NOT_FOUND,
        code="MODEL_NOT_FOUND",
        message="Model not found.",
    )


class ProviderCredentialNotFoundError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.NOT_FOUND,
        code="PROVIDER_CREDENTIAL_NOT_FOUND",
        message="Provider credential not found.",
    )


class ProviderCredentialInvalidError(AppError):
    spec = ErrorSpec(
        http_status=HTTPStatus.UNPROCESSABLE_ENTITY,
        code="PROVIDER_CREDENTIAL_INVALID",
        message="Provider credential is invalid.",
    )


ERROR_TYPE_MAP: dict[Type[AppError], ErrorSpec] = {
    UnauthenticatedError: UnauthenticatedError.spec,
    InvalidCredentialsError: InvalidCredentialsError.spec,
    UserDisabledError: UserDisabledError.spec,
    AccessDeniedError: AccessDeniedError.spec,
    PasswordChangeRequiredError: PasswordChangeRequiredError.spec,
    RuntimeNotFoundError: RuntimeNotFoundError.spec,
    UserNotFoundError: UserNotFoundError.spec,
    ModelNotFoundError: ModelNotFoundError.spec,
    ProviderCredentialNotFoundError: ProviderCredentialNotFoundError.spec,
    ProviderCredentialInvalidError: ProviderCredentialInvalidError.spec,
    SessionError: SessionError.spec,
    CurrentPasswordIncorrectError: CurrentPasswordIncorrectError.spec,
    PasswordChangeInvalidError: PasswordChangeInvalidError.spec,
    InvitationNotFoundError: InvitationNotFoundError.spec,
    InvitationExpiredError: InvitationExpiredError.spec,
    InvitationRevokedError: InvitationRevokedError.spec,
    InvitationAlreadyConsumedError: InvitationAlreadyConsumedError.spec,
    InvitationUsernameMismatchError: InvitationUsernameMismatchError.spec,
    InvitationPasswordInvalidError: InvitationPasswordInvalidError.spec,
    InvitationError: InvitationError.spec,
}

