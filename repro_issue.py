import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'src'))
import fb_outreach.security  # Apply the monkeypatch

import passlib.context
from passlib.context import CryptContext
import bcrypt

print(f"Bcrypt version: {bcrypt.__version__}")
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    # Test very long password (triggering wrap bug check or similar)
    long_pass = "a" * 255
    hash = pwd_context.hash(long_pass)
    print(f"Hash generated for long password: {hash[:10]}...")
    verify = pwd_context.verify(long_pass, hash)
    print(f"Verification successful: {verify}")
except Exception as e:
    print(f"Caught error: {e}")
    import traceback
    traceback.print_exc()
