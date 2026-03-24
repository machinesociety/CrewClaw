from app.domain.users import User, UserRole, UserStatus


class AuthService:
    """
    身份与访问接入相关服务。

    TODO:
    - 对接 Authentik，基于请求上下文构造 AuthContext。
    - 支持识别 admin / disabled 等状态。
    """

    def get_mock_user(self) -> User:
        """
        占位实现：返回一个固定示例用户。
        """

        return User(
            user_id="u_001",
            subject_id="authentik:12345",
            tenant_id="t_default",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )

