from typing import List, Optional
from datetime import datetime


class UsageRecord:
    def __init__(self, user_id: str, model_id: str, model_name: Optional[str], tokens: int, cost: Optional[float] = None):
        self.user_id = user_id
        self.model_id = model_id
        self.model_name = model_name
        self.tokens = tokens
        self.cost = cost
        self.timestamp = datetime.utcnow()


class UsageRepository:
    def add_usage(self, usage: UsageRecord) -> None:
        raise NotImplementedError
    
    def get_all_usage(self) -> List[UsageRecord]:
        raise NotImplementedError
    
    def get_usage_by_user(self, user_id: str) -> List[UsageRecord]:
        raise NotImplementedError
    
    def get_usage_by_model(self, model_id: str) -> List[UsageRecord]:
        raise NotImplementedError


class InMemoryUsageRepository(UsageRepository):
    def __init__(self):
        self.records: List[UsageRecord] = []
    
    def add_usage(self, usage: UsageRecord) -> None:
        self.records.append(usage)
    
    def get_all_usage(self) -> List[UsageRecord]:
        return self.records
    
    def get_usage_by_user(self, user_id: str) -> List[UsageRecord]:
        return [r for r in self.records if r.user_id == user_id]
    
    def get_usage_by_model(self, model_id: str) -> List[UsageRecord]:
        return [r for r in self.records if r.model_id == model_id]


def get_inmemory_usage_repository() -> UsageRepository:
    """返回内存实现的 UsageRepository 单例"""
    if not hasattr(get_inmemory_usage_repository, "_instance"):
        get_inmemory_usage_repository._instance = InMemoryUsageRepository()
    return get_inmemory_usage_repository._instance
