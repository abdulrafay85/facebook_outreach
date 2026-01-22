# ## Example 1
# # import time
# # from typing import Dict, List
# # from dataclasses import dataclass, field
# # from datetime import datetime
# # from typing import Any, List
# # import asyncio

# # @dataclass
# # class Event:
# #     type: str                 # event type, e.g., "ads_fetched", "pitch_generated"
# #     message: str              # short description of event
# #     data: Any = None          # optional extra info
# #     timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# # # Global list to store events
# # events_log: List[Event] = []

# # # Helper to add an event
# # def log_event(event_type: str, message: str, data: Any = None):
# #     event = Event(type=event_type, message=message, data=data)
# #     events_log.append(event)
# #     print(f"[EVENT] {event.timestamp} | {event.type} | {event.message}")  # optional console output


# # async def pipeline_run() -> Dict:
# #     """
# #     Main pipeline to fetch ads, get page data, and generate pitches.
# #     Returns a summary report.
# #     """
# #     log_event("pipeline_start", "Pipeline execution started")
    
# #     # Configuration
# #     ads_req = AdsRequest(
# #         search_terms="health",
# #         ad_reached_countries="IN",
# #         limit=5,  # Process multiple pages
# #         since="2025-09-26",
# #         until="2025-09-27",
# #         access_token=os.getenv("ACCESS_TOKEN")  # ✅ Secure
# #     )
# #     log_event("ads_request_built", f"AdsRequest built", data=ads_req.dict())
    
# #     # Fetch ads
# #     try:
# #         ads = await fetch_ads(ads_req)
# #     except Exception as e:
# #         log_event("ads_fetch_error", f"Failed to fetch ads: {e}")
# #         return {"status": "error", "message": str(e)}
    
# #     if not ads or 'data' not in ads or not ads['data']:
# #         log_event("ads_fetch_failed", "No ads found")
# #         return {
# #             "status": "completed",
# #             "total_processed": 0,
# #             "message": "No ads found"
# #         }
    
# #     log_event("ads_fetched", f"Fetched {len(ads['data'])} ads")
    
# #     # Process each ad
# #     results = {
# #         "total": len(ads['data']),
# #         "success": 0,
# #         "failed": 0,
# #         "skipped": 0,
# #         "details": []
# #     }
    
# #     for idx, ad in enumerate(ads['data'], 1):
# #         page_id = ad.get("page_id")
        
# #         if not page_id:
# #             log_event("missing_page_id", f"Ad {idx} has no page_id")
# #             results["skipped"] += 1
# #             continue
        
# #         log_event("processing_page", f"[{idx}/{results['total']}] Processing page_id={page_id}")
        
# #         # Rate limiting (important!)
# #         await asyncio.sleep(2)  # non-blocking sleep
        
# #         # Fetch page data
# #         try:
# #             apify_item = await get_page_data_from_apify(
# #                 page_id=str(page_id),
# #                 apify_api_token=APIFY_ACTOR_TOKEN
# #             )
# #         except Exception as e:
# #             log_event("apify_error", f"Apify failed for page_id={page_id}: {e}")
# #             results["failed"] += 1
# #             results["details"].append({
# #                 "page_id": page_id,
# #                 "status": "failed",
# #                 "reason": f"apify_error: {str(e)}"
# #             })
# #             continue
        
# #         if not apify_item:
# #             log_event("apify_no_data", f"No Apify data for page_id={page_id}")
# #             results["skipped"] += 1
# #             continue
        
# #         # Validate required fields
# #         email = apify_item.get("email")
# #         page_name = apify_item.get("pageName")
        
# #         if not email or '@' not in email:
# #             log_event("invalid_email", f"Invalid/missing email for page_id={page_id}")
# #             results["skipped"] += 1
# #             results["details"].append({
# #                 "page_id": page_id,
# #                 "status": "skipped",
# #                 "reason": "invalid_email"
# #             })
# #             continue
        
# #         # Create UserData
# #         try:
# #             user_data = UserData(
# #                 page_name=page_name or "Unknown",
# #                 email=email,
# #                 title=apify_item.get("title"),
# #                 likes=apify_item.get("likes", 0),
# #                 intro=apify_item.get("intro", ""),
# #                 info=apify_item.get("info", []),
# #                 followers=apify_item.get("followers", 0),
# #                 address=apify_item.get("address", "")
# #             )
# #             log_event("user_data_created", f"UserData created for {page_name}")
# #         except Exception as e:
# #             log_event("user_data_error", f"Failed to create UserData: {e}")
# #             results["failed"] += 1
# #             continue
        
