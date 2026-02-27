from fastapi import APIRouter, Request, Body
from fastapi.responses import JSONResponse
from app.core.config import Config

router = APIRouter()

@router.get("/config")
async def get_config(request: Request):
    config: Config = request.app.state.config
    return config.data

@router.post("/config/save")
async def save_config_v1(request: Request):
    config: Config = request.app.state.config
    try:
        config.save()
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

# Legacy
@router.get("/config_dirty")
async def config_dirty(request: Request):
    return {"unsaved_changes": getattr(request.app.state, "unsaved_changes", False)}

@router.post("/save_config")
async def save_config(request: Request, data: dict = Body(...)):
    c = request.app.state.config
    c.data.update(data)
    c.save()
    request.app.state.unsaved_changes = False
    return c.data
