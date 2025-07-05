from pydantic import BaseModel
from typing import Optional


class AnimationResponse(BaseModel):
    """Response model for animation creation"""

    animation_id: str
    status: str
    message: str
    download_url: str