# #         # Generate pitch
# #         try:
# #             result = Runner.run_sync(
# #                 starting_agent=pitch_generator,
# #                 input="Generate and send pitch email",
# #                 run_config=config,
# #                 context=user_data
# #             )
            
# #             log_event("pitch_generated", f"Pitch generated for {page_name}", 
# #                      data=result.final_output)
            
# #             results["success"] += 1
# #             results["details"].append({
# #                 "page_id": page_id,
# #                 "page_name": page_name,
# #                 "email": email,
# #                 "status": "success",
# #                 "output": result.final_output
# #             })
            
# #             print(f"✅ [{idx}/{results['total']}] Success: {page_name}")
            
# #         except Exception as e:
# #             log_event("pitch_error", f"Pitch generation failed for {page_name}: {e}")
# #             results["failed"] += 1
# #             results["details"].append({
# #                 "page_id": page_id,
# #                 "status": "failed",
# #                 "reason": f"agent_error: {str(e)}"
# #             })
# #             print(f"❌ [{idx}/{results['total']}] Failed: {page_name} - {e}")
    
# #     # Final summary
# #     log_event("pipeline_complete", "Pipeline execution finished", data=results)
    
# #     print("\n" + "="*50)
# #     print("📊 PIPELINE SUMMARY")
# #     print("="*50)
# #     print(f"Total Pages: {results['total']}")
# #     print(f"✅ Success: {results['success']}")
# #     print(f"❌ Failed: {results['failed']}")
# #     print(f"⏭️  Skipped: {results['skipped']}")
# #     print("="*50)
    
# #     return results


# # # Usage
# # if __name__ == "__main__":
# #     final_report = pipeline_run()
    
# #     # Save report to file (optional)
# #     import json
# #     with open("pipeline_report.json", "w") as f:
# #         json.dump(final_report, f, indent=2)


## Example 2

import asyncio
import os
from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from apify_client import ApifyClientAsync
from dotenv import load_dotenv
import requests

load_dotenv()


# ----- App-level config ----- 
APIFY_API_KEY = os.getenv("APIFY_API_KEY")
if not APIFY_API_KEY:
    raise RuntimeError("APIFY_API_KEY missing")

BASE_URL = "https://api.apify.com/v2/datasets"
HEADERS = {"Accept": "application/json"}

# ----- Event ----- 
@dataclass
class Event:
    """Represents a logged event within the outreach pipeline."""
    type: str  # Category of the event (e.g., 'ads_fetched', 'error')
    message: str  # Descriptive message for the event
    data: Any = None  # Optional payload for additional context
    # Automatically generate a timestamp in YYYY-MM-DD HH:MM:S format
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# Global list to maintain a history of execution events
events_log: List[Event] = []

def log_event(event_type: str, message: str, data: Any = None):
    """
    Creates an Event instance, appends it to the global log, 
    and prints a formatted log entry to the console.
    """
    event = Event(type=event_type, message=message, data=data)
    events_log.append(event)
    print(f"[EVENT] {event.timestamp} | {event.type} | {event.message}")


# ----- Apify Client ----- 
def get_apify_client():
    token = APIFY_API_KEY
    if not token:
        raise RuntimeError("APIFY_API_KEY missing")

    return ApifyClientAsync(token)

# ----- Run Facebook Scraper ----- 
async def run_facebook_page_scraper(client, page_id):
    actor = client.actor("apify/facebook-pages-scraper")
    run_input = {
        "startUrls": [
            {"url": f"https://www.facebook.com/{page_id}"}
        ]
    }
    return await actor.call(run_input=run_input)

# ----- Fetch Dataset ----- 
async def fetch_apify_dataset(dataset_id: str, timeout: int = 10):
    dataset_url =  f"{BASE_URL}/{dataset_id}/items"
    params = {"token": APIFY_API_KEY}  # Apify accepts token as query param
    
    try:
        response = requests.get(
            dataset_url,
            params=params,
            headers=HEADERS,
            timeout=timeout
        )
        response.raise_for_status()
        print(response)
        return response.json()
    except requests.exceptions.Timeout:
        print("Request timeout")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
    return None


