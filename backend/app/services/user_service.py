from app.domain.users import User, UserRuntimeBinding, DesiredState, ObservedState, RetentionPolicy


class UserService:
    """
    用户与 UserRuntimeBinding 相关服务。

    TODO:
    - 接入用户仓储与配额仓储。
    - 以 subjectId 幂等创建用户。
    """

    def get_or_create_user(self, subject_id: str) -> User:
        # TODO: 实现真实的获取或创建逻辑。
        _ = subject_id
        return User(
            user_id="u_001",
            subject_id=subject_id,
            tenant_id="t_default",
            role="user",  # type: ignore[arg-type]
            status="active",  # type: ignore[arg-type]
        )

    def get_runtime_binding(self, user_id: str) -> UserRuntimeBinding | None:
        # TODO: 从仓储中加载真实 binding。
        _ = user_id
        return UserRuntimeBinding(
            user_id="u_001",
            runtime_id="rt_001",
            volume_id="vol_001",
            image_ref="crewclaw-runtime-wrapper:openclaw-1.0.0",
            desired_state=DesiredState.RUNNING,
            observed_state=ObservedState.RUNNING,
            retention_policy=RetentionPolicy.PRESERVE_WORKSPACE,
            browser_url="https://u-001.crewclaw.example.com",
            internal_endpoint="http://crewclaw-u001:3000",
        )

