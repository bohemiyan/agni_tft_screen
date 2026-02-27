from fastapi import APIRouter, Request, HTTPException, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

def _is_protected(config):
    # Agni Dark theme is read-only
    return config.get("theme", "").endswith("agni_dark.py")

def mark_dirty(app, redraw=False):
    app.state.unsaved_changes = True
    if redraw and hasattr(app.state, "worker"):
        import asyncio
        asyncio.create_task(app.state.worker.render_loop())

@router.get("/theme")
async def get_theme(request: Request):
    config = request.app.state.config
    if config.theme:
        return config.theme.model_dump()
    return {}

class ThemeOrientationRequest(BaseModel):
    orientation: str

@router.post("/theme/orientation")
async def set_orientation(request: Request, body: ThemeOrientationRequest):
    if _is_protected(request.app.state.config):
        raise HTTPException(status_code=403, detail="Agni Dark theme is read-only")
    config = request.app.state.config
    if config.theme:
        if body.orientation in ["portrait", "landscape"]:
            config.theme.orientation = body.orientation
            return {"orientation": config.theme.orientation}
        raise HTTPException(status_code=400, detail="Invalid orientation")
    raise HTTPException(status_code=404, detail="Theme not loaded")

class ThemeRefreshRequest(BaseModel):
    refresh: str

@router.post("/theme/refresh")
async def set_refresh(request: Request, body: ThemeRefreshRequest):
    if _is_protected(request.app.state.config):
        raise HTTPException(status_code=403, detail="Agni Dark theme is read-only")
    config = request.app.state.config
    if config.theme:
        if body.refresh in ["redraw", "update"]:
            config.theme.refresh = body.refresh
            config.set("refresh_method", body.refresh)
            return {"refresh": config.theme.refresh}
        raise HTTPException(status_code=400, detail="Invalid refresh method")
    raise HTTPException(status_code=404, detail="Theme not loaded")

# Legacy Endpoints
@router.post("/theme_save")
async def theme_save(request: Request):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    c = request.app.state.config
    c.save()
    request.app.state.unsaved_changes = False
    return c.theme.model_dump() if c.theme else {}

@router.post("/theme_revert")
async def theme_revert(request: Request):
    c = request.app.state.config
    c.load()
    request.app.state.unsaved_changes = False
    mark_dirty(request.app, True)
    return c.theme.model_dump() if c.theme else {}

@router.post("/set_orientation")
async def set_orientation_legacy(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    if request.app.state.config.theme:
        request.app.state.config.theme.orientation = data.get("orientation", "portrait")
        mark_dirty(request.app, True)
        return {"orientation": request.app.state.config.theme.orientation}
    return JSONResponse(status_code=400, content={})

@router.post("/set_refresh")
async def set_refresh_legacy(request: Request, data: dict = Body(...)):
    if _is_protected(request.app.state.config):
        return JSONResponse(status_code=403, content={"error": "Agni Dark theme is read-only"})
    if request.app.state.config.theme:
        request.app.state.config.theme.refresh = data.get("refresh", "update")
        mark_dirty(request.app, False)
        return {"refresh": request.app.state.config.theme.refresh}
    return JSONResponse(status_code=400, content={})

class ThemeCreateRequest(BaseModel):
    name: str

@router.post("/theme/create")
async def create_theme(request: Request, body: ThemeCreateRequest):
    import re, os
    slug = re.sub(r'[^a-z0-9_]+', '_', body.name.lower()).strip('_')
    if not slug:
        raise HTTPException(status_code=400, detail="Invalid theme name")
        
    config = request.app.state.config
    theme_dir = os.path.join(config.config_dir, "app", "themes", slug)
    os.makedirs(theme_dir, exist_ok=True)
    
    theme_py = os.path.join(theme_dir, f"{slug}.py")
    if os.path.exists(theme_py):
        raise HTTPException(status_code=400, detail="Theme already exists")
        
    with open(theme_py, "w", encoding="utf-8") as f:
        f.write("# Automatically generated Python theme\n\nTHEME = {\n")
        f.write("    'orientation': 'portrait',\n")
        f.write("    'refresh': 'update',\n")
        f.write("    'screens': [\n        {'id': 1, 'name': 'Screen 1', 'background': '#0f172a', 'widgets': []}\n    ]\n}\n")
        
    theme_list = config.get("theme_list", [])
    theme_list.append({"config": f"app/themes/{slug}/{slug}.py", "name": body.name})
    config.set("theme_list", theme_list)
    config.set("theme", f"app/themes/{slug}/{slug}.py")
    config.save()
    config.load()
    
    if hasattr(request.app.state, "worker"):
        w = request.app.state.worker
        w.screen_index = 0
        w.config = config
    
    return {"status": "success", "config": f"app/themes/{slug}/{slug}.py"}
