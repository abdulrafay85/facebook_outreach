from fastapi import APIRouter, HTTPException, Depends, Cookie
from fastapi.responses import JSONResponse
from fb_outreach.dependencies import get_current_user_id, get_authenticated_user
from fb_outreach.custom_memory_session import memory, PipelineContext
from typing import List, Annotated
from fb_outreach.facebook_ads_service import FacebookAdsService
from fb_outreach.apify_service import ApifyService
from fastapi import Query
from fb_outreach.schemas import AdsRequest, AdsResponse, Paging
from dotenv import load_dotenv
from fb_outreach.schemas import (
    ApifyFacebookPageData,
    FacebookAdsResponse,
    FacebookAdData,
)
import os
from fb_outreach.outreach_pipeline import pipeline_run

from fastapi import FastAPI, Request, HTTPException, Query, Path, Cookie, Header, Form, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
# from fastapi import Response
from typing import Annotated, Any
# from class_1.mock import fake_products
from fb_outreach.custom_memory_session import memory
from fb_outreach.security import hash_password, verify_password, create_manual_token, verify_manual_token
import uuid
from pydantic import BaseModel

load_dotenv()

router = APIRouter()

## ------------------------------------

# Pydantic models for signup
class UserSignup(BaseModel): 
    email: str
    password: str

# Pydantic models for login
class UserLogin(BaseModel):
    email: str
    password: str

# # 
# @router.get("/auth/me")
# def auth_me(user_id: str = Depends(get_current_user_id)):
#     return {
#         "authenticated": True,
#         "user_id": user_id,
#         # aur agar chaho to aur user info bhi return kar sakte ho
#     }

# --------------------------------------
## signup endpoint
@router.post("/signup")
async def signup(user: UserSignup):
    # Check if email already exists
    for user_item in memory.buffer:
        # print(user_item.data)
        if user_item.data.get("email") == user.email:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password & create user
    hashed_password = hash_password(user.password)
    user_id = str(uuid.uuid4())
    memory.add_memory(data={"email": user.email, "password": hashed_password}, user_id=user_id, run_id="run_1")

    # print("User created successfully")
    return {"message": "User created successfully"}

@router.post("/login")
async def login(user: UserLogin):
    for user_item in memory.buffer:
        if user_item.data.get("email") == user.email:
            if verify_password(user.password, user_item.data.get("password")):
                token = create_manual_token(user_item.user_id)

                response = JSONResponse({"msg": "login success"})

                response.set_cookie(
                key="access_token",
                    value=token,
                    httponly=True,
                    # secure=False,
                    secure=True,
                    # secure=True,
                    samesite="none",
                    max_age=60 * 60 * 24,
                    path="/"
                )
                # print("Logged in successfully")
                return response

            raise HTTPException(status_code=401, detail="Invalid credentials")
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Step 4: Protected route mein use karo
@router.get("/me")
async def me(user = Depends(get_authenticated_user)):
    # print(f"user {user}")
    email = None
    
    if isinstance(user.data, dict):
        email = user.data.get("email")
    else:   
        email = getattr(user.data, "email", None)
    
    return {
        "user_id": user.user_id,
        "email": email
    }
    

# # # Login endpoint 
# @router.post("/login")
# async def login(user: UserLogin):
#     for user_item in memory.buffer:
#         print(user_item.data)
#         if user_item.data.get("email") == user.email:
#             if verify_password(user.password, user_item.data.get("password")):
#                 token = create_manual_token(user_item.user_id)

#                 # # FIXED: Settings for reliable local cookie setting
#                 response.set_cookie(
#                     key="access_token",
#                     value=token,
#                     httponly=True,
#                     # secure=False is required for HTTP (not HTTPS)
#                     secure=False,
#                     # samesite="lax" allows cookies to be sent in top-level navigations 
#                     # and works better with HTTP than "none" (which requires secure=True)
#                     samesite="lax"
#                 )

#                 response = JSONResponse({"msg": "login success"})
#                 response.set_cookie(
#                     key="access_token",
#                     value=token,
#                     httponly=True,
#                     secure=False,
#                     samesite="lax"
#                 )

#                 print("Logged in successfully")
#                 return response

#             raise HTTPException(status_code=401, detail="Invalid credentials")

#     raise HTTPException(status_code=401, detail="Invalid credentials")


