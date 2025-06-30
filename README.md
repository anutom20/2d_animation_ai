# 2D Animation AI

A FastAPI application integrated with Manim for creating 2D animations programmatically.

## Features

- FastAPI web framework for creating APIs
- Manim integration for 2D animation generation
- RESTful endpoints for animation creation, listing, and management
- Automatic video file handling and download capabilities

## Setup

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)

### Installation

1. **Clone/Navigate to the project directory:**
   ```bash
   cd 2d_animation_ai
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional):**
   ```bash
   # Copy example environment file
   cp env.example .env
   
   # Edit .env file with your preferred settings
   # All variables have sensible defaults
   ```

## Usage

### Running the Application

1. **Start the FastAPI server:**
   ```bash
   # Activate virtual environment first
   source venv/bin/activate
   
   # Run the application
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the application:**
   - API: http://localhost:8000
   - Interactive API documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### API Endpoints

#### GET `/`
Welcome message

#### GET `/health`
Health check endpoint

#### POST `/create-animation`
Create a new animation with custom text and color.

**Request body:**
```json
{
  "text": "Hello Manim!",
  "color": "BLUE"
}
```

**Response:**
```json
{
  "animation_id": "uuid-string",
  "status": "success",
  "message": "Animation created successfully!",
  "file_path": "path/to/animation.mp4",
  "download_url": "/download-animation/uuid-string"
}
```

#### GET `/download-animation/{animation_id}`
Download a specific animation by ID

#### GET `/list-animations`
List all generated animations

#### DELETE `/delete-animation/{animation_id}`
Delete a specific animation by ID

## Example Usage

### Using curl

1. **Create an animation:**
   ```bash
   curl -X POST "http://localhost:8000/create-animation" \
        -H "Content-Type: application/json" \
        -d '{"text": "Hello World!", "color": "RED"}'
   ```

2. **List animations:**
   ```bash
   curl "http://localhost:8000/list-animations"
   ```

3. **Download animation:**
   ```bash
   curl -O "http://localhost:8000/download-animation/{animation_id}"
   ```

### Using Python

```python
import requests

# Create animation
response = requests.post(
    "http://localhost:8000/create-animation",
    json={"text": "My Animation", "color": "GREEN"}
)
result = response.json()
print(result)

# Download animation
animation_id = result["animation_id"]
download_response = requests.get(f"http://localhost:8000/download-animation/{animation_id}")
with open(f"animation_{animation_id}.mp4", "wb") as f:
    f.write(download_response.content)
```

## Project Structure

```
2d_animation_ai/
├── app/                  # Application package
│   ├── __init__.py      # Package initialization
│   ├── main.py         # FastAPI application instance
│   └── router.py        # FastAPI routes and endpoints
├── venv/                # Virtual environment
├── animations/          # Generated animation files
├── config.py           # Configuration management
├── run.py              # Application entry point
├── run.sh              # Shell script to run the app
├── requirements.txt    # Python dependencies
├── env.example         # Environment variables example
├── README.md          # This file
└── .gitignore         # Git ignore rules
```

## Dependencies

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI
- **Manim**: Mathematical animation engine
- **Pydantic**: Data validation using Python type annotations

## Notes

- Animations are rendered in low quality by default for faster processing
- Generated animations are stored in the `animations/` directory
- The application creates temporary directories for rendering process
- Each animation gets a unique UUID for identification

## Development

To modify the animation logic, edit the `SimpleScene` class in `main.py`. You can:

- Add more complex animations
- Include mathematical equations
- Create different scene types
- Customize animation parameters

For more advanced Manim features, refer to the [Manim documentation](https://docs.manim.community/).

## Environment Variables

The application can be configured using environment variables. See `env.example` for all available options:

### Server Configuration
- `HOST`: Server host address (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
- `DEBUG`: Enable debug mode with auto-reload (default: `False`)

### Application Configuration
- `APP_TITLE`: Application title (default: `2D Animation AI`)
- `APP_DESCRIPTION`: Application description
- `APP_VERSION`: Application version (default: `1.0.0`)

### Animation Configuration
- `ANIMATIONS_DIR`: Directory for storing animations (default: `animations`)
- `DEFAULT_ANIMATION_TEXT`: Default text for animations (default: `Hello Manim!`)
- `DEFAULT_ANIMATION_COLOR`: Default color for animations (default: `BLUE`)

### Manim Configuration
- `MANIM_QUALITY`: Rendering quality - `low_quality`, `medium_quality`, `high_quality` (default: `low_quality`)
- `MANIM_PREVIEW`: Enable preview mode (default: `False`)

### File Management
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: `100`)
- `CLEANUP_TEMP_FILES`: Clean up temporary files after rendering (default: `True`) 