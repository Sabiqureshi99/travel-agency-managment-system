import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigService:
    def __init__(self, config_path: str = "data/config.json"):
        self.config_path = config_path
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        path = Path(self.config_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "company": {
                    "name": "Hamza Travel & Tours Nawabshah",
                    "address": "Tayaba Center, Nawabshah, Sindh, Pakistan",
                    "phone": "",
                    "email": "",
                    "website": "",
                    "ntn": "",
                    "strn": ""
                },
                "preferences": {
                    "theme": "dark",
                    "currency": "PKR"
                }
            }
            self.save_config(default_config)

    def load_config(self) -> dict:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}

    def save_config(self, config_data: dict) -> bool:
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            return False