# ----- Helper function to process a single ad -----
async def process_ad(idx: int, ad: Dict, results: Dict):
    page_id = ad.get("page_id")
    
    if not page_id:
        log_event("missing_page_id", f"Ad {idx} has no page_id")
        results["skipped"] += 1
        return

    log_event("processing_page", f"[{idx}] Processing page_id={page_id}")

    # Non-blocking delay
    await asyncio.sleep(2)

    # Fetch page data
    try:
        apify_client = get_apify_client()
        apify_item = await run_facebook_page_scraper(apify_client, page_id)
    except Exception as e:
        log_event("apify_error", f"Apify failed for page_id={page_id}: {e}")
        results["failed"] += 1
        results["details"].append({"page_id": page_id, "status": "failed", "reason": f"apify_error: {e}"})
        return

    if not apify_item:
        log_event("apify_no_data", f"No Apify data for page_id={page_id}")
        results["skipped"] += 1
        return

    # Validate email
    email = apify_item.get("email")
    page_name = apify_item.get("pageName")
    if not email or '@' not in email:
        log_event("invalid_email", f"Invalid/missing email for page_id={page_id}")
        results["skipped"] += 1
        results["details"].append({"page_id": page_id, "status": "skipped", "reason": "invalid_email"})
        return

    # Create UserData
    try:
        user_data = UserData(
            page_name=page_name or "Unknown",
            email=email,
            title=apify_item.get("title"),
            likes=apify_item.get("likes", 0),
            intro=apify_item.get("intro", ""),
            info=apify_item.get("info", []),
            followers=apify_item.get("followers", 0),
            address=apify_item.get("address", "")
        )
        log_event("user_data_created", f"UserData created for {page_name}")
    except Exception as e:
        log_event("user_data_error", f"Failed to create UserData: {e}")
        results["failed"] += 1
        return

    # Generate pitch
    try:
        result = Runner.run_sync(
            starting_agent=pitch_generator,
            input="Generate and send pitch email",
            run_config=config,
            context=user_data
        )
        log_event("pitch_generated", f"Pitch generated for {page_name}", data=result.final_output)
        results["success"] += 1
        results["details"].append({
            "page_id": page_id,
            "page_name": page_name,
            "email": email,
            "status": "success",
            "output": result.final_output
        })
        print(f"[{idx}] Success: {page_name}")
    except Exception as e:
        log_event("pitch_error", f"Pitch generation failed for {page_name}: {e}")
        results["failed"] += 1
        results["details"].append({"page_id": page_id, "status": "failed", "reason": f"agent_error: {e}"})
        print(f"[{idx}] Failed: {page_name} - {e}")

# ----- Main pipeline -----
async def pipeline_run() -> Dict:
    log_event("pipeline_start", "Pipeline execution started")

    # Ads request config
    ads_req = AdsRequest(
        search_terms="health",
        ad_reached_countries="IN",
        limit=5,
        since="2025-09-26",
        until="2025-09-27",
        access_token=os.getenv("ACCESS_TOKEN")
    )
    log_event("ads_request_built", "AdsRequest built", data=ads_req.dict())

    # Fetch ads
    try:
        ads = await fetch_ads(ads_req)
    except Exception as e:
        log_event("ads_fetch_error", f"Failed to fetch ads: {e}")
        return {"status": "error", "message": str(e)}

    if not ads or 'data' not in ads or not ads['data']:
        log_event("ads_fetch_failed", "No ads found")
        return {"status": "completed", "total_processed": 0, "message": "No ads found"}

    log_event("ads_fetched", f"Fetched {len(ads['data'])} ads")

    results = {"total": len(ads['data']), "success": 0, "failed": 0, "skipped": 0, "details": []}

    # ----- Run all ads in parallel -----
    tasks = [process_ad(idx+1, ad, results) for idx, ad in enumerate(ads['data'])]
    await asyncio.gather(*tasks)

    # Pipeline complete
    log_event("pipeline_complete", "Pipeline execution finished", data=results)
    print("\n" + "="*50)
    print("PIPELINE SUMMARY")
    print("="*50)
    print(f"Total Pages: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Failed: {results['failed']}")
    print(f"Skipped: {results['skipped']}")
    print("="*50)

    return results

# ----- Usage -----
if __name__ == "__main__":
    import asyncio, json
    final_report = asyncio.run(pipeline_run())
    with open("pipeline_report.json", "w") as f:
        json.dump(final_report, f, indent=2)

