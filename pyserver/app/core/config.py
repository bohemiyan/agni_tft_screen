import json
import os
from typing import Any, Dict
from .models import Theme

class Config:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config_dir = os.path.dirname(os.path.abspath(config_path))
        self.data: Dict[str, Any] = {}
        self.theme: Theme = None
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
                
            theme_rel_path = self.data.get("theme")
            if theme_rel_path:
                theme_abs_path = os.path.join(self.config_dir, theme_rel_path)
                if os.path.exists(theme_abs_path):
                    if theme_abs_path.endswith('.py'):
                        namespace = {}
                        with open(theme_abs_path, 'r') as f:
                            exec(f.read(), namespace)
                        self.theme = Theme(**namespace.get('THEME', {}))
                    else:
                        with open(theme_abs_path, 'r') as tf:
                            theme_data = json.load(tf)
                            self.theme = Theme(**theme_data)
                else:
                    self.theme = Theme()
            else:
                self.theme = Theme()
        else:
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

    def save(self):
        # Save theme separate from main config
        if self.theme:
            theme_rel_path = self.data.get("theme")
            if theme_rel_path:
                theme_abs_path = os.path.join(self.config_dir, theme_rel_path)
                if theme_abs_path.endswith('.py'):
                    import pprint
                    with open(theme_abs_path, 'w') as tf:
                        tf.write("# Automatically saved Python Theme configuration\n\nTHEME = ")
                        tf.write(pprint.pformat(self.theme.model_dump(), indent=4, width=120))
                        tf.write("\n")
                else:
                    with open(theme_abs_path, 'w') as tf:
                        json.dump(self.theme.model_dump(), tf, indent=4)
            
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

