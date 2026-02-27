import os
import sys

# Add the project root to sys.path to allow relative imports in main.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import Config

def test_config():
    pyserver_dir = "c:\\Users\\Chirag\\Desktop\\agni_tft_screen\\pyserver"
    config_file = os.path.join(pyserver_dir, "config.py")
    
    print(f"Loading config from {config_file}")
    try:
        config = Config(config_file)
        print("Config loaded successfully!")
        print(f"Theme Orientation: {config.theme.orientation}")
        print(f"Number of Screens: {len(config.theme.screens)}")
        if config.theme.screens:
            print(f"Widgets on Screen 1: {len(config.theme.screens[0].widgets)}")
    except Exception as e:
        print(f"Failed to load config: {e}")

if __name__ == "__main__":
    test_config()
