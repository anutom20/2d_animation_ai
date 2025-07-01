import tempfile
from pathlib import Path
import uuid
import shutil
import subprocess
import json
from typing import Dict, Any, Optional
from loguru import logger
from langchain.tools import Tool
import config
from app.models import AnimationResponse
from app.tools.code_generator import validate_manim_code, extract_scene_class


class CodeExecutionError(Exception):
    """Custom exception for code execution errors"""

    pass


def execute_manim_code(code: str) -> Dict[str, Any]:
    """
    Execute the generated Manim code safely and return the animation details.
    """
    # First validate the code
    errors = validate_manim_code(code)
    if errors:
        raise CodeExecutionError(f"Code validation failed: {', '.join(errors)}")

    try:
        # Create a temporary directory for the code
        with tempfile.TemporaryDirectory() as temp_dir:
            media_dir = Path("media")
            code_dir = Path("code_files")

            # Generate unique filename
            animation_id = str(uuid.uuid4())
            code_file = code_dir / f"animation_{animation_id}.py"

            # Write the code to a file
            code_file.write_text(code)

            # Get the scene class name
            scene_class = extract_scene_class(code)
            if not scene_class:
                raise CodeExecutionError("Could not find Scene class in the code")

            # Run manim command with resource limits
            cmd = [
                "manim",
                "-ql",  # Quality: -l for low, -m for medium, -h for high
                "--media_dir",
                str(media_dir),
                str(code_file),
                scene_class,
            ]

            # Execute with timeout and resource limits
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,  # 30 seconds timeout
                )

                logger.debug(f"Manim execution result: {result.stdout}")

                if result.returncode != 0:
                    raise CodeExecutionError(f"Manim execution failed: {result.stderr}")

                # Find the output file
                media_dir = media_dir / f"videos/animation_{animation_id}"

                logger.debug(f"Media directory: {media_dir}")
                video_files = list(media_dir.glob("*/*.mp4"))

                logger.warning(f"Video files: {video_files}")

                if not video_files:
                    raise CodeExecutionError("No output video file found")

                video_file = video_files[0]

                # Copy to animations directory
                output_path = config.ANIMATIONS_DIR / f"animation_{animation_id}.mp4"
                shutil.copy2(src=video_file, dst=output_path)

                # Create response
                response = AnimationResponse(
                    animation_id=animation_id,
                    status="success",
                    message="Animation created successfully from generated code!",
                    file_path=str(output_path),
                    download_url=f"/download-animation/{animation_id}",
                )

                return response.model_dump()

            except subprocess.TimeoutExpired:
                raise CodeExecutionError("Animation generation timed out")
            except subprocess.CalledProcessError as e:
                raise CodeExecutionError(f"Process error: {e.stderr}")

    except Exception as e:
        raise CodeExecutionError(f"Failed to execute code: {str(e)}")


def get_code_execution_tool() -> Tool:
    """
    Create a LangChain tool for executing Manim code.
    """
    return Tool(
        name="execute_manim_code",
        func=execute_manim_code,
        description="""Execute Manim code and generate an animation.
        Input should be valid Manim Python code as a string.
        The code must:
        - Define a Scene class
        - Have a construct method
        - Use only allowed Manim imports and methods
        - Complete within 30 seconds
        
        Returns a JSON response with animation details including:
        {"animation_id": unique identifier,
        "status": success/error,
        "message": description of the result,
        "file_path": path to the generated file,
        "download_url": URL to download the animation}
        
        return only json response and nothing else.
        """,
    )
