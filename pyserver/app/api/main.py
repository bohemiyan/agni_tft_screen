from fastapi import APIRouter
from .routes import config, theme, screen, hardware, widgets, sensors

api_router = APIRouter()

# v1 routes (clean REST)
v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(config.router, tags=["config"])
v1_router.include_router(theme.router, tags=["theme"])
v1_router.include_router(screen.router, prefix="/screen", tags=["screen"])
v1_router.include_router(hardware.router, tags=["hardware"])
v1_router.include_router(widgets.router, prefix="/widget", tags=["widgets"])
v1_router.include_router(sensors.router, prefix="/sensors", tags=["sensors"])

# Legacy routes (perfect frontend compatibility via consolidated standard endpoints)
legacy_router = APIRouter(prefix="/api")
legacy_router.include_router(config.router, tags=["legacy_config"])
legacy_router.include_router(theme.router, tags=["legacy_theme"])
legacy_router.include_router(screen.router, tags=["legacy_screen"])
legacy_router.include_router(widgets.router, tags=["legacy_widgets"])
legacy_router.include_router(hardware.router, tags=["legacy_hardware"])
legacy_router.include_router(sensors.router, tags=["legacy_sensors"])

api_router.include_router(v1_router)
api_router.include_router(legacy_router)

