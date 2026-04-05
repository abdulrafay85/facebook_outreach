from fastapi import Request, HTTPException, status
from fb_outreach.security import verify_token
from fb_outreach.custom_memory_session import memory

### -------------------------

## Step 1
# def get_token(request: Request):
#     token = request.cookies.get("access_token")
#     if not token:
#         raise HTTPException(status_code=401, detail="Login required")
#     return token

## Step 2
# def verify_user_token(token: str = Depends(get_token)):
#     user_id = verify_token(token)
#     return user_id

## Step 3
# def get_authenticated_user(user_id: str = Depends(verify_user_token)):
#     for user_item in memory.buffer:
#         if user_item.user_id == user_id:
#             return user_item
#     raise HTTPException(status_code=401, detail="User not found")

### -------------------------


def get_current_user_id(request: Request) -> str:
    try:

        access_token = request.cookies.get("access_token")
        
        # print(f"access_token {access_token}")

        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token missing",
            )

        user_id = verify_token(access_token)

        return user_id

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

def get_authenticated_user(request: Request):
    token = request.cookies.get("access_token")
    print("token:", token)

    if not token:
        raise HTTPException(status_code=401, detail="Login required")

    user_id = verify_token(token)

    for user_item in memory.buffer:
        print(f"user_item: {user_item}")
        if user_item.user_id == user_id:
            print(f"user_item found: {user_item}")
            return user_item

    raise HTTPException(status_code=401, detail="User not found")


