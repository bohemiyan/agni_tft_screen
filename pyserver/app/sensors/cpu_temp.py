import time
import logging
from typing import Dict, Any
from app.sensors.base import BaseSensor

try:
    import psutil
except ImportError:
    psutil = None

logger = logging.getLogger(__name__)

class CPUTempSensor(BaseSensor):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_points = config.get("max_points", 300)
        self.fahrenheit = config.get("fahrenheit", dict()).get("value", False) if isinstance(config.get("fahrenheit"), dict) else config.get("fahrenheit", False)
        
        self.history = [0] * self.max_points
        self.last_sampled = 0
        self.max_temp = 0.0
        self.min_temp = 0.0

    @classmethod
    def info(cls) -> dict:
        return {
            "name": "cpu_temp",
            "description": "cpu temp monitor",
            "icon": "pi-sun",
            "multiple": False,
            "ident": [],
            "fields": [
                {"name": "max_points", "type": "number", "value": 300},
                {"name": "fahrenheit", "type": "boolean", "value": True},
            ]
        }

    def _celsius_to_fahrenheit(self, c: float) -> float:
        return (c * 9/5) + 32

    async def sample(self) -> dict:
        current_time = int(time.time() * 1000)
        # Using a default rate logic or just sampling on every loop, Worker handles rate inherently mostly
        
        temp_c = 0.0
        
        # Use psutil on platforms where it's supported (Linux, sometimes Windows)
        if psutil and hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                # Look for coretemp first
                if "coretemp" in temps and temps["coretemp"]:
                    temp_c = temps["coretemp"][0].current
                else:
                    # Grab the first available temperature sensor
                    for name, entries in temps.items():
                        if entries:
                            temp_c = entries[0].current
                            break
                            
        final_temp = self._celsius_to_fahrenheit(temp_c) if self.fahrenheit else temp_c
        
        if self.max_temp == 0.0:
            self.max_temp = 230.0 if self.fahrenheit else 105.0
        if self.min_temp == 0.0:
            self.min_temp = 70.0 if self.fahrenheit else 21.0
            
        self.history.append(int(final_temp))
        if len(self.history) > self.max_points:
            self.history.pop(0)

        self._last_value = {
            "temp": self.history[-1],
            "history": self.history.copy(),
            "min": self.min_temp,
            "max": self.max_temp,
            "unit": "F" if self.fahrenheit else "C"
        }
        
        return self._last_value
