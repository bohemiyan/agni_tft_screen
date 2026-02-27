import os
import sys

# Add the project root to sys.path to allow relative imports in main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.core.config import Config
from app.core.registry import Registry
from app.worker import Worker
from app.api.main import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing complete pyserver application state...")
    config_path = os.getenv("S1PANEL_CONFIG_PATH", "config.py")
    
    try:
        app.state.config = Config(config_path)
    except Exception as e:
        logger.warning(f"Could not load config from {config_path}: {e}")
        app.state.config = Config("server/config.json")
        
    registry_path = os.path.join(os.path.dirname(config_path), 'registry.json')
    app.state.registry = Registry(registry_path)
        
    app.state.worker = Worker(app.state.config, app.state.registry)
    
    worker_task = asyncio.create_task(app.state.worker.start())
    
    yield
    
    # Shutdown
    if hasattr(app.state, "worker"):
        await app.state.worker.stop()

app = FastAPI(lifespan=lifespan, title="s1panel Python Backend")

# Allow CORS for the web GUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the full structured API
app.include_router(api_router)

# Mount the static Vue frontend GUI
client_dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "client", "dist"))
if os.path.exists(client_dist_dir):
    logger.info(f"Mounting static frontend from: {client_dist_dir}")
    app.mount("/", StaticFiles(directory=client_dist_dir, html=True), name="static")
else:
    logger.warning(f"Frontend dist block not found at {client_dist_dir}. GUI will not be served.")
    @app.get("/")
    async def root():
        return {"status": "ok", "service": "s1panel", "message": "GUI not built"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8888)
