from fastapi import APIRouter
from .routes import hardware, modular

api_router = APIRouter()

# v1 routes (clean REST)
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(hardware.router, tags=["hardware"])
v1_router.include_router(modular.router)

api_router.include_router(v1_router)
