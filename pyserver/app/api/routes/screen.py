from fastapi import APIRouter, Request, HTTPException, Body
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional
from app.core.models import Screen
import io

router = APIRouter()

def mark_dirty(app, redraw=False):
    app.state.unsaved_changes = True
    if redraw and hasattr(app.state, "worker"):
        import asyncio
        asyncio.create_task(app.state.worker.render_loop())

def _get_screen(config, screen_id: int):
    if not config.theme: return None
    return config.theme.get_screen(screen_id)

def _is_protected(config):
    # Agni Dark theme is read-only
    return config.get("theme", "").endswith("agni_dark.py")

@router.get("/active")
async def get_active_screen_v1(request: Request):
    return {"id": request.app.state.config.theme.screens[request.app.state.worker.screen_index].id if request.app.state.config.theme and request.app.state.config.theme.screens else 0}

class ScreenAddRequest(BaseModel):
    name: str

@router.post("/add")
async def add_screen_v1(request: Request, body: ScreenAddRequest):
    if _is_protected(request.app.state.config):
        raise HTTPException(status_code=403, detail="Agni Dark theme is read-only")
    config = request.app.state.config
    theme = config.theme
    if theme:
        new_id = max([s.id for s in theme.screens] + [0]) + 1
        new_screen = Screen(id=new_id, name=body.name)
        theme.screens.append(new_screen)
        mark_dirty(request.app, False)
        return new_screen.model_dump()
    raise HTTPException(status_code=404, detail="Theme not loaded")

class ScreenIdRequest(BaseModel):
    id: int

@router.post("/remove")
async def remove_screen_v1(request: Request, body: ScreenIdRequest):
    if _is_protected(request.app.state.config):
        raise HTTPException(status_code=403, detail="Agni Dark theme is read-only")
    config = request.app.state.config
    theme = config.theme
    if theme:
        theme.screens = [s for s in theme.screens if s.id != body.id]
        mark_dirty(request.app, False)
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Theme not loaded")

@router.post("/next")
async def next_screen_v1(request: Request, body: Optional[ScreenIdRequest] = None):
    w = getattr(request.app.state, "worker", None)
    if w and w.theme:
        import asyncio
        if body and body.id:
            for idx, s in enumerate(w.theme.screens):
                if s.id == body.id:
                    w.screen_index = idx
                    asyncio.create_task(w.render_loop())
                    return {"id": s.id}
        else:
            w.screen_index = (w.screen_index + 1) % len(w.theme.screens)
            asyncio.create_task(w.render_loop())
            return {"id": w.theme.screens[w.screen_index].id}
    raise HTTPException(status_code=400, detail="Worker or Theme missing")

class ScreenBgRequest(BaseModel):
    screen: int
    value: str

@router.post("/background")
async def set_background_v1(request: Request, body: ScreenBgRequest):
    if _is_protected(request.app.state.config):
        raise HTTPException(status_code=403, detail="Agni Dark theme is read-only")
    screen = _get_screen(request.app.state.config, body.screen)
    if screen:
        screen.background = body.value
        mark_dirty(request.app, True)
        return {"value": screen.background}
    raise HTTPException(status_code=404, detail="Screen not found")

# Legacy routes mapping perfectly to GUI paths
@router.get("/screen")
async def get_active_screen(request: Request):
    return await get_active_screen_v1(request)

@router.post("/set_screen_name")
async def set_screen_name(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    s = _get_screen(request.app.state.config, data.get("screen", 0))
    if s:
        s.name = data.get("name", "Screen")
        mark_dirty(request.app, False)
        return {"name": s.name}
    return JSONResponse(status_code=400, content={})

@router.post("/add_screen")
async def add_screen(request: Request, data: dict = Body(...)):
    body = ScreenAddRequest(name=data.get("name", "Screen"))
    try:
        return await add_screen_v1(request, body)
    except HTTPException:
        return JSONResponse(status_code=400, content={})

@router.post("/remove_screen")
async def remove_screen(request: Request, data: dict = Body(...)):
    body = ScreenIdRequest(id=data.get("id", 0))
    try:
        await remove_screen_v1(request, body)
        return {}
    except HTTPException:
        return JSONResponse(status_code=400, content={})

@router.post("/next_screen")
async def next_screen(request: Request, data: dict = Body(...)):
    body = ScreenIdRequest(id=data.get("id", 0)) if "id" in data else None
    try:
        return await next_screen_v1(request, body)
    except HTTPException:
        return JSONResponse(status_code=400, content={})

@router.post("/set_screen_duration")
async def set_screen_duration(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    # Legacy endpoint repurposed to set global rotation interval
    duration = data.get("duration", 60000)
    request.app.state.config.set("rotation_interval", duration)
    return {"duration": duration}

@router.post("/set_background")
async def set_background(request: Request, data: dict = Body(...)):
    body = ScreenBgRequest(screen=data.get("screen", 0), value=data.get("value", "#000"))
    try:
        return await set_background_v1(request, body)
    except HTTPException:
        return JSONResponse(status_code=400, content={})

@router.get("/lcd_screen")
async def get_lcd_screen(request: Request):
    buffer = request.app.state.worker.output_canvas
    if buffer:
        img_byte_arr = io.BytesIO()
        buffer.save(img_byte_arr, format='PNG')
        return Response(content=img_byte_arr.getvalue(), media_type="image/png")
    return Response(content=b"", media_type="image/png")
