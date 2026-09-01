from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import UserRegisterSchema, UserLoginSchema, TokenResponseSchema, UserResponseSchema
from app.database import get_database
from app.utils.crypto import hash_password, verify_password, hash_sha256
from app.utils.security import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponseSchema)
async def register(user_in: UserRegisterSchema):
    db = get_database()
    
    existing_user = await db.users.find_one({"email": user_in.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
        
    role = "admin" if user_in.is_admin else "user"
    
    # Store PII (Name, Phone) encrypted as SHA-256 hashes
    name_sha256 = hash_sha256(user_in.name)
    mobile_sha256 = hash_sha256(user_in.mobile_number)
    
    user_doc = {
        "email": user_in.email,
        "password_hash": hash_password(user_in.password),
        "name_sha256": name_sha256,
        "mobile_sha256": mobile_sha256,
        "role": role
    }
    
    result = await db.users.insert_one(user_doc)
    
    return UserResponseSchema(
        id=str(result.inserted_id),
        email=user_in.email,
        name_sha256=name_sha256,
        mobile_sha256=mobile_sha256,
        role=role
    )

@router.post("/login", response_model=TokenResponseSchema)
async def login(credentials: UserLoginSchema):
    db = get_database()
    user = await db.users.find_one({"email": credentials.email})
    
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(data={"sub": user["email"], "role": user["role"]})
    return TokenResponseSchema(access_token=access_token, token_type="bearer")