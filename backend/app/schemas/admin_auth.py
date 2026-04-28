from datetime import datetime

from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=512)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime


class AdminProfileResponse(BaseModel):
    id: int
    email: str
    role: str
    zone: str | None
