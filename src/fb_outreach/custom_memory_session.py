import enum
import uuid
import asyncio
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, List, Optional, Dict
from fb_outreach.schemas import ApifyFacebookPageData, FacebookAdsResponse, FacebookAdData, FacebookAdsPaging

# -------------------------------------------------------------------------
# Custom Memory Implementation (Provided by User)
# -------------------------------------------------------------------------
@dataclass
class BufferItem:
    data: Any
    user_id: str
    run_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@dataclass
class ShortTermMemory:
    buffer: List[BufferItem] = field(default_factory=list)
    storage_file: str = "memory_store.pkl"

    def __post_init__(self):
        self._load_from_disk()

    def _load_from_disk(self):
        if os.path.exists(self.storage_file):
            try:
                import pickle
                with open(self.storage_file, "rb") as f:
                    self.buffer = pickle.load(f)
                print(f"Loaded {len(self.buffer)} items from {self.storage_file}")
            except Exception as e:
                print(f"Failed to load memory: {e}")

    def _save_to_disk(self):
        try:
            import pickle
            with open(self.storage_file, "wb") as f:
                pickle.dump(self.buffer, f)
            # print(f"Saved {len(self.buffer)} items to {self.storage_file}")
        except Exception as e:
            print(f"Failed to save memory: {e}")

    def add_memory(self, data: Any, *, user_id: str, run_id: str) -> None:
        item = BufferItem(data=data, user_id=user_id, run_id=run_id)
        self.buffer.append(item)
        self._save_to_disk()

    def get_memory(self, user_id: str) -> List[BufferItem]:
        """Return all BufferItems for the given user_id."""
        # Reload to ensure we have latest data from other processes if needed
        self._load_from_disk()
        return [item for item in self.buffer if item.user_id == user_id]

    def persist(self):
        """Force save to disk (useful when modifying mutable objects in place)."""
        self._save_to_disk()

# Global instance   
memory = ShortTermMemory()

# -------------------------------------------------------------------------
# Enums
# -------------------------------------------------------------------------

