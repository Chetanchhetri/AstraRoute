import random
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from app.database import db
from app.schemas.auth import (
    RegisterInitiateSchema, 
    VerifyOTPSchema, 
    LoginRequest, 
    TokenResponse
)
from app.utils.security import hash_password, verify_password, create_access_token
from app.services.email_service import send_otp_email_sync

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register/initiate")
async def initiate_registration(req: RegisterInitiateSchema, background_tasks: BackgroundTasks):
    try:
        users_col = db["users"]
        pending_users_col = db["pending_users"]

        # 1. Check if user already exists
        existing_user = await users_col.find_one({"email": req.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="A user with this email address already exists."
            )

        # 2. Generate 6-Digit OTP & 10-Minute Expiry
        otp_code = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=10)

        pending_user_data = {
            "email": req.email,
            "password_hash": hash_password(req.password),
            "name": req.name,
            "mobile_number": req.mobile_number,
            "is_admin": req.is_admin,
            "otp": otp_code,
            "expires_at": expires_at,
            "updated_at": datetime.utcnow()
        }

        # 3. Store pending user registration in MongoDB
        await pending_users_col.update_one(
            {"email": req.email},
            {"$set": pending_user_data},
            upsert=True
        )

        # 4. Dispatch Email non-blockingly via BackgroundTasks
        background_tasks.add_task(send_otp_email_sync, req.email, otp_code)

        return {
            "status": "success",
            "message": f"Verification OTP sent to {req.email}. Please verify within 10 minutes."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration initiation failed: {str(e)}"
        )


@router.post("/register/verify")
async def verify_otp_and_register(req: VerifyOTPSchema):
    try:
        users_col = db["users"]
        pending_users_col = db["pending_users"]

        # 1. Fetch pending record
        pending = await pending_users_col.find_one({"email": req.email})
        if not pending:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="No pending registration request found for this email."
            )

        # 2. Verify Expiry
        if datetime.utcnow() > pending["expires_at"]:
            await pending_users_col.delete_one({"email": req.email})
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="OTP code has expired. Please initiate registration again."
            )

        # 3. Match OTP
        if pending["otp"] != req.otp.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid OTP code entered."
            )

        # 4. Insert final user document into MongoDB
        final_user_doc = {
            "email": pending["email"],
            "password_hash": pending["password_hash"],
            "name": pending["name"],
            "mobile_number": pending["mobile_number"],
            "is_admin": pending.get("is_admin", False),
            "created_at": datetime.utcnow()
        }

        await users_col.insert_one(final_user_doc)
        
        # 5. Clean up pending user entry
        await pending_users_col.delete_one({"email": req.email})

        return {
            "status": "success",
            "message": "Account successfully verified and created! You can now log in."
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OTP verification failed: {str(e)}"
        )


@router.post("/login", response_model=TokenResponse)
async def login_user(credentials: LoginRequest):
    try:
        users_col = db["users"]
        
        # 1. Check user existence
        user = await users_col.find_one({"email": credentials.email})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # 2. Verify Argon2/Bcrypt hash
        if not verify_password(credentials.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # 3. Create JWT access token
        access_token = create_access_token(
            data={"sub": user["email"], "is_admin": user.get("is_admin", False)}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )