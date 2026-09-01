from pydantic import BaseModel, EmailStr, Field

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)
    mobile_number: str = Field(pattern=r"^\+?[1-9]\d{1,14}$")
    is_admin: bool = False

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponseSchema(BaseModel):
    id: str
    email: EmailStr
    name_sha256: str
    mobile_sha256: str
    role: str