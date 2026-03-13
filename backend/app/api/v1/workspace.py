from fastapi import APIRouter, Depends

from app.core.dependencies import get_user_service, require_active_user
from app.domain.users import ObservedState
from app.schemas.runtime import WorkspaceEntryReason
from app.schemas.workspace import WorkspaceEntryResponse
from app.services.user_service import UserService


router = APIRouter(tags=["workspace"])


@router.get("/workspace-entry", response_model=WorkspaceEntryResponse)
async def get_workspace_entry(
    ctx=Depends(require_active_user),
    user_service: UserService = Depends(get_user_service),
) -> WorkspaceEntryResponse:
    """
    获取当前用户工作区入口。

    结合 UserRuntimeBinding 与用户状态判断 ready 与 reason。
    """
    binding = user_service.get_runtime_binding(ctx.userId)

    if binding is None:
        return WorkspaceEntryResponse(
            ready=False,
            runtimeId=None,
            browserUrl=None,
            reason=WorkspaceEntryReason.runtime_not_found,
        )

    if binding.observed_state == ObservedState.RUNNING and binding.browser_url:
        return WorkspaceEntryResponse(
            ready=True,
            runtimeId=binding.runtime_id,
            browserUrl=binding.browser_url,
            reason=None,
        )

    if binding.observed_state == ObservedState.CREATING:
        reason = WorkspaceEntryReason.runtime_starting
    elif binding.observed_state in (ObservedState.STOPPED, ObservedState.DELETED):
        reason = WorkspaceEntryReason.runtime_not_running
    elif binding.observed_state == ObservedState.ERROR:
        reason = WorkspaceEntryReason.runtime_error
    else:
        reason = WorkspaceEntryReason.runtime_not_running

    return WorkspaceEntryResponse(
        ready=False,
        runtimeId=binding.runtime_id,
        browserUrl=None,
        reason=reason,
    )

