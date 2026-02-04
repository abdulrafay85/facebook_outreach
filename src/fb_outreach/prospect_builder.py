# fb_outreach/pipeline/prospect_builder.py

# from typing import List, Dict
# from fb_outreach.custom_memory_session import memory
# from fb_outreach.schemas import ApifyFacebookPageData, FacebookAdData, ProspectContext, FacebookAdsResponse
# from fb_outreach.data_transformers import transform_to_prospect_context


# def get_pages_and_ads(user_id: str):
#     print(f"Getting pages and ads for user_id: {user_id}")
#     items = memory.get_memory(user_id)

#     pages = [
#         item.data for item in items
#         if isinstance(item.data, ApifyFacebookPageData)
#     ]

#     ads = [
#         item.data for item in items
#         if isinstance(item.data, FacebookAdsResponse)
#     ]

#     return {
#         "pages": pages,
#         "ads": ads
#     }


# def match_ads_by_page_id(
#     ads: List[FacebookAdsResponse]
# ) -> Dict[str, List[FacebookAdData]]:

#     print(f"Matching ads by page_id...")
    
#     ad_map: Dict[str, List[FacebookAdsResponse]] = {}

#     for ad in ads:
#         print(f"ad: {ad}")
#         for ad in ad.ads:
#             print(f"ad: {ad}")
#             if ad.page_id:  
#                 print(f"page_id: {ad.page_id}")
#                 ad_map.setdefault(ad.page_id, []).append(ad)
#     print(f"ad_map: {ad_map}")
#     return ad_map

# def build_prospects(user_id: str) -> List[ProspectContext]:
#     print("Building prospects...")
#     data = get_pages_and_ads(user_id)
#     ad_map = match_ads_by_page_id(data["ads"])
#     print(f"pages_: {data['pages']}")
#     print(f"ads: {data['ads']}")
#     print(f"ad_map: {ad_map}")

#     prospects: List[ProspectContext] = []

#     print("-----------------------------")
#     for page in data['pages']:
#         print(f"_page_id_: {page.page_id}")
#         if page.page_id in ad_map:
#             matched_ads = ad_map[page.page_id]
#             print(f"matched_ads: {matched_ads}")
#         else:
#             print(f"No matched ads found for page_id: {page.page_id}")
#         # ad = matched_ads[0] if matched_ads else None

#         # prospect = transform_to_prospect_context(
#         #     page=page,
#         #     ad=ad,
#         #     fallback_email=None
#         # )

#         # if prospect.is_valid_for_outreach():
#         #     prospects.append(prospect)

#     return prospects


# ---------------------------------------------------------

# fb_outreach/pipeline/prospect_builder.py

from typing import List, Dict
from fb_outreach.custom_memory_session import memory
from fb_outreach.schemas import (
    ApifyFacebookPageData,
    FacebookAdData,
    ProspectContext,
    FacebookAdsResponse,
)
from fb_outreach.data_transformers import transform_to_prospect_context


def get_pages_and_ads(user_id: str):
    print(f"Getting pages and ads for user_id: {user_id}")

    items = memory.get_memory(user_id)

    pages: List[ApifyFacebookPageData] = [
        item.data
        for item in items
        if isinstance(item.data, ApifyFacebookPageData)
    ]

    ads: List[FacebookAdsResponse] = [
        item.data
        for item in items
        if isinstance(item.data, FacebookAdsResponse)
    ]

    return {
        "pages": pages,
        "ads": ads,
    }


def match_ads_by_page_id(
    ads: List[FacebookAdsResponse],
) -> Dict[str, List[FacebookAdData]]:
    """
    page_id -> list of FacebookAdData
    """

    print("Matching ads by page_id...")

    ad_map: Dict[str, List[FacebookAdData]] = {}

    for response in ads:
        for ad in response.ads:
            if not ad.page_id:
                continue

            ad_map.setdefault(ad.page_id, []).append(ad)

    print(f"ad_map keys: {ad_map.keys()}")
    return ad_map


def build_prospects(user_id: str) -> List[ProspectContext]:
    print("Building prospects...")

    data = get_pages_and_ads(user_id)
    ad_map = match_ads_by_page_id(data["ads"])

    # deduplicate pages by page_id
    unique_pages: Dict[str, ApifyFacebookPageData] = {
        page.raw_data["pageAdLibrary"]["id"]: page for page in data["pages"]
        if page.raw_data["pageAdLibrary"]["id"]
    }

    print(f"unique_pages: {unique_pages}")

    prospects: List[ProspectContext] = []

    print("-----------------------------")
    for page_id, page in unique_pages.items():
        print(f"Processing page_id: {page_id}")

        matched_ads = ad_map.get(page_id, [])

        if not matched_ads:
            print(f"No ads found for page_id: {page_id}")
            continue

        # ✅ ek page ke multiple ads → multiple prospects
        for ad in matched_ads:
            prospect = transform_to_prospect_context(
                page=page,
                ad=ad,
                fallback_email=None,
            )

            if prospect.is_valid_for_outreach():
                prospects.append(prospect)

    print(f"Total prospects built: {len(prospects)}")
    return prospects
