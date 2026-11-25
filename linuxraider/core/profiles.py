"""Profile management and storage for LinuxRaider."""

import json
import os
from typing import Dict, List, Optional
from ..engine.curves import generate_tone_curve
from ..engine.icc_builder import ICCBuilder
from ..engine.window_watcher import DEFAULT_GAME_PATTERNS


DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/linuxraider")
PROFILES_DIR = os.path.join(DEFAULT_CONFIG_DIR, "profiles")
ICC_CACHE_DIR = os.path.join(DEFAULT_CONFIG_DIR, "icc")

BUILTIN_PROFILES = {
    "night_vision": {
        "name": "night_vision",
        "description": "Visión Nocturna - Elevación profunda de sombras",
        "shadow_boost": 0.85,
        "gamma": 1.40,
        "contrast": 1.00,
        "brightness": 1.20,
    },
    "neutral": {
        "name": "neutral",
        "description": "Estándar / Neutral",
        "shadow_boost": 0.0,
        "gamma": 1.0,
        "contrast": 1.0,
        "brightness": 1.0,
    },
}


class ProfileManager:
    """Manages profile loading, saving, and compiling into ICC files."""

    def __init__(self, config_dir: str = DEFAULT_CONFIG_DIR):
        self.config_dir = config_dir
        self.profiles_dir = os.path.join(config_dir, "profiles")
        self.icc_dir = os.path.join(config_dir, "icc")
        self.settings_path = os.path.join(config_dir, "settings.json")
        self.builder = ICCBuilder()
        self._ensure_dirs()
        self._install_builtins()

    def get_settings(self) -> Dict:
        """Load persistent application settings with defaults."""
        defaults = {
            "auto_detect_enabled": True,
            "auto_detect_patterns": DEFAULT_GAME_PATTERNS,
        }
        if not os.path.exists(self.settings_path):
            return defaults
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                defaults.update(loaded)
        except Exception:
            pass
        return defaults

    def save_settings(self, settings: Dict):
        """Persist application settings to disk."""
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)

    def _ensure_dirs(self):
        os.makedirs(self.profiles_dir, exist_ok=True)
        os.makedirs(self.icc_dir, exist_ok=True)

    def _install_builtins(self):
        for name, data in BUILTIN_PROFILES.items():
            path = os.path.join(self.profiles_dir, f"{name}.json")
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)

    def list_profiles(self) -> List[Dict]:
        profiles = []
        for file in sorted(os.listdir(self.profiles_dir)):
            if file.endswith(".json"):
                path = os.path.join(self.profiles_dir, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        profiles.append(data)
                except Exception:
                    continue
        return profiles

    def get_profile(self, name: str) -> Optional[Dict]:
        path = os.path.join(self.profiles_dir, f"{name}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_profile(
        self,
        name: str,
        shadow_boost: float,
        gamma: float,
        contrast: float,
        brightness: float = 1.0,
        description: str = "",
    ) -> Dict:
        data = {
            "name": name,
            "description": description or f"Custom profile {name}",
            "shadow_boost": shadow_boost,
            "gamma": gamma,
            "contrast": contrast,
            "brightness": brightness,
        }
        path = os.path.join(self.profiles_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return data

    def compile_profile_to_icc(self, profile_data: Dict, custom_filename: Optional[str] = None) -> str:
        name = custom_filename or profile_data.get("name", "custom")
        shadow_boost = float(profile_data.get("shadow_boost", 0.5))
        gamma = float(profile_data.get("gamma", 1.0))
        contrast = float(profile_data.get("contrast", 1.0))
        brightness = float(profile_data.get("brightness", 1.0))

        curve = generate_tone_curve(
            num_points=256,
            shadow_boost=shadow_boost,
            gamma=gamma,
            contrast=contrast,
            brightness=brightness,
        )

        icc_path = os.path.join(self.icc_dir, f"{name}.icc")

        self.builder.create_display_profile(
            curve_values=curve,
            output_filepath=icc_path,
            profile_desc=f"LinuxRaider - {name}",
        )

        return icc_path
