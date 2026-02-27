from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LEDConfig(BaseModel):
    theme: int = 4
    intensity: int = 3
    speed: int = 3

class WidgetConfig(BaseModel):
    id: int
    group: int = 1
    name: str
    rect: Dict[str, int]
    sensor: bool = False
    value: Any = None
    format: Optional[str] = None
    refresh: int = 1000
    debug_frame: bool = False
    
    # Catch-all for extra widget-specific fields (like color, font, fill, etc.)
    class Config:
        extra = "allow"

class Screen(BaseModel):
    id: int
    name: str = "Screen"
    background: str = "#000000"
    duration: int = 60000
    led_config: Optional[LEDConfig] = None
    widgets: List[WidgetConfig] = []
    
class Theme(BaseModel):
    orientation: str = "portrait"
    refresh: str = "update"
    screens: List[Screen] = []

    def get_screen(self, screen_id: int) -> Optional[Screen]:
        for screen in self.screens:
            if screen.id == screen_id:
                return screen
        return None
