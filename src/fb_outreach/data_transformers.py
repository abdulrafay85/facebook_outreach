"""
Data transformation utilities for the outreach pipeline.
"""

from typing import Dict, Any, Optional, Tuple
from fb_outreach.schemas import ProspectContext, ApifyFacebookPageData, FacebookAdData


def transform_to_prospect_context(
    page: ApifyFacebookPageData,
    ad: Optional[FacebookAdData] = None,
    fallback_email: Optional[str] = None
) -> ProspectContext:

    email = page.email or fallback_email or ""

    return ProspectContext(
        page_name=page.page_name or page.title or "Unknown",
        email=email,
        category=page.category or "",
        business_description=page.intro or "",
        intro=page.intro or "",
        followers=page.followers,
        likes=page.likes,
        website=page.websites[0] if page.websites else "",
        address=page.address or "",
        phone=page.phone or "",
        ad_creative_text=ad.creative_bodies[0] if ad and ad.creative_bodies else "",
        ad_title=ad.link_titles[0] if ad and ad.link_titles else "",
        ad_url=ad.link_captions[0] if ad and ad.link_captions else "",
        ad_snapshot_url=ad.ad_snapshot_url if ad else "",
        page_id=page.page_id,
        page_url=page.page_url,
        creation_date=page.creation_date or "",
        raw_data={
            "page": page.raw_data,
            "ad": ad.raw_data if ad else {}
        }
    )