class PipelineStatus(str, enum.Enum):
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class LogLevel(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    DEBUG = "DEBUG"

# -------------------------------------------------------------------------
# Data Models (In-Memory Dataclasses)
# -------------------------------------------------------------------------

@dataclass
class PipelineSessionModel:
    """Tracks a single execution run of the pipeline."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = PipelineStatus.STARTED
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    total_processed: int = 0
    success_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    error_details: Optional[str] = None

@dataclass
class FacebookAdModel:
    """Stores raw ad data."""
    session_id: str
    ad_id: Optional[str] = None
    page_id: Optional[str] = None
    raw_data: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class FacebookPageModel:
    """Stores detailed page info scraped via Apify."""
    session_id: str
    page_id: str
    page_name: Optional[str] = None
    email: Optional[str] = None
    likes: int = 0
    followers: int = 0
    raw_data: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PitchModel:
    """Stores the generated pitch for a specific page."""
    session_id: str
    page_id: str
    pitch_content: str
    email: Optional[str] = None
    status: str = "generated"
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class PipelineLogModel:
    """Structured logs for every step in the pipeline."""
    session_id: str
    step_name: str
    status: str
    message: Optional[str] = None
    details: Optional[Dict] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

# -------------------------------------------------------------------------
# Session & Logging Service (Using Custom Memory)
# -------------------------------------------------------------------------

class PipelineContext:
    """
    Manages the lifecycle of a pipeline execution (Session)
    and provides methods to log progress and save data using ShortTermMemory.
    """
    DEFAULT_USER_ID = "default_user"

    def __init__(self, user_id: str = DEFAULT_USER_ID):
        self.session_id: str = str(uuid.uuid4())
        self.user_id: str = user_id
        self._session_model: Optional[PipelineSessionModel] = None

    async def __aenter__(self):
        # Create the session model
        self._session_model = PipelineSessionModel(
            id=self.session_id,
            status=PipelineStatus.STARTED,
            start_time=datetime.utcnow()
        )
        
        # Add session object to memory
        # Note: Since it's in-memory, we can mutate this object later and it stays updated in the reference held by BufferItem
        memory.add_memory(
            data=self._session_model,
            user_id=self.user_id,
            run_id=self.session_id
        )
        
        # Log start
        await self.log_step("pipeline_init", "started", "Pipeline session started")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.utcnow()
        
        if exc_type:
            status = PipelineStatus.FAILED
            error_msg = str(exc_val)
            await self.log_step("pipeline_error", "failed", f"Unhandled error: {error_msg}")
        else:
            status = PipelineStatus.COMPLETED
            error_msg = None
            await self.log_step("pipeline_complete", "success", "Pipeline finished successfully")

        # Update Session Record (Mutation works because it's shared memory)
        if self._session_model:
            self._session_model.end_time = end_time
            self._session_model.status = status
            if error_msg:
                self._session_model.error_details = error_msg
        
        # PERSIST CHANGES TO DISK
        memory.persist()

    # --- Logging Methods ---

    async def log_step(self, step_name: str, status: str, message: str = "", details: Dict = None):
        """Logs a specific step execution to memory."""
        print(f"[{datetime.now()}] [{self.session_id}] [{step_name}] {status.upper()}: {message}")
        
        log_entry = PipelineLogModel(
            session_id=self.session_id,
            step_name=step_name,
            status=status,
            message=message,
            details=details
        )
        
        memory.add_memory(
            data=log_entry,
            user_id=self.user_id,
            run_id=self.session_id
        )

    # --- Data Saving Methods ---
    async def save_ad(self, ad_data: Dict):
        
        # print(f"ad_data_type: {type(ad_data)} ad_data: {ad_data}")
        # ads_data = ad_data.get("data", [{}])
        print(f"ads_data_type: {type(ad_data)} :::: ads_data: {ad_data}")
        # for data in ad_data:
        #     print(f"data_type: {type(data)} data: {data}")
        ad_record = FacebookAdsResponse(
                ads = [FacebookAdData(
                    session_id=self.session_id,
                    ad_id=ad_data.get("id"),
                    page_id=ad_data.get("page_id"),
                    page_name=ad_data.get("page_name"),
                    creative_bodies=[ad_data.get("ad_creative_bodies")],
                    link_titles=[ad_data.get("ad_creative_link_titles")],
                    link_descriptions=[ad_data.get("ad_creative_link_descriptions")],
                    link_captions=[ad_data.get("ad_creative_link_captions")],
                    ad_snapshot_url=ad_data.get("ad_snapshot_url"),
                    raw_data=ad_data
                )],
                paging=FacebookAdsPaging(
                    after_cursor=ad_data.get("cursor_after"),
                    next_url=ad_data.get("next_url")
                )
            ) 
        print(f"ad_record: {ad_record}")
        memory.add_memory(
            data=ad_record,
            user_id=self.user_id,
            run_id=self.session_id
        )

    async def save_page(self, page_data: Any):
        """Saves scraped page data (accepts single dict or list of dicts)."""

        # Normalize input
        if isinstance(page_data, dict):
            page_items = [page_data]
        elif isinstance(page_data, list):
            page_items = page_data
        else:
            raise TypeError(f"Invalid page_data type: {type(page_data)}")

        for item in page_items:
            rating_raw = item.get("rating")

            rating_text = None
            rating_overall = None
            rating_count = 0

            if isinstance(rating_raw, dict):
                rating_overall = rating_raw.get("overall")
                rating_count = rating_raw.get("count", 0)
                rating_text = rating_raw.get("text")

            elif isinstance(rating_raw, str):
                rating_text = rating_raw

            contact_data = item.get("contact", {}) or {}
            media_data = item.get("media", {}) or {}
            ads_data = item.get("pageAdLibrary", {}) or {}

            page = ApifyFacebookPageData(
                page_id=item.get("pageId"),
                facebook_id=item.get("facebookId"),
                page_name=item.get("pageName"),
                title=item.get("title"),

                facebook_url=item.get("facebookUrl"),
                page_url=item.get("pageUrl"),
                profile_picture_url=media_data.get("profilePictureUrl") or item.get("profilePictureUrl"),
                cover_photo_url=media_data.get("coverPhotoUrl") or item.get("coverPhotoUrl"),

                email=contact_data.get("email"),
                phone=contact_data.get("phone"),
                address=contact_data.get("address"),
                address_url=contact_data.get("addressUrl"),
                websites=item.get("websites", []),

                likes=item.get("likes", 0),
                followers=item.get("followers", 0),
                followings=item.get("followings", 0),

                category=item.get("category"),
                categories=item.get("categories", []),
                intro=item.get("intro"),
                info=item.get("info", []),
                creation_date=item.get("creation_date") or item.get("creationDate"),

                rating=rating_text,
                rating_overall=rating_overall,
                rating_count=rating_count,
                ratings=rating_text,

                ad_status=item.get("ad_status"),
                is_business_page_active=ads_data.get("is_business_page_active"),

                raw_data=item
            )

            memory.add_memory(
                data=page,
                user_id=self.user_id,
                run_id=self.session_id
            )

    async def save_pitch(self, page_id: str, email: str, content: str):
        """Saves the generated pitch."""    
        pitch_record = PitchModel(
            session_id=self.session_id,
            page_id=page_id,
            email=email,
            pitch_content=content,
            status="generated"
        )
        memory.add_memory(
            data=pitch_record,
            user_id=self.user_id,
            run_id=self.session_id
        )


# # --- Test/Verification Block ---
# if __name__ == "__main__":
#     async def test_run():
#         print("Running test for custom_memory_session.py...")
        
#         # Use a specific user_id for test
#         test_user = "test_user_123"
        
#         async with PipelineContext(user_id=test_user) as ctx:
#             print(f"Session Created: {ctx.session_id}")

#             # 1. Test Log
#             await ctx.log_step("test_step", "started", "Testing logging...")
            
#             # 2. Test Save Ad
#             mock_ad = {"id": "ad_123", "page_id": "page_456", "title": "Test Ad"}
#             await ctx.save_ad(mock_ad)
            
#             # 3. Test Save Page
#             mock_page = {"pageId": "page_456", "pageName": "Test Page", "email": "test@example.com"}
#             await ctx.save_page(mock_page)
            
#             # 4. Test Save Pitch
#             await ctx.save_pitch("page_456", "test@example.com", "Hello, this is a generated pitch.")
            
#             await ctx.log_step("test_step", "success", "Test complete")

#         print("\n--- Verifying Memory Contents ---")
#         user_items = memory.get_memory(test_user)
#         print(f"Total items for {test_user}: {len(user_items)}")
#         print(f"User Items: {user_items}")
        
#         for item in user_items:
#             print(f"[{item.timestamp}] Type: {type(item.data).__name__}")
#             if isinstance(item.data, PipelineSessionModel):
#                 print(f"  -> Session Status: {item.data.status}")
        
#     asyncio.run(test_run())
