from fastapi import APIRouter, Depends
from typing import List
from app.database import get_database
from app.schemas.auth import UserResponseSchema
from app.utils.security import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Controls"])

@router.get("/users", response_model=List[UserResponseSchema])
async def list_all_registered_users(admin_user: dict = Depends(require_admin)):
    """Retrieves all users displaying their encrypted SHA-256 PII fields."""
    db = get_database()
    cursor = db.users.find()
    users = []
    async for user in cursor:
        users.append(UserResponseSchema(
            id=str(user["_id"]),
            email=user["email"],
            name_sha256=user["name_sha256"],
            mobile_sha256=user["mobile_sha256"],
            role=user["role"]
        ))
    return users