import time
import logging
import os
from typing import Dict, Any
from app.sensors.base import BaseSensor

logger = logging.getLogger(__name__)

class CPUPowerSensor(BaseSensor):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.max_points = config.get("max_points", 300)
        self.history = [0] * self.max_points
        self.last_sampled = 0
        self.previous_energy = None

    @classmethod
    def info(cls) -> dict:
        return {
            "name": "cpu_power",
            "description": "cpu power monitor",
            "icon": "pi-bolt",
            "multiple": False,
            "ident": [],
            "fields": [
                {"name": "max_points", "type": "number", "value": 300},
            ]
        }

    def _power_usage(self) -> float:
        base_dir = '/sys/class/powercap/'
        watts = 0.0
        
        if not os.path.exists(base_dir):
            return watts
            
        try:
            current_energy = []
            for d in os.listdir(base_dir):
                energy_path = os.path.join(base_dir, d, 'energy_uj')
                if os.path.exists(energy_path):
                    with open(energy_path, 'r') as f:
                        val = f.read().strip()
                        if val.isdigit():
                            current_energy.append(int(val))
                            
            if self.previous_energy and len(current_energy) == len(self.previous_energy):
                watts_sum = 0.0
                for i in range(len(current_energy)):
                    watts_sum += (current_energy[i] - self.previous_energy[i]) / 1000000.0
                watts = watts_sum
                
            self.previous_energy = current_energy
        except Exception as e:
            logger.error(f"Error reading cpu_power: {e}")
            
        return watts

    async def sample(self) -> dict:
        current_time_ms = int(time.time() * 1000)
        diff_ms = current_time_ms - self.last_sampled
        
        # We don't sample immediately on first boot so we can calculate delta next time
        if self.last_sampled == 0:
            self._power_usage() # seed previous
            watts = 0.0
        else:
            watts = self._power_usage()
            seconds = diff_ms / 1000.0
            if seconds > 1:
                watts = watts / seconds
                
        self.last_sampled = current_time_ms

        self.history.append(int(watts))
        if len(self.history) > self.max_points:
            self.history.pop(0)

        self._last_value = {
            "watts": self.history[-1],
            "history": self.history.copy(),
            "min": 0,
            "max": 28 # Arbitrary max from original code
        }
        
        return self._last_value
