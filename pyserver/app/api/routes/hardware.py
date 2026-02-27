from fastapi import APIRouter, Request, Response
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

@router.get("/led")
async def get_led_strip(request: Request):
    config = request.app.state.config
    led_config = config.get("led_config", {"theme": 4, "intensity": 3, "speed": 3})
    return led_config

class LedRequest(BaseModel):
    theme: Optional[int] = None
    intensity: Optional[int] = None
    speed: Optional[int] = None
    screen: Optional[int] = None

@router.post("/led")
async def set_led_strip(request: Request, body: LedRequest):
    config = request.app.state.config
    led_config = config.get("led_config", {"theme": 4, "intensity": 3, "speed": 3})
    
    if body.theme is not None: led_config["theme"] = body.theme
    if body.intensity is not None: led_config["intensity"] = body.intensity
    if body.speed is not None: led_config["speed"] = body.speed
    
    config.set("led_config", led_config)
    # Signal worker state.update_led = True in full impl
    return led_config

@router.get("/lcd/screen")
async def get_lcd_screen(request: Request):
    # Returns the current canvas buffer as a PNG image 
    # Used by the frontend 'Device' preview tab
    worker = request.app.state.worker
    if worker and worker.canvas:
        import io
        img_byte_arr = io.BytesIO()
        worker.canvas.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        return Response(content=img_byte_arr, media_type="image/png")
    return Response(status_code=404)
