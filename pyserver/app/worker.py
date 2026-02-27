import asyncio
import logging
import time
from PIL import Image, ImageDraw
from .core.hardware.lcd import LCDDevice
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
        if name == "text":
            return TextWidget(name, config)
        elif name == "bar_chart":
            return BarChartWidget(name, config)
        elif name == "image":
            return ImageWidget(name, config)
        elif name == "line_chart":
            return LineChartWidget(name, config)
        elif name == "doughnut_chart":
            return DoughnutChartWidget(name, config)
        elif name == "custom_bar":
            return CustomBarWidget(name, config)
        elif name == "iconify":
            return IconifyWidget(name, config)
        elif name == "weather_icon":
            return WeatherIconWidget(name, config)
        return None

    async def start(self):
        self.running = True
        self.lcd.open()
        logger.info("Worker started")
        
        while self.running:
            try:
                # 1. Sample sensors
                readings = {}
                for name, sensor in self.sensors.items():
                    readings[name] = await sensor.sample()

                # 2. Clear Canvas
                self.draw_context.rectangle(
                    [0, 0, self.canvas.width, self.canvas.height], 
                    fill="black"
                )

                # 3. Handle rotation & Draw Widgets
                theme_id = self.registry.active_theme_id if self.registry else None
                rotation_interval = self.config.get("rotation_interval", 60000) / 1000.0
                
                if theme_id and theme_id in self.registry.themes:
                    # Modular flow
                    theme_node = self.registry.themes[theme_id]
                    if theme_node.rotation_interval:
                        rotation_interval = theme_node.rotation_interval / 1000.0
                        
                    screen_ids = theme_node.screen_ids
                    if screen_ids:
                        if rotation_interval > 0:
                            if time.time() - self.last_rotate_time > rotation_interval:
                                self.screen_index = (self.screen_index + 1) % len(screen_ids)
                                self.last_rotate_time = time.time()
                                
                        if self.screen_index >= len(screen_ids):
                            self.screen_index = 0
                            
                        active_screen_id = screen_ids[self.screen_index]
                        if active_screen_id in self.registry.screens:
                            active_screen = self.registry.screens[active_screen_id]
                            for w_id in active_screen.widget_ids:
                                if w_id in self.registry.widgets:
                                    w_node = self.registry.widgets[w_id]
                                    w = self._get_widget(w_node.type, {"id": w_node.id, **w_node.properties, "rect": w_node.rect})
                                    if w:
                                        reading = None
                                        if w_node.sensor_id and w_node.sensor_id in self.registry.sensors:
                                            s_node = self.registry.sensors[w_node.sensor_id]
                                            reading = readings.get(s_node.type, None)  # Assume standard naming temp mappings
                                        
                                        # Simple fallback extraction logic
                                        if isinstance(reading, dict):
                                            if "used_percent" in reading: reading = reading["used_percent"]
                                            elif "rx_history" in reading: reading = reading["rx_history"]
                                            elif "temp" in reading: reading = reading["temp"]
                                            elif "watts" in reading: reading = reading["watts"]
                                        w.draw(self.canvas, self.draw_context, reading, 0, 100)
                                        w.draw(self.canvas, self.draw_context, reading, 0, 100)
                # 4. Update LCD
                pixel_data = self.canvas.tobytes() 
                await self.lcd.redraw(pixel_data)

            except Exception as e:
                logger.error(f"Error in worker loop: {e}", exc_info=True)

            await asyncio.sleep(self.config.get("poll", 1000) / 1000.0)

    async def stop(self):
        self.running = False
        self.lcd.close()
        logger.info("Worker stopped")
