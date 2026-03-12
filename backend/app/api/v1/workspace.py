from fastapi import APIRouter

from app.schemas.workspace import WorkspaceEntryResponse


router = APIRouter(tags=["workspace"])


@router.get("/workspace-entry", response_model=WorkspaceEntryResponse)
async def get_workspace_entry() -> WorkspaceEntryResponse:
    """
    获取当前用户工作区入口。

    TODO:
    - 结合 UserRuntimeBinding 与用户状态判断 ready 与 reason。
    """
    return WorkspaceEntryResponse(
        ready=True,
        runtime_id="rt_001",
        browser_url="https://u-001.crewclaw.example.com",
        reason=None,
    )

