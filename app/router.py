from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import config
from loguru import logger
import os
from app.agents.code_generation_agent import create_code_generation_agent
from typing import Optional
from langchain.agents import AgentExecutor
from app.config import OPENAI_API_KEY
from app.models import AnimationResponse
import json

# Create router instance
router = APIRouter()


class AnimationRequest(BaseModel):
    prompt: str = (
        "Create a text animation that shows 'Hello World' appearing letter by letter in blue color, then scaling up and fading out"
    )


def get_agent():
    """
    Dependency to get the LangChain agent
    """
    if not OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key not found. Please set OPENAI_API_KEY environment variable.",
        )
    return create_code_generation_agent(openai_api_key=OPENAI_API_KEY)


@router.get("/")
async def root():
    return {"message": "Welcome to 2D Animation AI with FastAPI and Manim!"}


@router.get("/health")
async def health_check():
    return {"status": "healthy", "services": ["FastAPI", "Manim", "LangChain"]}


@router.post("/create-animation", response_model=AnimationResponse)
async def create_animation(
    request: AnimationRequest, agent: AgentExecutor = Depends(get_agent)
):
    """
    Create an animation using AI-generated Manim code
    """
    logger.info(f"Creating animation with request: {request}")
    try:
        # Run the agent
        result = agent.invoke({"input": request.prompt})
        logger.info(f"Result: {result}")

        # Handle case where agent returned invalid JSON
        try:
            if isinstance(result["output"], str):
                result_json = json.loads(result["output"])
            else:
                result_json = result["output"]
        except json.JSONDecodeError:
            logger.error(f"Failed to parse agent output as JSON: {result['output']}")
            return AnimationResponse(
                animation_id="error",
                status="error",
                message="Animation creation failed: Invalid response format",
                download_url="",
            )

        # Return the structured response
        return AnimationResponse(**result_json)

    except Exception as e:
        logger.error(f"Animation creation failed: {str(e)}")
        return AnimationResponse(
            animation_id="error",
            status="error",
            message=f"Animation creation failed: {str(e)}",
            download_url="",
        )


@router.get("/download-animation/{animation_id}")
async def download_animation(animation_id: str):
    """
    Download a generated animation
    """
    file_path = config.ANIMATIONS_DIR / f"animation_{animation_id}.mp4"

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Animation not found"
        )

    return FileResponse(
        path=file_path, media_type="video/mp4", filename=f"animation_{animation_id}.mp4"
    )


@router.get("/list-animations")
async def list_animations():
    """
    List all generated animations
    """
    animations = []
    for file_path in config.ANIMATIONS_DIR.glob("*.mp4"):
        animation_id = file_path.stem.replace("animation_", "")
        animations.append(
            {
                "animation_id": animation_id,
                "filename": file_path.name,
                "size": file_path.stat().st_size,
                "download_url": f"/download-animation/{animation_id}",
            }
        )

    return {"animations": animations}


@router.delete("/delete-animation/{animation_id}")
async def delete_animation(animation_id: str):
    """
    Delete a generated animation
    """
    file_path = config.ANIMATIONS_DIR / f"animation_{animation_id}.mp4"

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Animation not found"
        )

    try:
        file_path.unlink()
        return {"message": f"Animation {animation_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete animation: {str(e)}",
        )
