from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SensorNode(BaseModel):
    id: str
    type: str # e.g., 'cpu_temp', 'weather'
    name: str = "New Sensor"
    config: Dict[str, Any] = {}
    protected: bool = False

class WidgetNode(BaseModel):
    id: str
    type: str # e.g., 'text', 'line_chart'
    name: str = "New Widget"
    sensor_id: Optional[str] = None
    rect: Dict[str, int] = {"x": 0, "y": 0, "width": 50, "height": 50}
    properties: Dict[str, Any] = {}
    protected: bool = False

class ScreenNode(BaseModel):
    id: str
    name: str = "New Screen"
    background: str = "#000000"
    widget_ids: List[str] = []
    protected: bool = False

class ThemeNode(BaseModel):
    id: str
    name: str = "New Theme"
    orientation: str = "portrait"
    refresh: str = "update"
    rotation_interval: int = 60000
    screen_ids: List[str] = []
    protected: bool = False
