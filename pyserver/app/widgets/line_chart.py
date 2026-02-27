from .base import BaseWidget
from PIL import Image, ImageDraw
from typing import Any

class LineChartWidget(BaseWidget):
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
        
        color = self.config.get("color", "#00FF00")
        points = self.config.get("points", len(data))
        data = data[-points:]
        
        if len(data) < 2:
            return

        step_x = w / (len(data) - 1)
        range_val = max_val - min_val if max_val > min_val else 100

        line_points = []
        for i, val in enumerate(data):
            norm_val = (val - min_val) / range_val
            px = x + i * step_x
            py = y + h - (norm_val * h)
            line_points.append((px, py))
            
        draw.line(line_points, fill=color, width=self.config.get("thickness", 1))

    def info(self) -> dict:
        info = super().info()
        info["fields"].extend([
            {"name": "color", "value": "color"},
            {"name": "points", "value": "number"},
            {"name": "thickness", "value": "number"}
        ])
        return info
