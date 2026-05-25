import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/ai-news-summarizer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "ollama_url": "http://localhost:11434",
    "selected_model": "",
    "time_range": 2,  # 2 per oggi e ieri, 1 solo per oggi
    "theme": "Dark",
    "feeds": ["europe", "north_america"],  # Lista di feed geografici abilitati
    "max_news_count": 15,  # Numero massimo di notizie da mostrare
    "last_search_topic": "Intelligenza Artificiale"
}

def get_config_path():
    """Returns the path to the config file, creating the directory if it doesn't exist."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    return CONFIG_FILE

def load_config():
    """Loads config from the JSON file, or returns the default config if it doesn't exist."""
    path = get_config_path()
    if not os.path.exists(path):
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
            
            # Map old feeds to new continent feeds
            if "feeds" in config:
                mapped_feeds = []
                for f in config["feeds"]:
                    if f == "global_en" and "north_america" not in mapped_feeds:
                        mapped_feeds.append("north_america")
                    elif f == "asia_zh" and "asia" not in mapped_feeds:
                        mapped_feeds.append("asia")
                    elif f == "italy_it" and "europe" not in mapped_feeds:
                        mapped_feeds.append("europe")
                    elif f in ["north_america", "south_america", "europe", "asia", "africa", "oceania"]:
                        if f not in mapped_feeds:
                            mapped_feeds.append(f)
                if not mapped_feeds:
                    mapped_feeds = ["europe", "north_america"]
                config["feeds"] = mapped_feeds

            # Ensure all default keys exist
            for key, val in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = val
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Saves the config dictionary to the JSON file."""
    path = get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False
