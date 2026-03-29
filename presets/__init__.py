import importlib
import os

PRESETS = {}

def load_presets():
    preset_dir = os.path.dirname(__file__)
    for filename in os.listdir(preset_dir):
        if filename.endswith(".py") and filename != "__init__.py" and filename != "generic.py":
            module_name = filename[:-3]
            module = importlib.import_module(f"presets.{module_name}")
            if hasattr(module, "PRESET_NAME") and hasattr(module, "get_data"):
                PRESETS[module.PRESET_NAME] = module.get_data

load_presets()