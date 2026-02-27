import psutil
import time
from .base import BaseSensor
from typing import Any, Dict

class NetworkSensor(BaseSensor):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.interface = self.config.get("interface", "enp2s0")
        self.max_points = self.config.get("max_points", 300)
        self.history_rx = [0] * self.max_points
        self.history_tx = [0] * self.max_points
        self.last_io = psutil.net_io_counters(pernic=True).get(self.interface)
        self.last_time = time.time()

    async def sample(self) -> Dict[str, Any]:
        now = time.time()
        io = psutil.net_io_counters(pernic=True).get(self.interface)
        dt = now - self.last_time
        
        if io and self.last_io and dt > 0:
            rx_speed = (io.bytes_recv - self.last_io.bytes_recv) / dt
            tx_speed = (io.bytes_sent - self.last_io.bytes_sent) / dt
            
            self.history_rx.append(rx_speed)
            self.history_rx.pop(0)
            self.history_tx.append(tx_speed)
            self.history_tx.pop(0)
            
            self.last_io = io
            self.last_time = now
            
            # Simple representation for now, analogous to Node.js format strings
            return {
                "rx": rx_speed,
                "tx": tx_speed,
                "rx_history": ",".join(map(str, self.history_rx)),
                "tx_history": ",".join(map(str, self.history_tx))
            }
        return {"rx": 0, "tx": 0}

    def settings(self) -> dict:
        settings = super().settings()
        settings.update({
            "description": "monitor nic statistics",
            "fields": [
                {"name": "max_points", "type": "number", "value": 300},
                {"name": "interface", "type": "string", "value": "enp2s0"}
            ]
        })
        return settings
