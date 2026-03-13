from pydantic import BaseModel


class UsageSummaryResponse(BaseModel):
    userId: str
    totalTokens: int
    usedTokens: int

