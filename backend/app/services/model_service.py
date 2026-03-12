from app.domain.models import Model, ModelBinding, UsageSummary, ModelSource, BindingSource


class ModelService:
    """
    模型与绑定相关服务。

    TODO:
    - 连接模型仓储与凭据仓储。
    - 渲染 gateway-config 并写入配置文件。
    """

    def list_models_for_user(self, user_id: str) -> list[Model]:
        _ = user_id
        return [
            Model(
                model_id="gpt-4-mini",
                name="GPT-4 Mini",
                provider="openai",
                source=ModelSource.SHARED,
                enabled=True,
            )
        ]

    def list_bindings_for_user(self, user_id: str) -> list[ModelBinding]:
        _ = user_id
        return []

    def update_binding(self, user_id: str, model_id: str, credential_id: str | None) -> ModelBinding:
        _ = (user_id, model_id)
        return ModelBinding(
            user_id="u_001",
            model_id=model_id,
            credential_id=credential_id,
            source=BindingSource.USER_OWNED,
        )


class CredentialService:
    """
    凭据托管与校验服务。

    TODO:
    - 将 secret 持久化到安全的 secret store。
    - 通过模型网关或 provider 执行校验。
    """

    # 占位：具体方法待与 API 层需求一起完善。
    pass


class UsageService:
    """
    用量汇总服务。

    TODO:
    - 聚合 OpenClaw 上报与网关日志。
    """

    def get_user_usage(self, user_id: str) -> UsageSummary:
        _ = user_id
        return UsageSummary(user_id="u_001", total_tokens=1_000_000)

