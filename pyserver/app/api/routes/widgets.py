from fastapi import APIRouter, Request, HTTPException, Body, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any
from app.core.models import WidgetConfig
import os

router = APIRouter()

def mark_dirty(app, redraw=False):
    app.state.unsaved_changes = True
    if redraw and hasattr(app.state, "worker"):
        import asyncio
        asyncio.create_task(app.state.worker.render_loop())

def _get_screen(config, screen_id: int):
    if not config.theme: return None
    return config.theme.get_screen(screen_id)

def _get_widget(screen, widget_id: int):
    if not screen: return None
    for w in screen.widgets:
        if w.id == widget_id:
            return w
    return None

def _is_protected(config):
    # Agni Dark theme is read-only
    return config.get("theme", "").endswith("agni_dark.py")

import random
def _get_random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def _make_blank_widget(widget_id: int, info: dict):
    w = {
        "id": widget_id, "group": 1, "name": info["name"],
        "rect": {"x": 10, "y": 10, "width": 50, "height": 50},
        "sensor": False, "value": "", "format": "", "refresh": 1000, "debug_frame": True
    }
    for field in info.get("fields", []):
        fv = field["value"]
        fname = field["name"]
        if fv == "color": w[fname] = _get_random_color()
        elif fv in ("reserved", "boolean"): w[fname] = False
        elif fv in ("clock", "number"): w[fname] = 0
        elif fv == "font": w[fname] = "18px Arial"
        else:
            if ":" in str(fv): w[fname] = str(fv).split(":")[1].split(",")[0]
            else: w[fname] = ""
    return WidgetConfig(**w)

@router.get("/")
async def get_widgets_v1(request: Request):
    widgets = [
        {"name": "text", "description": "Text widget", "fields": [{"name": "font", "value": "font"}]},
        {"name": "bar_chart", "description": "Bar chart", "fields": [{"name": "fill", "value": "color"}]},
        {"name": "line_chart", "description": "Line chart", "fields": [{"name": "color", "value": "color"}]},
        {"name": "image", "description": "Static image", "fields": []},
        {"name": "doughnut_chart", "description": "Doughnut chart", "fields": [
            {"name": "used", "value": "color"}, {"name": "free", "value": "color"},
            {"name": "rotation", "value": "string"}, {"name": "cutout", "value": "string"}, {"name": "circumference", "value": "string"}
        ]},
        {"name": "custom_bar", "description": "Custom bar", "fields": []},
        {"name": "iconify", "description": "Iconify icon", "fields": [{"name": "iconSet", "value": "list:mdi,material-symbols"}, {"name": "color", "value": "color"}]},
        {"name": "weather_icon", "description": "Weather icon", "fields": [{"name": "type", "value": "list:weather,temperature,winddirection"}, {"name": "color", "value": "color"}]}
    ]
    for w in widgets:
        w["fields"] = [{"name": "name", "value": "string"}, {"name": "rect", "value": "rect"}, {"name": "sensor", "value": "reserved"}, {"name": "value", "value": "image" if w["name"] == "image" else "string"}, {"name": "format", "value": "string"}, {"name": "refresh", "value": "clock"}, {"name": "debug_frame", "value": "reserved"}] + w["fields"]
    return widgets

class AddWidgetRequest(BaseModel):
    screen: int
    name: str

@router.post("/add")
async def add_widget_v1(request: Request, body: AddWidgetRequest):
    if _is_protected(request.app.state.config):
        raise HTTPException(status_code=403, detail="Agni Dark theme is read-only")
    s = _get_screen(request.app.state.config, body.screen)
    if s:
        nid = max([w.id for w in s.widgets] + [0]) + 1
        w_info = await get_widgets_v1(request)
        info = next((i for i in w_info if i["name"] == body.name), None)
        if info:
            nw = _make_blank_widget(nid, info)
            s.widgets.append(nw)
            mark_dirty(request.app, True)
            return nw.model_dump()
    raise HTTPException(status_code=404, detail="Screen not found")

class DeleteWidgetRequest(BaseModel):
    screen: int
    widget: int

@router.post("/delete")
async def delete_widget_v1(request: Request, body: DeleteWidgetRequest):
    if _is_protected(request.app.state.config):
        raise HTTPException(status_code=403, detail="Agni Dark theme is read-only")
    s = _get_screen(request.app.state.config, body.screen)
    if s:
        s.widgets = [w for w in s.widgets if w.id != body.widget]
        mark_dirty(request.app, True)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Screen or widget not found")

