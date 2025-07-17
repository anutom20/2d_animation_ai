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
from langchain_openai import ChatOpenAI
from app.config import OPENAI_API_KEY
from app.models import AnimationResponse
from langchain_community.callbacks import get_openai_callback
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
        with get_openai_callback() as cb:
            result = agent.invoke({"input": request.prompt})
            logger.info(f"Total tokens: {cb.total_tokens}")
            logger.info(f"Prompt tokens: {cb.prompt_tokens}")
            logger.info(f"Completion tokens: {cb.completion_tokens}")
            logger.info(f"Total cost: {cb.total_cost}")
        logger.info(f"Result: {result}")

        # Handle case where agent returned invalid JSON
        try:
            structured_llm = ChatOpenAI(
                model="o4-mini",
                openai_api_key=OPENAI_API_KEY,
            ).with_structured_output(AnimationResponse)

            response_prompt = f"""
            clean the follwing output and return the clean output in json format:
            download_url = /download-animation/animation_id
            {str(result["output"])}
            """

            response = structured_llm.invoke(response_prompt)
            return AnimationResponse(**response.model_dump())
        except json.JSONDecodeError:
            logger.error(f"Failed to parse agent output as JSON: {result['output']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to parse agent output as JSON",
            )

        # Return the structured response

    except Exception as e:
        logger.error(f"Animation creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Animation creation failed: {str(e)}",
        )


@router.get("/download-animation/{animation_id}")
async def download_animation(animation_id: str):
    """
    Download a generated animation and cleanup files afterward
    """
    animation_file_path = config.ANIMATIONS_DIR / f"animation_{animation_id}.mp4"
    code_file_path = Path("code_files") / f"animation_{animation_id}.py"

    if not animation_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Animation not found"
        )

    # Create a response with the file
    response = FileResponse(
        path=animation_file_path,
        media_type="video/mp4",
        filename=f"animation_{animation_id}.mp4",
    )

    # Delete the animation file after sending
    try:
        # Schedule the files for deletion after the response is sent
        response.background = lambda: cleanup_files(animation_file_path, code_file_path)
    except Exception as e:
        logger.error(
            f"Failed to schedule cleanup for animation {animation_id}: {str(e)}"
        )

    return response


def cleanup_files(animation_path: Path, code_path: Path):
    """Helper function to cleanup animation and code files"""
    try:
        if animation_path.exists():
            animation_path.unlink()
            logger.info(f"Deleted animation file: {animation_path}")

        if code_path.exists():
            code_path.unlink()
            logger.info(f"Deleted code file: {code_path}")
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")


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
