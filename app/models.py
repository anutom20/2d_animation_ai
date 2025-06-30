from pydantic import BaseModel
from typing import Optional


class AnimationResponse(BaseModel):
    """Response model for animation creation"""

    animation_id: str
    status: str
    message: str
    file_path: Optional[str] = None
    download_url: str
