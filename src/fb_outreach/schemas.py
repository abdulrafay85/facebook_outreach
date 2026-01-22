from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import date
import uuid

# ----- Pydantic models -----
class Paging(BaseModel):
    next: Optional[str] = None

class AdsResponse(BaseModel):
    id: str
    ad_creative_bodies: Optional[List[str]] = None
    ad_snapshot_url: Optional[str] = None
    page_id: Optional[str] = None
    page_name: Optional[str] = None
    paging: Optional[Paging] = None

class AdsRequest(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="User ID.")
    search_terms: Any = Field(..., description="Keyword(s) to search ads for.")
    ad_reached_countries: Any = Field(..., description="Country code (e.g., US, IN).")
    limit: int = Field(5, description="Number of ads to fetch.")
    since: Optional[date] = Field(None, description="Start date (YYYY-MM-DD).")
    until: Optional[date] = Field(None, description="End date (YYYY-MM-DD).")
    access_token: str | None = Field(None, description="Facebook API access token.")

@dataclass
class ApifyFacebookPageData:
    # Core identifiers
    page_id: str
    facebook_id: Optional[str] = None
    page_name: Optional[str] = None
    title: Optional[str] = None

    # URLs
    facebook_url: Optional[str] = None
    page_url: Optional[str] = None
    profile_picture_url: Optional[str] = None
    cover_photo_url: Optional[str] = None

    # Contact & basic info
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    address_url: Optional[str] = None
    websites: List[str] = field(default_factory=list)

    # Stats
    likes: int = 0
    followers: int = 0
    followings: int = 0

    # Page metadata
    category: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    intro: Optional[str] = None
    info: List[str] = field(default_factory=list)
    creation_date: Optional[str] = None

    # Ratings
    rating: Optional[str] = None
    rating_overall: Optional[str] = None
    rating_count: int = 0
    ratings: Optional[str] = None

    # Ads & business info
    ad_status: Optional[str] = None
    is_business_page_active: Optional[bool] = None

    # Raw fallback (future safety)
    raw_data: Optional[Dict[str, Any]] = None


@dataclass
class FacebookAdData:
    """Represents a single Facebook Ad from Ads Archive API."""

    # Core identifiers
    session_id: str
    ad_id: str
    page_id: Optional[str] = None
    page_name: Optional[str] = None

    # Creative content
    creative_bodies: List[str] = field(default_factory=list)
    link_titles: List[str] = field(default_factory=list)
    link_descriptions: List[str] = field(default_factory=list)
    link_captions: List[str] = field(default_factory=list)

    # URLs
    ad_snapshot_url: Optional[str] = None

    # Raw fallback (safety for future API changes)
    raw_data: Optional[Dict[str, Any]] = None

@dataclass
class FacebookAdsPaging:
    after_cursor: Optional[str] = None
    next_url: Optional[str] = None

@dataclass
class FacebookAdsResponse:
    ads: List[FacebookAdData] = field(default_factory=list)
    paging: Optional[FacebookAdsPaging] = None


"""
Data models for the Facebook outreach pipeline.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


@dataclass
class ProspectContext:
    """
    Complete context for generating personalized outreach pitch.
    
    Combines Facebook page data and ad data to provide full context
    about a prospect for AI-powered pitch generation.
    
    Attributes:
        page_name: Name of the Facebook page/company
        email: Contact email address
        company: Company/owner name
        category: Business category (e.g., "Health & wellness")
        business_description: Detailed business description
        intro: Short introduction/tagline
        followers: Number of Facebook followers
        likes: Number of Facebook likes
        website: Company website URL
        address: Physical address (if available)
        ad_creative_text: Text from the Facebook ad
        ad_title: Title/headline from the ad
        ad_url: URL in the ad
        page_id: Facebook page ID
        raw_data: Complete raw data for reference
    
    Example:
        >>> context = ProspectContext(
        ...     page_name="Healthy Foods Inc",
        ...     email="contact@healthyfoods.com",
        ...     business_description="Organic food delivery",
        ...     followers=5000
        ... )
    """
    
    # ──────────────────────────────────────
    # Required Fields
    # ──────────────────────────────────────
    page_name: str
    email: str
    
    # ──────────────────────────────────────
    # Company Info
    # ──────────────────────────────────────
    company: str = ""
    category: str = ""
    
    # ──────────────────────────────────────
    # Business Details
    # ──────────────────────────────────────
    business_description: str = ""
    intro: str = ""
    
    # ──────────────────────────────────────
    # Social Proof
    # ──────────────────────────────────────
    followers: int = 0
    likes: int = 0
    
    # ──────────────────────────────────────
    # Contact Info
    # ──────────────────────────────────────
    website: str = ""
    address: str = ""
    phone: str = ""
    
    # ──────────────────────────────────────
    # Ad Context (Optional but valuable)
    # ──────────────────────────────────────
    ad_creative_text: str = ""
    ad_title: str = ""
    ad_url: str = ""
    ad_snapshot_url: str = ""
    
    # ──────────────────────────────────────
    # Additional Context
    # ──────────────────────────────────────
    page_id: str = ""
    page_url: str = ""
    creation_date: str = ""
    tags: List[str] = field(default_factory=list)
    
    # ──────────────────────────────────────
    # Metadata
    # ──────────────────────────────────────
    raw_data: Dict[str, Any] = field(default_factory=dict)
    scraped_at: datetime = field(default_factory=datetime.utcnow)
    
    # ──────────────────────────────────────
    # Methods
    # ──────────────────────────────────────
    
    def is_valid_for_outreach(self) -> bool:
        """Check if context has minimum required data for outreach."""
        return (
            bool(self.page_name) and
            bool(self.email) and
            "@" in self.email and
            (bool(self.business_description) or bool(self.intro))
        )
    
    def get_summary(self) -> str:
        """Get human-readable summary of the prospect."""
        return (
            f"{self.page_name} ({self.category}) - "
            f"{self.followers} followers - {self.email}"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (useful for JSON serialization)."""
        return {
            "page_name": self.page_name,
            "email": self.email,
            "company": self.company,
            "category": self.category,
            "business_description": self.business_description,
            "intro": self.intro,
            "followers": self.followers,
            "likes": self.likes,
            "website": self.website,
            "address": self.address,
            "phone": self.phone,
            "ad_creative_text": self.ad_creative_text,
            "ad_title": self.ad_title,
            "ad_url": self.ad_url,
            "page_id": self.page_id,
            "page_url": self.page_url,
            "creation_date": self.creation_date,
            "tags": self.tags,
        }


@dataclass
class PitchResult:
    """
    Result of pitch generation for a prospect.
    
    Attributes:
        prospect_context: Original prospect data
        pitch_content: Generated pitch text
        subject_line: Email subject line
        status: Generation status (success/failed)
        error_message: Error if failed
        generated_at: Timestamp
        metadata: Additional info (tokens used, model, etc.)
    """
    
    prospect_context: ProspectContext
    pitch_content: str = ""
    subject_line: str = ""
    status: str = "pending"  # pending, success, failed
    error_message: str = ""
    generated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_successful(self) -> bool:
        """Check if pitch was generated successfully."""
        return self.status == "success" and bool(self.pitch_content)