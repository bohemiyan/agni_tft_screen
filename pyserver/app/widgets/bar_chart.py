from .base import BaseWidget
from PIL import Image, ImageDraw
from typing import Any

class BarChartWidget(BaseWidget):
    def draw(self, image: Image.Image, draw: ImageDraw, value: Any, min_val: float, max_val: float):
        if not value:
            return
            
        try:
            if isinstance(value, str):
                data = [float(x) for x in value.split(",")]
            else:
                data = [float(value)]
        except Exception:
            return

        x, y = self.rect["x"], self.rect["y"]
        w, h = self.rect["width"], self.rect["height"]
        
        fill = self.config.get("fill", "#00FF00")
        points = self.config.get("points", len(data))
        data = data[-points:]
        
        if not data:
            return

        bar_width = w / len(data)
        range_val = max_val - min_val if max_val > min_val else 100

        for i, val in enumerate(data):
            # Calculate bar height
            norm_val = (val - min_val) / range_val
            bar_height = norm_val * h
            
            x0 = x + i * bar_width
            y0 = y + h - bar_height
            x1 = x0 + bar_width - 1
            y1 = y + h
            
            draw.rectangle([x0, y0, x1, y1], fill=fill)

    def info(self) -> dict:
        info = super().info()
        info["fields"].extend([
            {"name": "fill", "value": "color"},
            {"name": "points", "value": "number"}
        ])
        return info
