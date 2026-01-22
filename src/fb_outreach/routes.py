from fastapi import APIRouter, HTTPException
from custom_memory_session import memory
from typing import List, Annotated
from facebook_ads_service import FacebookAdsService
from apify_service import ApifyService
from fastapi import Query
from schemas import AdsRequest, AdsResponse, Paging
from dotenv import load_dotenv
from schemas import (
    ApifyFacebookPageData,
    FacebookAdsResponse,
    FacebookAdData,
)
import os
from custom_memory_session import memory, PipelineContext
from outreach_pipeline import pipeline_run

load_dotenv()

router = APIRouter()

# # --------------------------------------
# # ## signup endpoint
# @router.post("/signup")
# async def signup(user: UserSignup):
#     # Check if email already exists
#     for user_item in memory.buffer:
#         print(user_item.data)
#         if user_item.data.get("email") == user.email:
#             raise HTTPException(status_code=400, detail="Email already registered")
    
#     # Hash password & create user
#     hashed_password = hash_password(user.password)
#     user_id = str(uuid.uuid4())
#     memory.add_memory(data={"email": user.email, "password": hashed_password}, user_id=user_id, run_id="run_1")

#     print("User created successfully")
#     return {"message": "User created successfully"}

# # Login endpoint 
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


@router.get("/ads")
async def get_ads(user_id: str = "test_user_123"):
    """
    Fetch all ads stored in ShortTermMemory for a user
    """
    print(f"user_id: {user_id}")
    items = memory.get_memory(user_id)
    print(f"items: {items}")
    ads = []
    for item in items:
        data = item.data
        print(f"data: {data}")
        if isinstance(data, FacebookAdsResponse):
            ads.append(data)
    return ads

@router.post("/fetch")
async def fetch_facebook_ads(payload: AdsRequest):
    print(f"payload: {payload}")
    try:
        async with PipelineContext(user_id=payload.user_id) as ctx:
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
            
            # print(result.get("data"))
    
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

            # await ctx.save_ads(result.get("data"))

            await ctx.log_step(
                "ads_saved",
                "success",
                f"Saved {len(result['data'])} ads",
            )

            return {
                "status": "success",
                "message": "Ads fetched and stored successfully",
                "data": result
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# @router.post("/pages/fetch")
# async def fetch_pages(user_id: str):
#     try:
#         async with PipelineContext(user_id=user_id) as ctx:
#             apify_client = ApifyService(
#                 api_token=os.getenv("APIFY_API_KEY"),   
#             )
#             items = memory.get_memory(user_id)
#             page_ids = {ad.page_id for item in items if isinstance(item.data, FacebookAdsResponse) for ad in item.data.ads if ad.page_id}

#             for page_id in page_ids:
#                 try:
#                     run = await apify_client.scrape_facebook_page(page_id)
#                     dataset_id = run["defaultDatasetId"]
#                     apify_items = await apify_client.fetch_dataset(dataset_id)
            
#                     for page_data in apify_items:
#                         await ctx.save_page(page_data)
#                 except Exception as e:
#                     await ctx.log_step("apify_error", "failed", f"Failed for page_id={page_id}", details={"error": str(e)})


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
    

KEYWORDS = [
    "real estate",
    "realtor services",
    "realty marketing",
    "retail",
    "restaurant",
    "beauty salon",
    "digital marketing",
    "saas marketing",
    "ecommerce brands",
    "local business",
    "technology services",
    "fintech startups"
]

@router.get("/keywords/suggest")
async def keywords_suggestion(
    q: Annotated[str | None, Query()] = None
):
    if not q:
        return []

    q = q.lower().strip()

    results = []

    for keyword in KEYWORDS:
        words = keyword.lower().split(" ")

        for word in words:
            if q in word:   # word-level match
                results.append(keyword)
                break

    return results

# @router.get("campaigns/fetch-ad")
# async def fetch_ads(
#     ad_id: str
# ):