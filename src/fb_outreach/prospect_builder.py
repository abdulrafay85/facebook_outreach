# fb_outreach/pipeline/prospect_builder.py

from typing import List, Dict
from .custom_memory_session import memory
from .schemas import ApifyFacebookPageData, FacebookAdData, ProspectContext
from .data_transformers import transform_to_prospect_context


def get_pages_and_ads(user_id: str):
    items = memory.get_memory(user_id)

    pages = [
        item.data for item in items
        if isinstance(item.data, ApifyFacebookPageData)
    ]

    ads = [
        item.data for item in items
        if isinstance(item.data, FacebookAdData)
    ]

    return pages, ads


def match_ads_by_page_id(
    ads: List[FacebookAdData]
) -> Dict[str, List[FacebookAdData]]:
    ad_map: Dict[str, List[FacebookAdData]] = {}

    for ad in ads:
        if ad.page_id:  
            print(f"page_id: {ad.page_id}")
            ad_map.setdefault(ad.page_id, []).append(ad)
    print(f"ad_map: {ad_map}")
    return ad_map


def build_prospects(user_id: str) -> List[ProspectContext]:
    pages, ads = get_pages_and_ads(user_id)
    ad_map = match_ads_by_page_id(ads)

    prospects: List[ProspectContext] = []

    for page in pages:
        matched_ads = ad_map.get(page.page_id, [])
        ad = matched_ads[0] if matched_ads else None

        prospect = transform_to_prospect_context(
            page=page,
            ad=ad,
            fallback_email=None
        )

        if prospect.is_valid_for_outreach():
            prospects.append(prospect)

    return prospects
