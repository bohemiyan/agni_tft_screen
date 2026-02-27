from .base import BaseWidget
from PIL import Image, ImageDraw
from typing import Any

class CustomBarWidget(BaseWidget):
    def draw(self, image: Image.Image, draw: ImageDraw, value: Any, min_val: float, max_val: float):
        try:
            val = float(value)
        except (ValueError, TypeError):
            return

        w, h = self.rect["width"], self.rect["height"]
        x, y = self.rect["x"], self.rect["y"]
        
        range_val = max_val - min_val if max_val > min_val else 100
        percentage = (val - min_val) / range_val
        percentage = max(0.0, min(1.0, percentage))
        
        fill_width = w * percentage
        
        # Solid fallback for gradients
        draw.rectangle([x, y, x + w, y + h], fill="#404040")
        if fill_width > 0:
            draw.rectangle([x, y, x + fill_width, y + h], fill="lightgreen")

    def info(self) -> dict:
        info = super().info()
        return info
