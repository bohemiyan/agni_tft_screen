import asyncio
import logging
import time
from PIL import Image, ImageDraw, ImageFont
from .core.hardware.lcd import LCDDevice
from .core.hardware.led import LEDDevice
from .core.config import Config
from .sensors.cpu_usage import CPUUsageSensor
from .sensors.cpu_temp import CPUTempSensor
from .sensors.cpu_power import CPUPowerSensor
from .sensors.clock import ClockSensor
from .sensors.calendar import CalendarSensor
from .sensors.memory import MemorySensor
from .sensors.network import NetworkSensor
from .sensors.space import SpaceSensor
from .sensors.weather import WeatherSensor
from .widgets.text import TextWidget
from .widgets.bar_chart import BarChartWidget
from .widgets.image import ImageWidget
from .widgets.line_chart import LineChartWidget
from .widgets.doughnut_chart import DoughnutChartWidget
from .widgets.custom_bar import CustomBarWidget
from .widgets.iconify import IconifyWidget
from .widgets.weather_icon import WeatherIconWidget

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, config: Config, registry=None):
        self.config = config
        self.registry = registry
        self.lcd = LCDDevice()
        self.led = LEDDevice()
        self.running = False
        self.sensors = {}
        self.canvas = None
        self.screen_index = 0
        self.last_rotate_time = time.time()
        self._initialize_components()

    def _initialize_components(self):
        self.sensors["cpu_usage"] = CPUUsageSensor("cpu_usage")
        self.sensors["cpu_temp"] = CPUTempSensor({"max_points": 300})
        self.sensors["cpu_power"] = CPUPowerSensor({"max_points": 300})
        self.sensors["clock"] = ClockSensor("clock")
        self.sensors["calendar"] = CalendarSensor("calendar")
        self.sensors["memory"] = MemorySensor("memory")
        self.sensors["network"] = NetworkSensor("network")
        self.sensors["space"] = SpaceSensor("space")
        self.sensors["weather"] = WeatherSensor("weather")
        
        # Initialize Canvas
        canvas_cfg = self.config.get("canvas", {"width": 320, "height": 170})
        self.canvas = Image.new("RGB", (canvas_cfg["width"], canvas_cfg["height"]), "black")
        self.draw_context = ImageDraw.Draw(self.canvas)

    def _get_widget(self, name, config):
        widget_map = {
            "text": TextWidget,
            "bar_chart": BarChartWidget,
            "image": ImageWidget,
            "line_chart": LineChartWidget,
            "doughnut_chart": DoughnutChartWidget,
            "custom_bar": CustomBarWidget,
            "iconify": IconifyWidget,
            "weather_icon": WeatherIconWidget
        }
        widget_class = widget_map.get(name)
        return widget_class(name, config) if widget_class else None

    async def _update_leds(self, led_cfg):
        """Update LED strip with error handling."""
        try:
            device_path = led_cfg.get("device", "/dev/ttyUSB0")
            theme = led_cfg.get("theme", 5)
            intensity = led_cfg.get("intensity", 3)
            speed = led_cfg.get("speed", 3)
            
            await self.led.set_strip(theme, intensity, speed, device_path)
        except Exception as e:
            logger.error(f"LED update failed: {e}")

    def _extract_reading(self, reading, sensor_type):
        """Safely extract numeric value from sensor reading based on sensor type."""
        if reading is None:
            return None
            
        if isinstance(reading, (int, float)):
            return reading
            
        if isinstance(reading, dict):
            # Map sensor types to their typical value keys
            extraction_map = {
                "cpu_usage": ["used_percent", "percent", "value"],
                "cpu_temp": ["temp", "temperature", "value"],
                "cpu_power": ["watts", "power", "value"],
                "memory": ["used_percent", "percent", "value"],
                "network": ["rx_history", "tx_history", "speed"],
                "weather": ["temp", "temperature", "value"]
            }
            
            keys_to_try = extraction_map.get(sensor_type, ["value"])
            for key in keys_to_try:
                if key in reading:
                    return reading[key]
                    
            # Fallback: return first numeric value found
            for key, value in reading.items():
                if isinstance(value, (int, float)):
                    return value
                    
        return reading

    async def start(self):
        self.running = True
        self.lcd.open()
        logger.info("Worker started")
        
        # --- BOOT SEQUENCE ---
        try:
            # 1. Fire Rainbow LEDs
            led_cfg = self.config.get("led_config", {})
            if led_cfg:
                await self._update_leds({**led_cfg, "theme": 1, "intensity": 5, "speed": 3})
            
            # 2. Draw "Welcome" Splash 
            self.draw_context.rectangle([0, 0, self.canvas.width, self.canvas.height], fill="#060a10")
            try:
                font = ImageFont.truetype("arialbd.ttf", 24)
            except IOError:
                font = ImageFont.load_default()
                
            text = "Welcome...."
            bbox = self.draw_context.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            x = (self.canvas.width - text_w) / 2
            y = (self.canvas.height - text_h) / 2
            
            self.draw_context.text((x, y), text, fill="#00d4ff", font=font)
            
            # 3. Push Splash to LCD
            await self.lcd.redraw(self.canvas.tobytes())
            
            # 4. Hold Splash for 10 Seconds
            await asyncio.sleep(10)
            
        except Exception as e:
            logger.error(f"Failed to play Welcome sequence: {e}")
        # --- END BOOT SEQUENCE ---

        # LED update tracking
        last_led_update = time.time()
        led_update_interval = 5.0  # Update LEDs every 5 seconds minimum

        while self.running:
            try:
                # 1. Sample sensors
                readings = {}
                for name, sensor in self.sensors.items():
                    try:
                        readings[name] = await sensor.sample()
                    except Exception as e:
                        logger.error(f"Sensor {name} sampling failed: {e}")
                        readings[name] = None

                # 2. Clear Canvas
                self.draw_context.rectangle(
                    [0, 0, self.canvas.width, self.canvas.height], 
                    fill="#060a10"
                )

                # 3. Handle rotation & Draw Widgets
                theme_id = self.registry.active_theme_id if self.registry else None
                
                if theme_id and theme_id in self.registry.themes:
                    theme_node = self.registry.themes[theme_id]
                    
                    # Get rotation interval (default 60 seconds)
                    rotation_interval = self.config.get("rotation_interval", 60000) / 1000.0
                    if theme_node.rotation_interval is not None:
                        rotation_interval = theme_node.rotation_interval / 1000.0
                    
                    screen_ids = theme_node.screen_ids or []
                    
                    if screen_ids:
                        # Handle screen rotation
                        should_rotate = (rotation_interval > 0 and 
                                       time.time() - self.last_rotate_time > rotation_interval)
                        
                        if should_rotate:
                            self.screen_index = (self.screen_index + 1) % len(screen_ids)
                            self.last_rotate_time = time.time()
                            logger.debug(f"Rotated to screen {self.screen_index}")
                        
                        # Ensure index is valid
                        self.screen_index = self.screen_index % len(screen_ids)
                        active_screen_id = screen_ids[self.screen_index]
                        
                        # Draw widgets for active screen
                        if active_screen_id in self.registry.screens:
                            active_screen = self.registry.screens[active_screen_id]
                            
                            for w_id in active_screen.widget_ids:
                                if w_id not in self.registry.widgets:
                                    continue
                                    
                                w_node = self.registry.widgets[w_id]
                                w_config = {"id": w_node.id, **w_node.properties, "rect": w_node.rect}
                                w = self._get_widget(w_node.type, w_config)
                                
                                if not w:
                                    continue
                                
                                # Get reading for this widget's sensor
                                reading = None
                                if w_node.sensor_id and w_node.sensor_id in self.registry.sensors:
                                    s_node = self.registry.sensors[w_node.sensor_id]
                                    # Use sensor type to lookup in readings dict
                                    reading = readings.get(s_node.type)
                                
                                # Extract numeric value safely
                                extracted = self._extract_reading(reading, s_node.type if s_node else None)
                                
                                # Draw widget
                                try:
                                    w.draw(self.canvas, self.draw_context, extracted, 0, 100)
                                except Exception as e:
                                    logger.error(f"Widget {w_id} draw failed: {e}")

                # 4. Update LEDs periodically (not just on rotation)
                led_cfg = self.config.get("led_config")
                if led_cfg and (time.time() - last_led_update > led_update_interval):
                    asyncio.create_task(self._update_leds(led_cfg))
                    last_led_update = time.time()

                # 5. Update LCD
                await self.lcd.redraw(self.canvas.tobytes())

            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

            await asyncio.sleep(self.config.get("poll", 1000) / 1000.0)

    async def stop(self):
        self.running = False
        # Turn off LEDs on stop
        try:
            led_cfg = self.config.get("led_config", {})
            if led_cfg:
                await self.led.set_strip(4, 5, 5, led_cfg.get("device", "/dev/ttyUSB0"))
        except Exception as e:
            logger.error(f"Failed to turn off LEDs: {e}")
        
        self.lcd.close()
        logger.info("Worker stopped")