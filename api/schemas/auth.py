from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=120)
    password: str = Field(..., min_length=8)
    fleet_name: str = Field(..., min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    fleet_id: str
    fleet_name: str
    role: str = "member"
    onboarding_completed: bool = True


class OnboardingRequest(BaseModel):
    onboarding_completed: bool = True


class InviteInfoResponse(BaseModel):
    fleet_name: str
    email: str


class AcceptInviteRequest(BaseModel):
    token: str = Field(..., min_length=10)
    full_name: str = Field(..., min_length=1, max_length=120)
    new_password: str = Field(..., min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)


class FleetUpdateRequest(BaseModel):
    fleet_name: str = Field(..., min_length=1, max_length=120)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
