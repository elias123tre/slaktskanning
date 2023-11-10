import configparser
import os
from pathlib import Path
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


CONFIG_PATH = (
    Path(os.getenv("APPDATA")) / "slaktskanning.ini"
    if os.name == "nt"
    else Path.home() / ".slaktskanning.ini"
)


def get_config():
    """Save the scan folder in a config file in AppData/slaktskanning.ini on windows and ~/.slaktskanning.ini to persist between sessions"""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    return config


def save_config(new_config: dict):
    """Save the scan folder in a config file in AppData/slaktskanning.ini on windows and ~/.slaktskanning.ini to persist between sessions"""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH, encoding="utf-8")
    for key, value in new_config.items():
        if not config.has_section("General"):
            config.add_section("General")
        config.set("General", key, value)
    with open(CONFIG_PATH, "w", encoding="utf-8") as config_file:
        config.write(config_file)
