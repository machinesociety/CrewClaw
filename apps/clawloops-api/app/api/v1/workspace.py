from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

from app.core.dependencies import get_app_settings, get_user_service, require_active_user
from app.domain.users import ObservedState
from app.infra.runtime_manager_client import RuntimeManagerClient
from app.schemas.runtime import WorkspaceEntryReason
from app.schemas.workspace import WorkspaceEntryResponse
from app.services.openclaw_url import merge_with_existing_token, replace_openclaw_path
from app.services.user_service import UserService


router = APIRouter(tags=["workspace"])


@router.get("/workspace-entry", response_model=WorkspaceEntryResponse)
async def get_workspace_entry(
    ctx=Depends(require_active_user),
    user_service: UserService = Depends(get_user_service),
    settings=Depends(get_app_settings),
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

    # Reconcile status from runtime-manager container facts to avoid stale binding projection.
    try:
        rm_client = RuntimeManagerClient(settings.runtime_manager_base_url or "http://runtime-manager:18080")
        container_fact = rm_client.get_container(binding.runtime_id)
        fact_observed = container_fact.get("observedState")
        fact_browser_url = merge_with_existing_token(
            new_browser_url=container_fact.get("browserUrl"),
            existing_browser_url=binding.browser_url,
        )
        if fact_observed and (
            fact_observed != binding.observed_state.value.lower() or fact_browser_url != binding.browser_url
        ):
            mapped = {
                "creating": ObservedState.CREATING,
                "running": ObservedState.RUNNING,
                "stopped": ObservedState.STOPPED,
                "error": ObservedState.ERROR,
                "deleted": ObservedState.DELETED,
            }
            user_service.update_runtime_binding_state(
                user_id=ctx.userId,
                desired_state=binding.desired_state,
                observed_state=mapped.get(fact_observed, binding.observed_state),
                browser_url=fact_browser_url,
                internal_endpoint=binding.internal_endpoint,
                last_error=binding.last_error,
            )
            binding = user_service.get_runtime_binding(ctx.userId) or binding
    except Exception:
        pass

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


@router.get("/workspace-entry/redirect", include_in_schema=False)
async def redirect_workspace_entry(
    ctx=Depends(require_active_user),
    user_service: UserService = Depends(get_user_service),
    path: str | None = None,
) -> RedirectResponse:
    """
    通过控制面中间跳转，避免前端直接拼接 OpenClaw 明文地址。
    """
    binding = user_service.get_runtime_binding(ctx.userId)
    if binding is None or binding.observed_state != ObservedState.RUNNING or not binding.browser_url:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="workspace runtime not ready",
        )

    target = binding.browser_url
    if path is not None:
        if path not in {"/chat", "/skills"}:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid path")
        target = replace_openclaw_path(binding.browser_url, path) or binding.browser_url
    return RedirectResponse(url=target, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
