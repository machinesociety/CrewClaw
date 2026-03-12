from pydantic import BaseModel


class UsageSummaryResponse(BaseModel):
    user_id: str
    total_tokens: int
    used_tokens: int

