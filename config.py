import os
from pathlib import Path


# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

# Application Configuration
APP_TITLE = os.getenv("APP_TITLE", "2D Animation AI")
APP_DESCRIPTION = os.getenv(
    "APP_DESCRIPTION", "FastAPI application with Manim integration"
)
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# Animation Configuration
ANIMATIONS_DIR = Path(os.getenv("ANIMATIONS_DIR", "animations"))
DEFAULT_ANIMATION_TEXT = os.getenv("DEFAULT_ANIMATION_TEXT", "Hello Manim!")
DEFAULT_ANIMATION_COLOR = os.getenv("DEFAULT_ANIMATION_COLOR", "BLUE")

# Manim Configuration
MANIM_QUALITY = os.getenv(
    "MANIM_QUALITY", "low_quality"
)  # low_quality, medium_quality, high_quality
MANIM_PREVIEW = os.getenv("MANIM_PREVIEW", "False").lower() in ("true", "1", "yes")

# File Management
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "100"))
CLEANUP_TEMP_FILES = os.getenv("CLEANUP_TEMP_FILES", "True").lower() in (
    "true",
    "1",
    "yes",
)

# Create necessary directories
ANIMATIONS_DIR.mkdir(exist_ok=True)
