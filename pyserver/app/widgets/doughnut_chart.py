from .base import BaseWidget
from PIL import Image, ImageDraw
from typing import Any
import math

class DoughnutChartWidget(BaseWidget):
    def draw(self, image: Image.Image, draw: ImageDraw, value: Any, min_val: float, max_val: float):
        try:
            val = float(value)
        except (ValueError, TypeError):
            return

        w, h = self.rect["width"], self.rect["height"]
        x, y = self.rect["x"], self.rect["y"]
        used_color = self.config.get("used", "#48BB78")
        free_color = self.config.get("free", "#EDF2F7")
        rotation = float(self.config.get("rotation", 225))
        circumference = float(self.config.get("circumference", 270))
        cutout = self.config.get("cutout", "80%")
        
        # Calculate percentage
        range_val = max_val - min_val if max_val > min_val else 100
        percentage = (val - min_val) / range_val
        percentage = max(0.0, min(1.0, percentage))
        
        # In Pillow arc: 0 is right (3 o'clock). 
        # Chart.js rotation 225 means starting bottom-leftish. 
        # We need to map standard angles.
        start_angle = rotation - 90
        end_angle = start_angle + circumference
        
        val_angle = start_angle + (percentage * circumference)
        
        cutout_pct = float(str(cutout).replace("%", "")) / 100.0 if isinstance(cutout, str) and "%" in cutout else 0.8
        thickness = int((1.0 - cutout_pct) * (min(w, h) / 2))
        
        # Pillow's arc/chord uses bounding box. 
        # width parameter acts as stroke thickness
        draw.arc([x, y, x + w, y + h], start_angle, end_angle, fill=free_color, width=thickness)
        
        if val_angle > start_angle:
            draw.arc([x, y, x + w, y + h], start_angle, val_angle, fill=used_color, width=thickness)
        
    def info(self) -> dict:
        info = super().info()
        info["fields"].extend([
            {"name": "used", "value": "color"},
            {"name": "free", "value": "color"},
            {"name": "rotation", "value": "string"},
            {"name": "cutout", "value": "string"},
            {"name": "circumference", "value": "string"}
        ])
        return info