class SensorRequest(BaseModel):
    screen: int
    widget: int
    sensor: str

@router.post("/sensor")
async def set_sensor_v1(request: Request, body: SensorRequest):
    if _is_protected(request.app.state.config):
        raise HTTPException(status_code=403, detail="Agni Dark theme is read-only")
    w = _get_widget(_get_screen(request.app.state.config, body.screen), body.widget)
    if w:
        w.value = body.sensor
        w.sensor = True
        mark_dirty(request.app, False)
        return {"value": w.value}
    raise HTTPException(status_code=404, detail="Widget not found")

# Legacy mapped GUI endpoints
@router.get("/widget_list")
async def get_widget_list(request: Request):
    return await get_widgets_v1(request)

@router.post("/add_widget")
async def add_widget(request: Request, data: dict = Body(...)):
    body = AddWidgetRequest(screen=data.get("screen", 0), name=data.get("name", "text"))
    try:
        return await add_widget_v1(request, body)
    except Exception:
        return JSONResponse(status_code=400, content={})

@router.post("/delete_widget")
async def delete_widget(request: Request, data: dict = Body(...)):
    body = DeleteWidgetRequest(screen=data.get("screen", 0), widget=data.get("widget", 0))
    try:
        await delete_widget_v1(request, body)
        return {}
    except Exception:
        return JSONResponse(status_code=400, content={})

@router.post("/set_sensor")
async def set_sensor(request: Request, data: dict = Body(...)):
    body = SensorRequest(screen=data.get("screen", 0), widget=data.get("widget", 0), sensor=data.get("sensor", ""))
    try:
        return await set_sensor_v1(request, body)
    except Exception:
        return JSONResponse(status_code=400, content={})

@router.post("/toggle_debug_frame")
async def toggle_debug_frame(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    w = _get_widget(_get_screen(request.app.state.config, data.get("screen", 0)), data.get("widget", 0))
    if w:
        w.debug_frame = not w.debug_frame
        mark_dirty(request.app, True)
        return {"value": w.debug_frame}
    return JSONResponse(status_code=400, content={})

@router.post("/adjust_rect")
async def adjust_rect(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    w = _get_widget(_get_screen(request.app.state.config, data.get("screen", 0)), data.get("widget", 0))
    if w and "rect" in data:
        w.rect.update(data["rect"])
        mark_dirty(request.app, True)
        return {}
    return JSONResponse(status_code=400, content={})

@router.post("/update_property")
async def update_property(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    w = _get_widget(_get_screen(request.app.state.config, data.get("screen", 0)), data.get("widget", 0))
    if w and "key" in data and "value" in data:
        k = data["key"]
        v = data["value"]
        setattr(w, k, v)
        if k == "value" and getattr(w, "sensor", False):
            w.sensor = False
        mark_dirty(request.app, False)
        return {"value": getattr(w, k)}
    return JSONResponse(status_code=400, content={})

@router.post("/up_widget")
async def up_widget(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    s = _get_screen(request.app.state.config, data.get("screen", 0))
    if s:
        wid = data.get("widget")
        for i, w in enumerate(s.widgets):
            if w.id == wid and i > 0:
                w.id, s.widgets[i-1].id = s.widgets[i-1].id, w.id
                s.widgets.sort(key=lambda x: x.id)
                mark_dirty(request.app, True)
                return {}
    return JSONResponse(status_code=400, content={})

@router.post("/down_widget")
async def down_widget(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    s = _get_screen(request.app.state.config, data.get("screen", 0))
    if s:
        wid = data.get("widget")
        for i, w in enumerate(s.widgets):
            if w.id == wid and i < len(s.widgets) - 1:
                w.id, s.widgets[i+1].id = s.widgets[i+1].id, w.id
                s.widgets.sort(key=lambda x: x.id)
                mark_dirty(request.app, True)
                return {}
    return JSONResponse(status_code=400, content={})

@router.post("/upload_image")
async def upload_image(request: Request, screen: int, widget: int, file: UploadFile = File(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    w = _get_widget(_get_screen(request.app.state.config, screen), widget)
    if w:
        theme_path = getattr(request.app.state.config.theme, '__file_path__', 'app/themes/custom')
        dir_path = os.path.dirname(os.path.abspath(theme_path))
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        w.value = f"app/themes/{os.path.basename(dir_path)}/{file.filename}"
        mark_dirty(request.app, True)
        return {"value": w.value, "widget": w.id}
    return JSONResponse(status_code=400, content={})
