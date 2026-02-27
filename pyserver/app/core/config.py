import json
import os
from typing import Any, Dict

class Config:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_dir = os.path.dirname(os.path.abspath(config_path))
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            if self.config_path.endswith('.py'):
                namespace = {}
                with open(self.config_path, 'r') as f:
                    exec(f.read(), namespace)
                self.data = namespace.get('CONFIG', {})
            else:
                with open(self.config_path, 'r') as f:
                    self.data = json.load(f)
        else:
            # Seed default system configuration
            self.data = {
                "poll": 1000,
                "rotation_interval": 60000,
                "listen": "0.0.0.0:1234",
                "canvas": {"width": 320, "height": 170},
                "device": "1-8:1.1",
                "led_config": {"device": "/dev/ttyUSB0", "intensity": 3, "speed": 3, "theme": 5}
            }
            self.save()

    def save(self):
        if self.config_path.endswith('.py'):
            import pprint
            with open(self.config_path, 'w') as f:
                f.write("# Automatically saved Python configuration\n\nCONFIG = ")
                f.write(pprint.pformat(self.data, indent=4, width=120))
                f.write("\n")
        else:
            with open(self.config_path, 'w') as f:
                json.dump(self.data, f, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value