# # --------------------------------------
## @router.get("/ads")
## async def get_ads(user_id: str = "test_user_123"):
##     """
##     Fetch all ads stored in ShortTermMemory for a user
##     """
##     print(f"user_id: {user_id}")
##     items = memory.get_memory(user_id)
##     print(f"items: {items}")
##     ads = []
##     for item in items:
##         data = item.data
##         print(f"data: {data}")
##         if isinstance(data, FacebookAdsResponse):
##             ads.append(data)
##     return ads

# ---------------------------------
# version 1
# @router.post("/fetch")
# async def fetch_facebook_ads(payload: AdsRequest, user_id: str = Depends(get_current_user_id)):
#     print(f"user_id: {user_id}")
#     try:
#         async with PipelineContext(user_id=user_id) as ctx:
#             ads_service = FacebookAdsService(
#                 access_token=os.getenv("FB_ACCESS_TOKEN"),
#             )

#             await ctx.log_step(
#                 "ads_request_built",
#                 "started",
#                 "AdsRequest created",
#                 details=payload.model_dump(),
#             )
#             result = ads_service.fetch_ads(payload)

#             print(f"result: {result}")
            
#             print(f"ads_data: {result.get("data")}")
    
#             if not result or not result.get("data"):
#                 await ctx.log_step( 
#                     "ads_fetch_empty",
#                     "completed",
#                     "No ads found",
#                 )
                
#                 raise HTTPException(
#                     status_code=500,
#                     detail="Ads not fetched successfully"
#                 )

#             await ctx.log_step(
#                 "ads_fetched",
#                 "success",
#                 f"Fetched {len(result['data'])} ads",
#             )

#             await ctx.save_ad(result.get("data"))

#             await ctx.log_step(
#                 "ads_saved",
#                 "success",
#                 f"Saved {len(result['data'])} ads",
#             )


#             response = JSONResponse(content={
#                 "status": "success",
#                 "message": "Ads fetched and stored successfully",
#                 "data": result
#             })

#             response.set_cookie(
#                 key="user_id",
#                 value=user_id,
#                 httponly=True,
#                 secure=False,
#                 samesite="lax",
#                 path="/"
#             )

#             return response


#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=str(e)
#         )   



# ---------------------------------
# version 2
@router.post("/fetch")
async def fetch_facebook_ads(payload: AdsRequest, user_id: str = Depends(get_current_user_id)):
    # print(f"user_id: {user_id}")
    try:
        async with PipelineContext(user_id=user_id) as ctx:
            ads_service = FacebookAdsService(
                access_token=os.getenv("FB_ACCESS_TOKEN"),
            )

            await ctx.log_step(
                "ads_request_built",
                "started",
                "AdsRequest created",
                details=payload.model_dump(),
            )
            result = ads_service.fetch_ads(payload)

            # print(f"result: {result}")
            # print(f"type of result: {type(result)}")
            # print(f"ads_data: {result.get('data')}")  # changed double quotes inside to single quotes
    
            if not result or not result.get("data"):
                await ctx.log_step( 
                    "ads_fetch_empty",
                    "completed",
                    "No ads found",
                )
                
                raise HTTPException(
                    status_code=500,
                    detail="Ads not fetched successfully"
                )

            await ctx.log_step(
                "ads_fetched",
                "success",
                f"Fetched {len(result['data'])} ads",
            )

            # Loop through each ad and save separately
            for ad in result.get("data"):
                await ctx.save_ad(ad)

            await ctx.log_step(
                "ads_saved",
                "success",
                f"Saved {len(result['data'])} ads",
            )


            response = JSONResponse(content={
                "status": "success",
                "message": "Ads fetched and stored successfully",
                "data": result
            })

            response.set_cookie(
                key="user_id",
                value=user_id,
                httponly=True,
                secure=False,
                samesite="lax",
                path="/"
            )

            return response


    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )   

# ---------------------------------
# version 1
# ---------------------------------
# @router.get("/pages")
# async def fetch_pages(user_id: str = Depends(get_current_user_id)):
#     pages = []
#     print(f"user_id: {user_id}")
#     user_id = user_id
#     async with PipelineContext(user_id=user_id) as ctx:
#         apify_client = ApifyService(
#             api_token=os.getenv("APIFY_API_KEY"),   
#         )
#         items = memory.get_memory(user_id)
#         print(f"items: {items}")    
#         # page_ids = {ad.page_id for item in items if isinstance(item.data, FacebookAdsResponse) for ad in item.data.ads if ad.page_id}
#         # print(f"page_ids: {page_ids}")

