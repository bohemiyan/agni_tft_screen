from .base import BaseWidget
from PIL import Image, ImageDraw, ImageFont
from typing import Any

class TextWidget(BaseWidget):
    def draw(self, image: Image.Image, draw: ImageDraw, value: Any, min_val: float, max_val: float):
        font_style = self.config.get("font", "Arial")
        font_size = self.config.get("size", 18)
        color = self.config.get("color", "#FFFFFF")
        
        try:
            # Note: In a real environment, you'd need the path to the font file
            font = ImageFont.truetype(font_style, font_size)
        except:
            font = ImageFont.load_default()

        text = str(value)
        if self.config.get("format"):
            try:
                if isinstance(value, tuple) or isinstance(value, list):
                    text = self.config.get("format").format(*value)
                else:
                    text = self.config.get("format").format(value)
            except Exception as e:
                pass

        draw.text(
            (self.rect["x"], self.rect["y"]),
            text,
            fill=color,
            font=font
        )

    def info(self) -> dict:
        info = super().info()
        info["fields"].extend([
            {"name": "font", "value": "font"},
            {"name": "size", "value": "number"},
            {"name": "color", "value": "color"}
        ])
        return info
