from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from app.core.modular_models import SensorNode, WidgetNode, ScreenNode, ThemeNode
from typing import List, Optional

router = APIRouter(prefix="/modular", tags=["modular"])

class SettingsModel(BaseModel):
    poll: Optional[int] = None
    rotation_interval: Optional[int] = None

def get_registry(request: Request):
    return request.app.state.registry

def get_config(request: Request):
    return request.app.state.config

@router.get("/settings", response_model=SettingsModel)
async def get_settings(request: Request):
    cfg = get_config(request)
    return SettingsModel(
        poll=cfg.get("poll", 1000),
        rotation_interval=cfg.get("rotation_interval", 60000)
    )

@router.post("/settings", response_model=SettingsModel)
async def update_settings(request: Request, settings: SettingsModel):
    cfg = get_config(request)
    if settings.poll is not None:
        cfg.set("poll", settings.poll)
    if settings.rotation_interval is not None:
        cfg.set("rotation_interval", settings.rotation_interval)
    cfg.save()
    return get_settings(request)

@router.get("/sensors", response_model=List[SensorNode])
async def list_sensors(request: Request):
    return list(get_registry(request).sensors.values())

@router.post("/sensors", response_model=SensorNode)
async def create_sensor(request: Request, sensor: SensorNode):
    return get_registry(request).add_sensor(sensor)

@router.delete("/sensors/{sensor_id}")
async def delete_sensor(request: Request, sensor_id: str):
    reg = get_registry(request)
    if sensor_id in reg.sensors and reg.sensors[sensor_id].protected:
        raise HTTPException(status_code=403, detail="Cannot delete protected system sensor.")
    reg.delete_sensor(sensor_id)
    return {"status": "deleted"}

@router.get("/widgets", response_model=List[WidgetNode])
async def list_widgets(request: Request):
    return list(get_registry(request).widgets.values())

@router.post("/widgets", response_model=WidgetNode)
async def create_widget(request: Request, widget: WidgetNode):
    return get_registry(request).add_widget(widget)

@router.delete("/widgets/{widget_id}")
async def delete_widget(request: Request, widget_id: str):
    reg = get_registry(request)
    if widget_id in reg.widgets and reg.widgets[widget_id].protected:
        raise HTTPException(status_code=403, detail="Cannot delete protected system widget.")
    reg.delete_widget(widget_id)
    return {"status": "deleted"}

@router.get("/screens", response_model=List[ScreenNode])
async def list_screens(request: Request):
    return list(get_registry(request).screens.values())

@router.post("/screens", response_model=ScreenNode)
async def create_screen(request: Request, screen: ScreenNode):
    return get_registry(request).add_screen(screen)

@router.delete("/screens/{screen_id}")
async def delete_screen(request: Request, screen_id: str):
    reg = get_registry(request)
    if screen_id in reg.screens and reg.screens[screen_id].protected:
        raise HTTPException(status_code=403, detail="Cannot delete protected system screen.")
    reg.delete_screen(screen_id)
    return {"status": "deleted"}

@router.get("/themes", response_model=List[ThemeNode])
async def list_themes(request: Request):
    return list(get_registry(request).themes.values())

@router.post("/themes", response_model=ThemeNode)
async def create_theme(request: Request, theme: ThemeNode):
    return get_registry(request).add_theme(theme)

@router.delete("/themes/{theme_id}")
async def delete_theme(request: Request, theme_id: str):
    reg = get_registry(request)
    if theme_id in reg.themes and reg.themes[theme_id].protected:
        raise HTTPException(status_code=403, detail="Cannot delete protected system theme.")
    reg.delete_theme(theme_id)
    return {"status": "deleted"}

@router.post("/active_theme/{theme_id}")
async def set_active_theme(request: Request, theme_id: str):
    reg = get_registry(request)
    if theme_id not in reg.themes:
        raise HTTPException(status_code=404, detail="Theme not found")
    reg.active_theme_id = theme_id
    reg.save()
    
    # Restart worker logic with the new theme
    if hasattr(request.app.state, "worker"):
        import asyncio
        w = request.app.state.worker
        w.screen_index = 0
        asyncio.create_task(w.render_loop())
    return {"status": "active"}

