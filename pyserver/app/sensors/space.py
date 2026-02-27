import psutil
import os
from .base import BaseSensor
from typing import Any, Dict

class SpaceSensor(BaseSensor):
    def __init__(self, name: str, config: Dict[str, Any] = None):
        super().__init__(name, config)
        self.mount_point = self.config.get("mount_point", "/")
        self.max_points = self.config.get("max_points", 300)
        self.history_used = [0] * self.max_points

    async def sample(self) -> Dict[str, Any]:
        try:
            usage = psutil.disk_usage(self.mount_point)
            used_percent = usage.percent
            
            self.history_used.append(used_percent)
            self.history_used.pop(0)
            
            return {
                "used_percent": used_percent,
                "free_percent": 100 - used_percent,
                "used_mb": usage.used / (1024 * 1024),
                "total_mb": usage.total / (1024 * 1024),
                "history_used": ",".join(map(str, self.history_used))
            }
        except Exception:
            return {"used_percent": 0}

    def settings(self) -> dict:
        settings = super().settings()
        settings.update({
            "description": "disk space monitor",
            "fields": [
                {"name": "max_points", "type": "number", "value": 300},
                {"name": "mount_point", "type": "string", "value": "/"}
            ]
        })
        return settings
