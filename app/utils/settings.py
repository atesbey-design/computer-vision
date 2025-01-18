import os
import json
from pathlib import Path


class Settings:
    def __init__(self):
        """Initialize settings with default values."""
        self.settings_dir = self.get_settings_directory_path()
        self.settings_file = self.settings_dir / "settings.json"
        
        # Create settings directory if it doesn't exist
        if not self.settings_dir.exists():
            self.settings_dir.mkdir(parents=True)
            
        # Default settings
        self.default_settings = {
            "gemini_api_key": "AIzaSyA3AWgsGyy-IrmNAlFnCDqSlsdYTImjbhM",  # Will be set through UI
            "play_sound_on_completion": True,
            "default_model": "gemini",
            "keyboard_shortcuts": {
                "send_request": "Control-Return",
                "stop_request": "Escape"
            }
        }
        
        # Load or create settings file
        if not self.settings_file.exists():
            self.save_settings_to_file(self.default_settings)
            
    def get_settings_directory_path(self) -> Path:
        """Get the path to the settings directory."""
        home = Path.home()
        return home / ".computer-use-gemini"
        
    def get_dict(self) -> dict:
        """Get the current settings as a dictionary."""
        return self.load_settings_from_file()
        
    def save_settings_to_file(self, settings_dict: dict) -> None:
        """Save settings to the settings file."""
        try:
            # Merge with existing settings to preserve other values
            existing_settings = self.load_settings_from_file()
            existing_settings.update(settings_dict)
            
            with open(self.settings_file, "w") as f:
                json.dump(existing_settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def load_settings_from_file(self) -> dict:
        """Load settings from the settings file."""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r") as f:
                    settings = json.load(f)
                # Ensure all default settings exist
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
            return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy() 