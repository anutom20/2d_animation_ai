from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import config
from loguru import logger
import os
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from app.agents.code_generation_agent import create_code_generation_agent
from typing import Optional
from app.agents.code_generation_agent import AnimationAgentWrapper
from langchain_openai import ChatOpenAI
from app.config import OPENAI_API_KEY
from app.models import AnimationResponse, AnimationStatusResponse
from app.status_tracker import status_tracker, AnimationStatus
from langchain_community.callbacks import get_openai_callback
import json

# Create router instance
router = APIRouter()

# Create a thread pool executor for background tasks
thread_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="animation-worker")


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
    request: AnimationRequest, 
    agent: AnimationAgentWrapper = Depends(get_agent)
):
    """
    Create an animation using AI-generated Manim code (async with background processing)
    """
    # Generate animation ID immediately
    animation_id = str(uuid.uuid4())
    
    logger.info(f"Creating animation {animation_id} with request: {request}")
    
    # Create initial status
    status_tracker.create_status(animation_id, "Animation request received and queued")
    
    # Submit task to thread pool (non-blocking)
    thread_executor.submit(
        process_animation_background,
        animation_id=animation_id,
        prompt=request.prompt,
        agent=agent
    )
    
    logger.info(f"Animation {animation_id} submitted to thread pool")
    
    # Return immediately with animation ID
    return AnimationResponse(
        animation_id=animation_id,
        status="pending",
        message="Animation request received and queued for processing",
        download_url=None
    )


def process_animation_background(
    animation_id: str,
    prompt: str,
    agent: AnimationAgentWrapper
):
    """
    Background task to process animation generation (runs in separate thread)
    """
    thread_name = threading.current_thread().name
    logger.info(f"Starting animation processing in thread: {thread_name} for animation {animation_id}")
    
    try:
        # Update status to processing
        status_tracker.update_status(
            animation_id, 
            AnimationStatus.PROCESSING, 
            "Generating animation code and rendering...",
            progress="Starting AI code generation"
        )
        
        logger.info(f"[{thread_name}] Starting background processing for animation {animation_id}")
        
        # Modify the agent input to include the animation_id
        agent_input = {
            "input": prompt,
            "animation_id": animation_id
        }
        
        # Run the agent with token tracking
        with get_openai_callback() as cb:
            result = agent.invoke(agent_input)
            logger.info(f"[{thread_name}] Animation {animation_id} - Total tokens: {cb.total_tokens}")
            logger.info(f"[{thread_name}] Animation {animation_id} - Total cost: {cb.total_cost}")
        
        logger.info(f"[{thread_name}] Animation {animation_id} - Agent result: {result}")
        
        # Update status to completed
        download_url = f"/download-animation/{animation_id}"
        status_tracker.update_status(
            animation_id,
            AnimationStatus.COMPLETED,
            "Animation generated successfully and ready for download",
            download_url=download_url
        )
        
        logger.info(f"[{thread_name}] Animation {animation_id} completed successfully")
        
    except Exception as e:
        logger.error(f"[{thread_name}] Animation {animation_id} failed: {str(e)}")
        
        # Update status to failed
        status_tracker.update_status(
            animation_id,
            AnimationStatus.FAILED,
            "Animation generation failed",
            error_details=str(e)
        )


@router.get("/animation-status/{animation_id}", response_model=AnimationStatusResponse)
async def get_animation_status(animation_id: str):
    """
    Get the current status of an animation
    """
    status_info = status_tracker.get_status(animation_id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Animation not found"
        )
    
    return AnimationStatusResponse(
        animation_id=status_info.animation_id,
        status=status_info.status.value,
        message=status_info.message,
        download_url=status_info.download_url,
        error_details=status_info.error_details,
        progress=status_info.progress
    )


