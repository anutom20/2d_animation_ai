from fastapi import FastAPI
from app.router import router
import config

# Create FastAPI app
app = FastAPI(
    title=config.APP_TITLE,
    description=config.APP_DESCRIPTION,
    version=config.APP_VERSION,
)

# Include the router
app.include_router(router)
