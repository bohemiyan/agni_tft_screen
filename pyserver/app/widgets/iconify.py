from .base import BaseWidget
from PIL import Image, ImageDraw
import requests
import io
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Simple globally cached icons to prevent re-fetching the same SVG over the network
ICON_CACHE = {}

def get_icon(slug: str, width: int, height: int, color: str) -> Image.Image:
    cache_key = f"{slug}_{width}_{height}_{color}"
    if cache_key in ICON_CACHE:
        return ICON_CACHE[cache_key]
        
    url = f"https://api.iconify.design/{slug}.svg"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            svg_data = resp.text
            # Iconify uses 'currentColor' for fill and stroke.
            svg_data = svg_data.replace('currentColor', color)
            
            # Rasterize logic
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPM
            
            # svglib parsing
            drawing = svg2rlg(io.StringIO(svg_data))
            if drawing:
                # Scale the drawing itself to the requested size
                scale_x = width / float(drawing.width)
                scale_y = height / float(drawing.height)
                drawing.scale(scale_x, scale_y)
                drawing.width = width
                drawing.height = height
                
                # Render to PNG buffer
                img_data = renderPM.drawToString(drawing, fmt='PNG')
                # Load via PIL
                img = Image.open(io.BytesIO(img_data)).convert("RGBA")
                ICON_CACHE[cache_key] = img
                return img
    except Exception as e:
        logger.error(f"Failed to load icon {slug} from Iconify: {e}")
    return None

class IconifyWidget(BaseWidget):
    def draw(self, image: Image.Image, draw: ImageDraw, value: Any, min_val: float, max_val: float):
        if not value:
            return
            
        iconSet = self.config.get("iconSet", "mdi")
        color = self.config.get("color", "#FFFFFF")
        slug = f"{iconSet}/{value}"
        
        icon_img = get_icon(slug, self.rect["width"], self.rect["height"], color)
        
        if icon_img:
            # use alpha channel as mask if available
            mask = icon_img if icon_img.mode == 'RGBA' else None
            image.paste(icon_img, (self.rect["x"], self.rect["y"]), mask)

    def info(self) -> dict:
        info = super().info()
        info["fields"].extend([
            {"name": "iconSet", "value": "list:mdi,material-symbols,simple-icons"},
            {"name": "color", "value": "color"}
        ])
        return info
