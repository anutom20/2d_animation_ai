from pydantic import BaseModel
from typing import Optional


class AnimationResponse(BaseModel):
    """Response model for animation creation"""

    animation_id: str
    status: str
    message: str
    download_url: Optional[str] = None


class AnimationStatusResponse(BaseModel):
    """Response model for animation status polling"""

    animation_id: str
    status: str  # pending, processing, completed, failed
    message: str
    download_url: Optional[str] = None
    error_details: Optional[str] = None
    progress: Optional[str] = None
