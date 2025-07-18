from typing import Optional, Dict, Any
from langchain.tools import Tool
from manim import *
import tempfile
import uuid
from pathlib import Path
import shutil
import config
from loguru import logger
from app.models import AnimationResponse
import json


class SimpleScene(Scene):
    def __init__(self, text=None, color=None, **kwargs):
        self.text_content = text or config.DEFAULT_ANIMATION_TEXT
        self.text_color = color or config.DEFAULT_ANIMATION_COLOR
        super().__init__(**kwargs)

    def construct(self):
        # Create text
        title = Text(self.text_content, color=self.text_color)

        # Add animations
        self.play(Write(title))
        self.play(title.animate.scale(1.5))
        self.play(FadeOut(title))


def create_animation(input_str: str) -> Dict[str, Any]:
    """
    Create a simple animation with Manim
    """
    try:
        # Parse the input dictionary
        input_dict = json.loads(input_str)

        # Get animation_id from input or generate one
        animation_id = input_dict.get("animation_id", str(uuid.uuid4()))
        output_file = f"animation_{animation_id}"

        # Create and render the scene
        scene = SimpleScene(
            text=input_dict.get("text", "Hello World"),
            color=input_dict.get("color", "BLUE"),
        )
        scene.render()

        # Find the output file in default media directory and copy to animations directory
        media_dir = Path("media/videos/1080p60")
        video_file = media_dir / "SimpleScene.mp4"

        logger.info(f"Video file: {video_file}")

        if video_file.exists():
            output_path = config.ANIMATIONS_DIR / f"{output_file}.mp4"
            # Copy to animations directory
            shutil.copy2(video_file, output_path)

            # Create and return a structured response
            response = AnimationResponse(
                animation_id=animation_id,
                status="success",
                message="Animation created successfully!",
                file_path=str(output_path),
                download_url=f"/download-animation/{animation_id}",
            )

            return response.model_dump()

        else:
            logger.error(f"Video file not found: {video_file}")
            raise Exception("Failed to generate animation file")

    except Exception as e:
        raise Exception(f"Animation creation failed: {str(e)}")


def get_manim_tool() -> Tool:
    """
    Create a LangChain tool for Manim animation generation
    """
    return Tool(
        name="create_manim_animation",
        func=create_animation,
        description="""Create a simple animation using Manim.
        Input should be a stringified dictionary with optional 'text', 'color', and 'animation_id' keys.
        Example: '{"text": "Hello World!", "color": "BLUE", "animation_id": "optional_id"}'
        If animation_id is not provided, a new UUID will be generated.
        Returns a structured json response with animation details including:
        {
            "animation_id": unique identifier,
            "status": success/failure,
            "message": description of the result,
            "file_path": path to the generated file,
            "download_url": URL to download the animation
        }
        return only json response and nothing else.
        """,
    )
