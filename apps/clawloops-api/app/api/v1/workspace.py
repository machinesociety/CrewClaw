from fastapi import APIRouter, Depends

from app.core.dependencies import get_user_service, require_active_user
from app.domain.users import ObservedState
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
            hasWorkspace=False,
            runtimeId=None,
            browserUrl=None,
            reason="RUNTIME_PREPARING",
        )

    if binding.observed_state == ObservedState.RUNNING and binding.browser_url:
        return WorkspaceEntryResponse(
            ready=True,
            hasWorkspace=True,
            runtimeId=binding.runtime_id,
            browserUrl=binding.browser_url,
            reason=None,
        )

    return WorkspaceEntryResponse(
        ready=False,
        hasWorkspace=True,
        runtimeId=binding.runtime_id,
        browserUrl=None,
        reason="RUNTIME_PREPARING",
    )

