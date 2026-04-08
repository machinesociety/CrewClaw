from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.repositories.usage_repository import UsageRepository, UsageRecord
from app.schemas.admin import AdminUsageSummaryResponse, AdminUsageByModel, AdminUsageByUser, AdminUsagePeriod


class UsageService:
    def __init__(self, usage_repo: UsageRepository):
        self.usage_repo = usage_repo
    
    def add_usage(self, user_id: str, model_id: str, model_name: str, tokens: int, cost: float = 0.0) -> None:
        """添加使用记录"""
        usage = UsageRecord(
            user_id=user_id,
            model_id=model_id,
            model_name=model_name,
            tokens=tokens,
            cost=cost
        )
        self.usage_repo.add_usage(usage)
    
    def get_total_usage(self) -> AdminUsageSummaryResponse:
        """获取总使用情况"""
        all_usage = self.usage_repo.get_all_usage()
        
        # 计算总请求数、总tokens和总费用
        total_requests = len(all_usage)
        total_tokens = sum(u.tokens for u in all_usage)
        total_cost = sum(u.cost or 0 for u in all_usage)
        
        # 按模型分组
        model_usage: Dict[str, Dict[str, Any]] = {}
        for u in all_usage:
            if u.model_id not in model_usage:
                model_usage[u.model_id] = {
                    "model_id": u.model_id,
                    "model_name": u.model_name,
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            model_usage[u.model_id]["requests"] += 1
            model_usage[u.model_id]["tokens"] += u.tokens
            model_usage[u.model_id]["cost"] += u.cost or 0
        
        # 按用户分组
        user_usage: Dict[str, Dict[str, Any]] = {}
        for u in all_usage:
            if u.user_id not in user_usage:
                user_usage[u.user_id] = {
                    "user_id": u.user_id,
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0
                }
            user_usage[u.user_id]["requests"] += 1
            user_usage[u.user_id]["tokens"] += u.tokens
            user_usage[u.user_id]["cost"] += u.cost or 0
        
        # 构建响应数据
        by_model = [
            AdminUsageByModel(
                modelId=v["model_id"],
                modelName=v["model_name"],
                requests=v["requests"],
                tokens=v["tokens"],
                cost=v["cost"]
            )
            for v in model_usage.values()
        ]
        
        by_user = [
            AdminUsageByUser(
                userId=v["user_id"],
                requests=v["requests"],
                tokens=v["tokens"],
                cost=v["cost"]
            )
            for v in user_usage.values()
        ]
        
        # 计算统计周期（最近30天）
        now = datetime.utcnow()
        start_date = now - timedelta(days=30)
        
        period = AdminUsagePeriod(
            from_=start_date.isoformat(),
            to=now.isoformat()
        )
        
        return AdminUsageSummaryResponse(
            totalRequests=total_requests,
            totalTokens=total_tokens,
            totalCost=total_cost,
            byModel=by_model,
            byUser=by_user,
            period=period
        )
