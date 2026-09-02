from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# ------------------------------------------------------------------
# Registration Schemas (Two-Stage OTP Workflow)
# ------------------------------------------------------------------

class RegisterInitiateSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: str = Field(..., min_length=2, description="User full name")
    mobile_number: Optional[str] = Field(None, pattern=r"^\+?[1-9]\d{1,14}$", description="E.164 format mobile number")
    is_admin: Optional[bool] = False

class VerifyOTPSchema(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit numeric OTP")


# ------------------------------------------------------------------
# Authentication Schemas (Login & Tokens)
# ------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ------------------------------------------------------------------
# User Response Schemas
# ------------------------------------------------------------------

class UserResponseSchema(BaseModel):
    id: str
    email: EmailStr
    name: str
    mobile_number: Optional[str] = None
    is_admin: bool = False


# ------------------------------------------------------------------
# Backward-Compatibility Aliases for existing imports (e.g., route.py)
# ------------------------------------------------------------------

RegisterRequest = RegisterInitiateSchema
VerifyOTPRequest = VerifyOTPSchema
UserLoginSchema = LoginRequest
TokenResponseSchema = TokenResponse