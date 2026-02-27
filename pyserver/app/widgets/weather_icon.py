from .base import BaseWidget
from PIL import Image, ImageDraw
from typing import Any
import math
from .iconify import get_icon

# WMO Weather Icons mapping mapped to Iconify "wi" collection
WMO_ICONS = {
     0: { 'day': 'wi/forecast-io-clear-day',           'night': 'wi/night-clear' },
     1: { 'day': 'wi/forecast-io-clear-day',           'night': 'wi/night-clear' },
     2: { 'day': 'wi/forecast-io-partly-cloudy-day',   'night': 'wi/forecast-io-partly-cloudy-night' },
     3: { 'day': 'wi/cloudy',                          'night': 'wi/cloudy' },
    45: { 'day': 'wi/day-fog',                         'night': 'wi/night-fog' },
    48: { 'day': 'wi/fog',                             'night': 'wi/fog' },
    51: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    53: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    55: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    56: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    57: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    61: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    63: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    65: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    66: { 'day': 'wi/day-rain-mix',                    'night': 'wi/night-rain-mix' },
    67: { 'day': 'wi/day-rain-mix',                    'night': 'wi/night-rain-mix' },
    71: { 'day': 'wi/day-snow',                        'night': 'wi/night-snow' },  
    73: { 'day': 'wi/day-snow',                        'night': 'wi/night-snow' },
    75: { 'day': 'wi/day-snow',                        'night': 'wi/night-snow' },
    77: { 'day': 'wi/day-snow',                        'night': 'wi/night-snow' },
    80: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    81: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    82: { 'day': 'wi/day-rain',                        'night': 'wi/night-rain' },
    85: { 'day': 'wi/day-snow',                        'night': 'wi/night-snow' },
    86: { 'day': 'wi/day-snow',                        'night': 'wi/night-snow' },
    95: { 'day': 'wi/day-thunderstorm',                'night': 'wi/night-thunderstorm' },
    96: { 'day': 'wi/day-snow-thunderstorm',           'night': 'wi/night-snow-thunderstorm' },
    99: { 'day': 'wi/day-snow-thunderstorm',           'night': 'wi/night-snow-thunderstorm' },
}

WIND_DIR_ICONS = {
    'N' : 'wi/direction-up',
    'NE': 'wi/direction-up-right',
    'E' : 'wi/direction-right',
    'SE': 'wi/direction-down-right',
    'S' : 'wi/direction-down',
    'SW': 'wi/direction-down-left',
    'W' : 'wi/direction-left',
    'NW': 'wi/direction-up-left'
}

WIND_DIRECTIONS = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

class WeatherIconWidget(BaseWidget):
    def draw(self, image: Image.Image, draw: ImageDraw, value: Any, min_val: float, max_val: float):
        try:
            val = float(value)
        except (ValueError, TypeError):
            val = 0

        color = self.config.get("color", "#FFFFFF")
        widget_type = self.config.get("type", "weather")
        icon_slug = "carbon/document-unknown"
        bg_icon_slug = None
        
        if widget_type == 'weather':
            mapping = WMO_ICONS.get(int(val), WMO_ICONS.get(0))
            is_day = True # Node version logic was somewhat missing max_val logic, default to day
            icon_slug = mapping['day'] if is_day else mapping['night']
        elif widget_type == 'temperature':
            if val >= 21:
                icon_slug = "carbon/hot"
            elif val <= 10:
                icon_slug = "carbon/snowflake-cold"
            else:
                icon_slug = "carbon/thermometer"
        elif widget_type == 'winddirection':
            index = int(round(val / 45) % 8)
            direction = WIND_DIRECTIONS[index]
            icon_slug = WIND_DIR_ICONS.get(direction, 'wi/direction-up')
            bg_icon_slug = 'gis/compass'

        # Fetch and compose background + foreground icons
        if bg_icon_slug:
            bg_img = get_icon(bg_icon_slug, self.rect["width"], self.rect["height"], color)
            if bg_img:
                mask = bg_img if bg_img.mode == 'RGBA' else None
                image.paste(bg_img, (self.rect["x"], self.rect["y"]), mask)
                
        icon_img = get_icon(icon_slug, self.rect["width"], self.rect["height"], color)
        if icon_img:
            mask = icon_img if icon_img.mode == 'RGBA' else None
            image.paste(icon_img, (self.rect["x"], self.rect["y"]), mask)

    def info(self) -> dict:
        info = super().info()
        info["fields"].extend([
            {"name": "type", "value": "list:weather,temperature,winddirection"},
            {"name": "color", "value": "color"}
        ])
        return info