#         page_ids = set()

#         for item in items:
#             data = item.data
#             # Check if this data object has attribute 'ads'
#             if hasattr(data, 'ads') and isinstance(data, FacebookAdsResponse):
#                 print(f"data.ads: {data.ads}")
#                 for ad in data.ads:
#                     # Check if ad has attribute page_id and it is not None
#                     if hasattr(ad, 'page_id') and ad.page_id:
#                         page_ids.add(ad.page_id)

#         print(f"page_ids: {page_ids}")

#         for page_id in page_ids:
#             try:
#                 run = await apify_client.scrape_facebook_page(page_id)
#                 dataset_id = run["defaultDatasetId"]
#                 apify_items = await apify_client.fetch_dataset(dataset_id)
#                 # print(f"apify_items: {apify_items}")
    
#                 for page_data in apify_items:
#                     print(f"page_data: {page_data}")
#                     await ctx.save_page(page_data)
#                     pages.append(page_data)

#             except Exception as e:
#                 await ctx.log_step("apify_error", "failed", f"Failed for page_id={page_id}", details={"error": str(e)})
#         return pages


## version 2
@router.get("/pages")
async def fetch_pages(user_id: str = Depends(get_current_user_id)):
    pages = []
    # print(f"user_id: {user_id}")
    async with PipelineContext(user_id=user_id) as ctx:
        apify_client = ApifyService(api_token=os.getenv("APIFY_API_KEY"))
        items = memory.get_memory(user_id)
        # print(f"items count: {len(items)}")
        
        page_ids = set()

        for item in items:
            data = item.data
            # print(f"_data_: {data}")
            if hasattr(data, 'ads') and isinstance(data, FacebookAdsResponse):
                
                for ad in data.ads:
                    if hasattr(ad, 'page_id') and ad.page_id:
                        page_ids.add(ad.page_id)

        # print(f"Unique page_ids found: {page_ids}")

        for page_id in page_ids:
            try:
                # print(f"Fetching data for page_id: {page_id}")
                run = await apify_client.scrape_facebook_page(page_id)
                dataset_id = run["defaultDatasetId"]
                apify_items = await apify_client.fetch_dataset(dataset_id)
                # print(f"Fetched {len(apify_items)} items for page_id {page_id}")

                for page_data in apify_items:
                    # print(f"Appending page_data for page_id {page_id}")
                    await ctx.save_page(page_data)
                    pages.append(page_data)

            except Exception as e:
                await ctx.log_step("apify_error", "failed", f"Failed for page_id={page_id}", details={"error": str(e)})

        # print(f"Total pages returned: {len(pages)}")
        return pages

# -----------------------------
# @router.post("/pipeline/run")
# async def run_pipeline(req: PipelineRunRequest):
#     """
#     Trigger pipeline execution using form/JSON input
#     """
#     try:
#         result = await pipeline_run(user_id=req.user_id)
#         return PipelineRunResponse(**result)

#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Pipeline execution failed: {str(e)}"
#         )

# ---- Static keyword source (Page Categories + Interests) ----
# KEYWORDS = [
# "real estate",
# "realtor services",
# "realty marketing",
# "retail",
# "restaurant",
# "beauty salon",
# "digital marketing",
# "saas marketing",
# "ecommerce brands",
# "local business"
# ]

# async def keywords_suggestion(q: Annotated[str | None, Query()] = None):
#     """
#     Fetch keywords from memory
#     """
#     q = q.lower()
#     return [keyword for keyword in KEYWORDS if q in keyword]

# KEYWORDS = [
#     "real estate",
#     "realtor services",
#     "realty marketing",
#     "retail",
#     "restaurant",
#     "beauty salon",
#     "digital marketing",
#     "saas marketing",
#     "ecommerce brands",
#     "local business",
#     "technology services",
#     "fintech startups"
# ]

# @router.get("/keywords/suggest")
# async def keywords_suggestion(
#     q: Annotated[str | None, Query()] = None
# ):
#     if not q:
#         return []

#     q = q.lower().strip()

#     results = []

#     for keyword in KEYWORDS:
#         words = keyword.lower().split(" ")

#         for word in words:
#             if q in word:   # word-level match
#                 results.append(keyword)
#                 break
                
#     return results



# @router.get("campaigns/fetch-ad")
# async def fetch_ads(
#     ad_id: str
# ):    

# https://bountiful-upliftment-production-5a3b.up.railway.app/
