from .base import BaseWidget
from PIL import Image, ImageDraw
from typing import Any

class ImageWidget(BaseWidget):
    def __init__(self, name: str, config: dict):
        super().__init__(name, config)
        self._cached_image = None
        self._last_path = None

    def draw(self, image: Image.Image, draw: ImageDraw, value: Any, min_val: float, max_val: float):
        image_path = value
        if not image_path:
            return

        if image_path != self._last_path:
            try:
                # Resolve relative path if needed based on home_dir
                if os.path.exists(image_path):
                    self._cached_image = Image.open(image_path).convert("RGBA")
                    self._last_path = image_path
                else:
                    self._cached_image = None
            except Exception:
                self._cached_image = None

        if self._cached_image:
            # Resize image to fit rect if specified
            w, h = self.rect["width"], self.rect["height"]
            if self._cached_image.size != (w, h):
                render_img = self._cached_image.resize((w, h), Image.Resampling.LANCZOS)
            else:
                render_img = self._cached_image
                
            image.paste(render_img, (self.rect["x"], self.rect["y"]), render_img)

    def info(self) -> dict:
        return {
            "name": "image",
            "description": "a static png image",
            "fields": []
        }
import os
