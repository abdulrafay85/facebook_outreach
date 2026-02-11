
from fastapi import Request, HTTPException, Depends
import bcrypt

# Monkeypatch bcrypt to work with passlib 1.7.4
try:
    bcrypt.__about__
except AttributeError:
    class About:
        __version__ = bcrypt.__version__
    bcrypt.__about__ = About()

# Patch bcrypt.hashpw and checkpw to truncate password to 72 bytes
# distinct behavior in bcrypt > 4.0.0 causes passlib to crash
_orig_hashpw = bcrypt.hashpw
def _patched_hashpw(password, salt):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)
bcrypt.hashpw = _patched_hashpw

_orig_checkpw = bcrypt.checkpw
def _patched_checkpw(password, hashed_password):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _orig_checkpw(password, hashed_password)
bcrypt.checkpw = _patched_checkpw

from passlib.context import CryptContext
import uuid
import time
import base64
import json

# Create a password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Takes plain password and returns hashed password
    """
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password too long (max 72 characters)")
    return pwd_context.hash(password)   

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if plain_password matches hashed_password
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_manual_token(user_id: str, expires_seconds: int = 3600) -> str:
    """
    Creates a simple token containing user_id and expiry timestamp
    """
    payload = {
        "user_id": user_id,
        "iat": int(time.time()),  # issued at
        "exp": int(time.time()) + expires_seconds  # expiry timestamp
    }
    # convert payload to JSON string
    payload_str = json.dumps(payload)
    
    # encode to base64 to make it string-safe
    token = base64.urlsafe_b64encode(payload_str.encode()).decode()
    return token

def verify_manual_token(token: str) -> dict:
    """
    Verifies the manual token and returns the payload if valid
    """
    try:
        # decode from base64
        payload_str = base64.urlsafe_b64decode(token.encode()).decode()
        payload = json.loads(payload_str)
        
        # check expiry
        if payload["exp"] < int(time.time()):
            raise ValueError("Token expired")
        
        return payload
    except Exception as e:
        raise ValueError(f"Invalid token: {e}")



# --------------------------------------------

# Step 1: Cookie se token read karna
def get_current_user(request: Request):
    token = request.cookies.get("access_token")

    if not token:a
        raise HTTPException(status_code=401, detail="Not authenticated")

    return token

# Step 2: Token verify karna
def verify_token(token: str):
    try:
        payload = verify_manual_token(token)  # tumhara logic
        user_id = payload.get("user_id")

        if not user_id:
            raise Exception()

        return user_id

    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
