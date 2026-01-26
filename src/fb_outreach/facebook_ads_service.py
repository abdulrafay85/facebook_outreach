import os
import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fb_outreach.schemas import AdsRequest, AdsResponse, Paging
from time import sleep
import logging


# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ----- Facebook Ads Service -----
class FacebookAdsService:
    FB_API_BASE = "https://graph.facebook.com/v23.0/ads_archive"

    def __init__(self, access_token: Optional[str] = None):
        self.access_token = access_token
        if not self.access_token:
            raise RuntimeError("Facebook access token is missing")

    def fetch_ads(self, req: AdsRequest, retries: int = 3, backoff: int = 2) -> Optional[Dict[str, Any]]:
        """
        Fetch ads from Facebook Ads Archive API.
        - Retries `retries` times on network errors with exponential backoff.
        """ 

        # Check if search_terms and ad_reached_countries are present
        if not req.search_terms or not req.ad_reached_countries:
            raise HTTPException(
                status_code=400,
                detail="search_terms and ad_reached_countries are required"
            )

        print(f"req.search_terms: {req.search_terms}")
        
        # --- search_terms ---
        if isinstance(req.search_terms, list):
            # list of dicts or list of strings
            search_terms_list = [
                item["value"] if isinstance(item, dict) else item
                for item in req.search_terms
            ]
        elif isinstance(req.search_terms, str):
            # single string
            search_terms_list = [req.search_terms]
        else:
            search_terms_list = []

        print(f"search_terms_list: {search_terms_list}")

        print(f"req.ad_reached_countries: {req.ad_reached_countries}")        
        # --- ad_reached_countries ---
        if isinstance(req.ad_reached_countries, list):
            countries_list = [
                item["value"] if isinstance(item, dict) else item
                for item in req.ad_reached_countries
            ]
        elif isinstance(req.ad_reached_countries, str):
            countries_list = [req.ad_reached_countries]
        else:
            countries_list = []

        print(f"countries_list: {countries_list}")

        params = {
            "search_terms": search_terms_list,
            "ad_active_status": "ACTIVE",
            "ad_reached_countries": countries_list,
            "fields": ",".join([
                "id",
                "ad_creative_bodies",
                "ad_creative_link_titles",
                "ad_creative_link_descriptions",
                "ad_creative_link_captions",
                "ad_snapshot_url",
                "page_id",
                "page_name"
            ]),
            "access_token": self.access_token,
            "limit": req.limit
        }

        print(f"req.since: {req.since}")
        print(f"req.until: {req.until}")
       
        if req.since:
            params["ad_delivery_date_min"] = req.since
        if req.until:
            params["ad_delivery_date_max"] = req.until

        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(self.FB_API_BASE, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Fetched {len(data.get('data', []))} ads for search_terms={req.search_terms}")
                return data
            except requests.exceptions.RequestException as e:
                attempt += 1
                logger.warning(f"Attempt {attempt}/{retries} failed: {e}")
                sleep(backoff ** attempt)  # exponential backoff

        logger.error(f"Failed to fetch ads after {retries} attempts")
        return None