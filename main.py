from fastapi import FastAPI
from app.router import router, shutdown_thread_pool
import config

# Create FastAPI app
app = FastAPI(
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
)

# Include the router
app.include_router(router)

# Shutdown event for graceful cleanup
@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown of background resources"""
    shutdown_thread_pool()
