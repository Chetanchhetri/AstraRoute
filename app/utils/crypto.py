import hashlib
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes password using Argon2id algorithm (OWASP Standard)."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against stored Argon2id hash."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_sha256(data: str) -> str:
    """
    Encrypts/hashes PII data (Name, Phone) using SHA-256 with a system pepper.
    """
    peppered_data = f"{data}{settings.PEPPER_KEY}".encode('utf-8')
    return hashlib.sha256(peppered_data).hexdigest()