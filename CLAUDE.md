# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start the FastAPI server
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Using the provided script
./run.sh
```

### Docker Operations
```bash
# Build and run using Docker
./scripts/docker.build.sh
docker run -p 8000:8000 your-image-name
```

### Dependencies
```bash
# Install dependencies
pip install -r requirements.txt

# For Docker builds, uses uv for faster package installation
```

## Architecture Overview

### Core Components

**Main Application Structure:**
- `main.py` - FastAPI application entry point
- `app/router.py` - API endpoints and request handling
- `config.py` - Configuration management with environment variables

**AI Agent System:**
- `app/agents/animation_agent.py` - LangChain agent for animation creation
- `app/agents/code_generation_agent.py` - Code generation agent
- `app/tools/manim_tool.py` - Manim integration tool
- `app/tools/code_executor.py` - Code execution utilities

**Data Models:**
- `app/models.py` - Pydantic models for API responses
- `app/config.py` - Configuration settings

### Key Features

1. **AI-Powered Animation Generation**: Uses LangChain agents with OpenAI models to generate Manim code from natural language prompts
2. **Manim Integration**: Renders mathematical animations using the Manim library
3. **File Management**: Automatic cleanup of generated files after download
4. **Docker Support**: Containerized deployment with optimized Python environment

### API Endpoints

- `POST /create-animation` - Generate animation from text prompt
- `GET /download-animation/{animation_id}` - Download generated animation
- `GET /list-animations` - List all animations
- `DELETE /delete-animation/{animation_id}` - Delete specific animation
- `GET /health` - Health check endpoint

### Environment Configuration

Required environment variables:
- `OPENAI_API_KEY` - OpenAI API key for AI agent functionality
- `HOST`, `PORT` - Server configuration
- `ANIMATIONS_DIR` - Directory for storing generated animations
- `MANIM_QUALITY` - Animation rendering quality (low_quality, medium_quality, high_quality)

### File Organization

Generated files are stored in:
- `animations/` - Rendered MP4 files
- `code_files/` - Generated Python/Manim code
- `media/` - Manim media cache (images, videos, texts)

### Agent Flow

1. User submits animation prompt via POST request
2. LangChain agent processes prompt using OpenAI models
3. Agent generates Manim code using the manim_tool
4. Code is executed to render animation
5. Response includes animation_id and download URL
6. Files are cleaned up after download

### Development Notes

- The application uses FastAPI with async endpoints
- LangChain agents handle the AI-powered code generation
- Manim renders animations in configurable quality levels
- Docker setup uses Python 3.12 slim with optimized dependencies
- Uses loguru for logging throughout the application