@router.get("/download-animation/{animation_id}")
async def download_animation(animation_id: str, background_tasks: BackgroundTasks):
    """
    Download a generated animation and cleanup files afterward
    """
    # Check if animation is completed
    status_info = status_tracker.get_status(animation_id)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Animation not found"
        )
    
    if status_info.status != AnimationStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Animation is not ready for download. Current status: {status_info.status.value}"
        )
    
    animation_file_path = config.ANIMATIONS_DIR / f"animation_{animation_id}.mp4"
    code_file_path = Path("code_files") / f"animation_{animation_id}.py"

    if not animation_file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Animation file not found"
        )

    # Schedule cleanup task to run after response is sent
    background_tasks.add_task(
        cleanup_files, 
        animation_file_path, 
        code_file_path, 
        animation_id
    )
    
    logger.info(f"Scheduled cleanup for animation {animation_id}")

    # Create and return the file response
    return FileResponse(
        path=animation_file_path,
        media_type="video/mp4",
        filename=f"animation_{animation_id}.mp4",
    )


def cleanup_files(animation_path: Path, code_path: Path, animation_id: str):
    """Helper function to cleanup animation and code files"""
    try:
        if animation_path.exists():
            animation_path.unlink()
            logger.info(f"Deleted animation file: {animation_path}")

        if code_path.exists():
            code_path.unlink()
            logger.info(f"Deleted code file: {code_path}")
        
        # Remove status tracking entry
        status_tracker.remove_status(animation_id)
        logger.info(f"Removed status tracking for animation {animation_id}")
        
    except Exception as e:
        logger.error(f"Error during file cleanup: {str(e)}")


# Cleanup function for graceful shutdown
def shutdown_thread_pool():
    """Shutdown the thread pool gracefully"""
    logger.info("Shutting down thread pool...")
    thread_executor.shutdown(wait=True, cancel_futures=True)
    logger.info("Thread pool shutdown complete")


# Optional: Add this to your FastAPI app shutdown event
# @app.on_event("shutdown")
# async def shutdown_event():
#     shutdown_thread_pool()


@router.get("/list-animations")
async def list_animations():
    """
    List all animations (both completed and in-progress)
    """
    animations = []
    
    # Get all tracked animations
    all_statuses = status_tracker.get_all_statuses()
    
    for animation_id, status_info in all_statuses.items():
        animation_data = {
            "animation_id": animation_id,
            "status": status_info.status.value,
            "message": status_info.message,
            "created_at": status_info.created_at.isoformat(),
            "updated_at": status_info.updated_at.isoformat(),
        }
        
        # Add download URL if completed
        if status_info.status == AnimationStatus.COMPLETED:
            animation_data["download_url"] = f"/download-animation/{animation_id}"
            
            # Add file size if file exists
            file_path = config.ANIMATIONS_DIR / f"animation_{animation_id}.mp4"
            if file_path.exists():
                animation_data["size"] = file_path.stat().st_size
                animation_data["filename"] = file_path.name
        
        # Add error details if failed
        if status_info.error_details:
            animation_data["error_details"] = status_info.error_details
            
        animations.append(animation_data)

    return {"animations": animations}


@router.delete("/delete-animation/{animation_id}")
async def delete_animation(animation_id: str):
    """
    Delete a generated animation and its tracking status
    """
    # Check if animation exists in tracking
    status_info = status_tracker.get_status(animation_id)
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Animation not found"
        )
    
    try:
        # Delete files if they exist
        animation_file_path = config.ANIMATIONS_DIR / f"animation_{animation_id}.mp4"
        code_file_path = Path("code_files") / f"animation_{animation_id}.py"
        
        if animation_file_path.exists():
            animation_file_path.unlink()
            logger.info(f"Deleted animation file: {animation_file_path}")
        
        if code_file_path.exists():
            code_file_path.unlink()
            logger.info(f"Deleted code file: {code_file_path}")
        
        # Remove status tracking
        status_tracker.remove_status(animation_id)
        
        return {"message": f"Animation {animation_id} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete animation: {str(e)}",
        )
