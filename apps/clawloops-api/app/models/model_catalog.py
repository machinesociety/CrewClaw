from __future__ import annotations

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.domain.models import ModelSource, PricingType


class GovernedModelCatalogModel(Base):
    __tablename__ = "governed_model_catalog"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source: Mapped[ModelSource] = mapped_column(Enum(ModelSource))
    pricing_type: Mapped[PricingType] = mapped_column(Enum(PricingType), default=PricingType.FREE)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    user_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    default_route: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_provider_credential_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    upstream_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
