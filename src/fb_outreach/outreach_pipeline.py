import asyncio
from fb_outreach.agent import pitch_prompt, PitchService, UserData
import os
from typing import Dict, Any
from datetime import datetime
from fb_outreach.facebook_ads_service import FacebookAdsService, AdsRequest
from fb_outreach.apify_service import ApifyService
from fb_outreach.agent import PitchService, pitch_prompt
from dotenv import load_dotenv
from fb_outreach.custom_memory_session import PipelineContext, memory
from fb_outreach.prospect_builder import build_prospects

load_dotenv()

# ------------------------------------------------------------------
# Helper function to process a single ad
# ------------------------------------------------------------------
async def process_ad(idx: int, ad: Dict, results: Dict, ctx: PipelineContext):
    page_id = ad.get("page_id")
    print(f"Processing ad {idx} with page_id={page_id}")
    await ctx.save_ad(ad)
    print("ad saved")
    print(f"ad: {ad}")
    if not page_id:
        await ctx.log_step(
            "missing_page_id",
            "skipped",
            f"Ad {idx} has no page_id",
        )
        results["skipped"] += 1
        return

    await ctx.log_step(
        "processing_page",
        "started",
        f"[{idx}] Processing page_id={page_id}",
    )

    apify_client = ApifyService(api_token=os.getenv("APIFY_API_KEY"))

    await asyncio.sleep(2)

    try:
        run = await apify_client.scrape_facebook_page(page_id)
        print(f"apify_run: {run}")
        dataset_id = run["defaultDatasetId"]
        apify_items = await apify_client.fetch_dataset(dataset_id)
        
        print(f"apify_items: {apify_items}")
        
        for apify_item in apify_items:
            # print(f"apify_item: {apify_item}")
            if not apify_items:
                raise RuntimeError("Dataset empty")

    except Exception as e:
        await ctx.log_step(
            "apify_error",
            "failed",
            f"Apify failed for page_id={page_id}",
            details={"error": str(e)},
        )
        results["failed"] += 1
        return

    if not apify_item:
        await ctx.log_step(
            "apify_no_data",
            "skipped",
            f"No Apify data for page_id={page_id}",
        )
        results["skipped"] += 1
        return
    print(f"Saving page {apify_item}")
    await ctx.save_page(apify_item)
    print(f"Page saved")

    # # -------------------------------
    # # BUILD PROSPECT CONTEXTS
    # # -------------------------------
    # prospects = build_prospects(user_id)

    # await ctx.log_step(
    #     "prospects_built",
    #     "success",
    #     f"Built {len(prospects)} valid prospects"
    # )

    # try:
    #     pitch_service = PitchService(api_key=os.getenv("GEMINI_API_KEY"))
    #     pitch = pitch_service.generate_pitch(
    #         "Generate and send pitch email",

    #     )

    #     await ctx.save_pitch(page_id, email, pitch)

    #     await ctx.log_step(
    #         "pitch_generated",
    #         "success",
    #         f"Pitch generated for {page_name}",
    #     )

    #     results["success"] += 1

    # except Exception as e:
    #     await ctx.log_step(
    #         "pitch_error",
    #         "failed",
    #         f"Pitch generation failed for {page_name}",
    #         details={"error": str(e)},
    #     )
    #     results["failed"] += 1

# ------------------------------------------------------------------
# Main Pipeline
# ------------------------------------------------------------------
async def pipeline_run(user_id: str = "default_user") -> Dict:
    async with PipelineContext(user_id=user_id) as ctx:
        fb_service = FacebookAdsService(
            access_token=os.getenv("FB_ACCESS_TOKEN")
        )

        ads_req = AdsRequest(
            search_terms="health",
            ad_reached_countries="IN",
            limit=5,
            since="2025-09-26",
            until="2025-09-27",
        )

        await ctx.log_step(
            "ads_request_built",
            "started",
            "AdsRequest created",
            details=ads_req.model_dump(),
        )

        try:
            ads = fb_service.fetch_ads(ads_req)
        except Exception as e:
            await ctx.log_step(
                "ads_fetch_error",
                "failed",
                str(e),
            )
            raise

        if not ads or not ads.get("data"):
            await ctx.log_step(
                "ads_fetch_empty",
                "completed",
                "No ads found",
            )
            # return {"total": 0}

        await ctx.log_step(
            "ads_fetched",
            "success",
            f"Fetched {len(ads['data'])} ads",
        )

        results = {
            "total": len(ads["data"]),
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        tasks = [
            process_ad(idx + 1, ad, results, ctx)
            for idx, ad in enumerate(ads["data"])
        ]

        await asyncio.gather(*tasks)

        # memory.save_memory(user_id, ctx)
        
        # --------------------------------
        # BUILD PROSPECT CONTEXTS (ONE TIME)
        # --------------------------------
        print(f"user_id:  {user_id}")

        # items = memory.get_memory(user_id)

        # print(f"stored_data: {items}")

        prospects = build_prospects(user_id)

        print(f"prospects: {prospects}")

        if prospects is None or len(prospects) == 0:
            await ctx.log_step(
                "prospects_built",
                "failed",
                "No prospects found",
            )
            # return {"total": 0}

        await ctx.log_step(
            "prospects_built",
            "success",
            f"Built {len(prospects)} valid prospects"
        )
        
        # --------------------------------
        # GENERATE PITCHES
        # --------------------------------
        print(f"Generating pitches for {len(prospects)} prospects")

        for prospect in prospects:
            try:
                # print(f"Generating pitch for {prospect.page_name}")
                pitch = pitch_service.generate_pitch(
                    user_input="Generate and send pitch email",
                    context=prospect,
                )
                print(f"Pitch: {pitch}")

                await ctx.save_pitch(
                    page_id=prospect.page_id,
                    email=prospect.email,
                    content=pitch
                )

                print(f"Pitch saved for {prospect.page_name}")
                
                await ctx.log_step(
                    "pitch_generated",
                    "success",
                    f"Pitch generated for {prospect.page_name}"
                )

            except Exception as e:
                await ctx.log_step(
                    "pitch_error",
                    "failed",
                    f"Pitch failed for {prospect.page_name}",
                    details={"error": str(e)}
                )

        await ctx.log_step(
            "pipeline_summary",
            "success",
            "Pipeline execution finished",
            details=results,
        )
        print(f"results: {results}")
        return results

# ------------------------------------------------------------------
# Run
# ------------------------------------------------------------------
if __name__ == "__main__":
    import json

    final_report = asyncio.run(pipeline_run(user_id="test_user_123"))
    with open("pipeline_report.json", "w") as f:
        json.dump(final_report, f, indent=2)