from typing import Dict, Optional
from datetime import datetime
import threading
from dataclasses import dataclass
from enum import Enum


class AnimationStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AnimationStatusInfo:
    animation_id: str
    status: AnimationStatus
    message: str
    created_at: datetime
    updated_at: datetime
    download_url: Optional[str] = None
    error_details: Optional[str] = None
    progress: Optional[str] = None


class StatusTracker:
    """Thread-safe status tracking for animations"""
    
    def __init__(self):
        self._statuses: Dict[str, AnimationStatusInfo] = {}
        self._lock = threading.Lock()
    
    def create_status(self, animation_id: str, message: str = "Animation request received") -> AnimationStatusInfo:
        """Create a new animation status entry"""
        with self._lock:
            now = datetime.now()
            status_info = AnimationStatusInfo(
                animation_id=animation_id,
                status=AnimationStatus.PENDING,
                message=message,
                created_at=now,
                updated_at=now
            )
            self._statuses[animation_id] = status_info
            return status_info
    
    def update_status(
        self, 
        animation_id: str, 
        status: AnimationStatus, 
        message: str,
        download_url: Optional[str] = None,
        error_details: Optional[str] = None,
        progress: Optional[str] = None
    ) -> Optional[AnimationStatusInfo]:
        """Update animation status"""
        with self._lock:
            if animation_id in self._statuses:
                status_info = self._statuses[animation_id]
                status_info.status = status
                status_info.message = message
                status_info.updated_at = datetime.now()
                if download_url:
                    status_info.download_url = download_url
                if error_details:
                    status_info.error_details = error_details
                if progress:
                    status_info.progress = progress
                return status_info
            return None
    
    def get_status(self, animation_id: str) -> Optional[AnimationStatusInfo]:
        """Get current status of an animation"""
        with self._lock:
            return self._statuses.get(animation_id)
    
    def remove_status(self, animation_id: str) -> None:
        """Remove status entry (for cleanup)"""
        with self._lock:
            if animation_id in self._statuses:
                del self._statuses[animation_id]
    
    def get_all_statuses(self) -> Dict[str, AnimationStatusInfo]:
        """Get all current statuses"""
        with self._lock:
            return self._statuses.copy()


# Global instance
status_tracker = StatusTracker()