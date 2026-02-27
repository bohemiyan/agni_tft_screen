from .app.core.config import Config
import os
import json

def create_sample_files():
    pyserver_dir = "c:\\Users\\Chirag\\Desktop\\agni_tft_screen\\pyserver"
    config_file = os.path.join(pyserver_dir, "config.json")
    
    sample_config = {
        "poll": 1000,
        "canvas": {"width": 320, "height": 170},
        "theme_data": {
            "screens": [
                {
                    "id": 1,
                    "name": "Default",
                    "widgets": [
                        {
                            "name": "text",
                            "value": "cpu_usage",
                            "format": "CPU: {:.1f}%",
                            "rect": {"x": 10, "y": 10, "width": 100, "height": 20},
                            "color": "#00FF00"
                        },
                        {
                            "name": "text",
                            "value": "memory",
                            "format": "MEM: {:.1f}%",
                            "rect": {"x": 10, "y": 40, "width": 100, "height": 20},
                            "color": "#0000FF"
                        }
                    ]
                }
            ]
        }
    }
    
    if not os.path.exists(config_file):
        with open(config_file, "w") as f:
            json.dump(sample_config, f, indent=4)
        print(f"Created sample config at {config_file}")

if __name__ == "__main__":
    create_sample_files()
