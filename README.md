# 2D Animation AI

A FastAPI-based application that uses AI agents to generate mathematical animations with Manim. Transform natural language prompts into beautiful animated visualizations using OpenAI's GPT models and LangChain.

## 🎬 What This Project Does

This application combines the power of AI with mathematical visualization to create stunning 2D animations from simple text descriptions. Users can describe what they want to see animated (like "show a circle morphing into a square" or "animate the Pythagorean theorem"), and the AI will generate Manim code to create professional-quality mathematical animations.

### Key Features

- **AI-Powered Animation Generation**: Uses LangChain agents with OpenAI models to interpret natural language prompts
- **Manim Integration**: Renders high-quality mathematical animations using the Manim library  
- **Asynchronous Processing**: Background animation rendering with real-time status tracking
- **RESTful API**: Clean FastAPI endpoints for animation creation, status monitoring, and file management
- **Docker Support**: Containerized deployment with optimized Python environment
- **Automatic Cleanup**: Files are cleaned up after download to manage storage
- **Multiple Quality Options**: Choose from low, medium, or high quality rendering

## 🏗️ Architecture

The application is built with a modular architecture:

```
├── app/                    # Core application logic
│   ├── agents/            # LangChain AI agents
│   │   ├── animation_agent.py
│   │   └── code_generation_agent.py
│   ├── tools/             # Manim integration tools
│   │   ├── manim_tool.py
│   │   ├── code_executor.py
│   │   └── code_generator.py
│   ├── models.py          # Pydantic data models
│   ├── router.py          # API endpoint definitions
│   ├── config.py          # App configuration
│   └── status_tracker.py  # Animation status management
├── animations/            # Generated MP4 files
├── code_files/           # Generated Python/Manim code
├── media/                # Manim media cache
├── config.py             # Environment configuration
├── main.py               # FastAPI application entry point
├── Dockerfile           # Container configuration
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- OpenAI API Key
- FFmpeg (for video processing)
- LaTeX (for mathematical text rendering)

### Option 1: Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd 2d_animation_ai
   ```

2. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   # or
   ./run.sh
   # or
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Option 2: Docker Deployment

1. **Build the Docker image**
   ```bash
   ./scripts/docker.build.sh
   # or
   docker build -t 2d-animation-ai .
   ```

2. **Run the container**
   ```bash
   docker run -p 8000:8000 -e OPENAI_API_KEY="your-api-key" 2d-animation-ai
   ```

The application will be available at `http://localhost:8000`

## 📖 API Usage

### Create Animation

**POST** `/create-animation`

```json
{
  "prompt": "Create a circle that morphs into a square, then rotates 360 degrees"
}
```

**Response:**
```json
{
  "animation_id": "uuid-string",
  "status": "pending",
  "message": "Animation request received and queued for processing",
  "download_url": null
}
```

### Check Animation Status

**GET** `/animation-status/{animation_id}`

**Response:**
```json
{
  "animation_id": "uuid-string",
  "status": "completed",
  "message": "Animation generated successfully",
  "download_url": "/download-animation/uuid-string",
  "progress": "Rendering complete"
}
```

### Download Animation

**GET** `/download-animation/{animation_id}`

Returns the generated MP4 file. Files are automatically cleaned up after download.

### Other Endpoints

- **GET** `/` - Welcome message
- **GET** `/health` - Health check
- **GET** `/list-animations` - List all animations
- **DELETE** `/delete-animation/{animation_id}` - Delete specific animation

## 🎯 Example Prompts

Here are some example prompts you can try:

- **Basic Animations:**
  - "Create a text that says 'Hello World' appearing letter by letter"
  - "Show a circle growing from a point and changing colors"
  - "Animate a square rotating 360 degrees"

- **Mathematical Concepts:**
  - "Visualize the Pythagorean theorem with a right triangle"
  - "Show the sine wave function from 0 to 2π"
  - "Animate a parabola y = x² with a moving point"

- **Shape Transformations:**
  - "Morph a triangle into a circle"
  - "Show a line transforming into a spiral"
  - "Create a flowchart with connected boxes and arrows"

- **Physics Simulations:**
  - "Animate Newton's first law of motion"
  - "Show the concept of gravity with falling objects"
  - "Visualize wave interference patterns"

## ⚙️ Configuration

The application can be configured using environment variables:

### Server Configuration
- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8000`)
- `DEBUG` - Debug mode (default: `False`)

### Application Settings
- `APP_TITLE` - Application title (default: `"2D Animation AI"`)
- `APP_DESCRIPTION` - App description
- `APP_VERSION` - Version (default: `"1.0.0"`)

### Animation Settings
- `ANIMATIONS_DIR` - Directory for storing animations (default: `animations`)
- `MANIM_QUALITY` - Rendering quality: `low_quality`, `medium_quality`, `high_quality`
- `MANIM_PREVIEW` - Enable Manim preview (default: `False`)

### Required Environment Variables
- `OPENAI_API_KEY` - Your OpenAI API key (required)

### File Management
- `MAX_FILE_SIZE_MB` - Maximum file size limit (default: `100`)
- `CLEANUP_TEMP_FILES` - Auto-cleanup files after download (default: `True`)

## 🐳 Docker Details

The Docker setup includes:

- **Base Image:** Python 3.12 slim
- **System Dependencies:** FFmpeg, LaTeX, Cairo, Pango
- **Package Manager:** UV for faster Python package installation
- **Security:** Non-root user execution
- **Optimization:** Multi-stage build with dependency caching

## 🔧 Development

### Project Structure Details

- **Agents:** LangChain agents that interpret prompts and generate Manim code
- **Tools:** Custom tools that interface with Manim and execute generated code
- **Models:** Pydantic models for request/response validation
- **Status Tracker:** In-memory tracking of animation generation progress
- **Background Processing:** Thread pool executor for non-blocking animation generation

### Adding New Features

1. Create new tools in `app/tools/` for additional functionality
2. Extend agents in `app/agents/` for new AI capabilities  
3. Add new endpoints in `app/router.py` for additional API features
4. Update models in `app/models.py` for new data structures

## 🚨 Limitations

- **LaTeX Dependency:** Full LaTeX installation required for mathematical text rendering
- **OpenAI API:** Requires valid OpenAI API key and credits
- **Memory Usage:** Animations are processed in-memory; large animations may require more RAM
- **File Storage:** Generated files are stored locally (consider cloud storage for production)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is open source. Please check the LICENSE file for details.

## 🆘 Troubleshooting

### Common Issues

1. **"OpenAI API key not found"**
   - Ensure `OPENAI_API_KEY` environment variable is set
   - Check that your API key is valid and has credits

2. **Animation generation fails**
   - Check the logs for specific error messages
   - Verify that Manim dependencies are installed correctly
   - Try simpler prompts first

3. **Docker build issues**
   - Ensure Docker has sufficient memory allocated
   - LaTeX installation may take significant time and space

4. **File not found errors**
   - Check that the `animations/` and `code_files/` directories exist
   - Verify file permissions if running in Docker

### Getting Help

- Check the application logs for detailed error messages
- Use the `/health` endpoint to verify service status
- Review the `/list-animations` endpoint to see animation status

---

**Built with ❤️ using FastAPI, LangChain, Manim, and OpenAI** 