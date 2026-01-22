import os
import requests
from typing import Any, Dict, Optional
from apify_client import ApifyClientAsync
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.apify.com/v2/datasets"
HEADERS = {"Accept": "application/json"}

class ApifyService:
    """
    Service to handle Apify interactions:
    - Client creation
    - Facebook page scraping
    - Dataset fetching
    """

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token
        if not self.api_token:
            raise RuntimeError("APIFY_API_KEY is missing")
        self._client: Optional[ApifyClientAsync] = None

    @property
    def client(self) -> ApifyClientAsync:
        """Lazy-load ApifyClientAsync instance."""
        if not self._client:
            self._client = ApifyClientAsync(self.api_token)
        return self._client

    # ----------------- Facebook Page Scraper -----------------
    async def scrape_facebook_page(self, page_id: str) -> Dict[str, Any]:
        """
        Calls Apify Facebook Pages Scraper actor for a given page_id.
        Returns the scraped data as a dictionary.
        """
        actor = self.client.actor("apify/facebook-pages-scraper")
        run_input = {
            "startUrls": [{"url": f"https://www.facebook.com/{page_id}"}]
        }

        try:
            result = await actor.call(run_input=run_input)
            return result
        except Exception as e:
            raise RuntimeError(f"Failed to scrape page {page_id}: {e}")

    # ----------------- Dataset Fetching -----------------
    async def fetch_dataset(self, dataset_id: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        Fetches all items from an Apify dataset.
        Returns JSON data or None on failure.
        """
        dataset_url = f"{BASE_URL}/{dataset_id}/items"
        params = {"token": self.api_token}

        try:
            response = requests.get(dataset_url, params=params, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            print(f"[ApifyService] Request to dataset {dataset_id} timed out")
        except requests.exceptions.HTTPError as e:
            print(f"[ApifyService] HTTP error ({e.response.status_code}) for dataset {dataset_id}")
        except requests.exceptions.RequestException as e:
            print(f"[ApifyService] Request failed for dataset {dataset_id}: {e}")

        return None
