from abc import ABC, abstractmethod
from PIL import Image, ImageDraw
from typing import Any, Dict

class BaseWidget(ABC):
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.rect = config.get("rect", {"x": 0, "y": 0, "width": 0, "height": 0})

    @abstractmethod
    def draw(self, image: Image.Image, draw: ImageDraw, value: Any, min_val: float, max_val: float):
        pass

    def info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "rect": self.rect,
            "fields": []
        }
