import os
import json
from datetime import datetime, timezone

ARCHIVE_DIR = os.path.expanduser("~/.config/ai-news-summarizer")
ARCHIVE_FILE = os.path.join(ARCHIVE_DIR, "archive.json")
MAX_ARCHIVE_DAYS = 7

def get_archive_path():
    """Returns the path to the archive file, creating the directory if needed."""
    if not os.path.exists(ARCHIVE_DIR):
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
    return ARCHIVE_FILE

def load_archive():
    """Loads archived news, cleans up items older than 7 days, and returns the list."""
    path = get_archive_path()
    if not os.path.exists(path):
        return []
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            items = json.load(f)
    except Exception:
        return []
    
    # Filter items: keep only those archived within the last 7 days
    now = datetime.now(timezone.utc)
    updated_items = []
    
    for item in items:
        archived_at_str = item.get("archived_at")
        if archived_at_str:
            try:
                archived_at = datetime.fromisoformat(archived_at_str)
                # Ensure it has timezone info
                if archived_at.tzinfo is None:
                    archived_at = archived_at.replace(tzinfo=timezone.utc)
                diff = now - archived_at
                if diff.days < MAX_ARCHIVE_DAYS:
                    updated_items.append(item)
            except Exception:
                # If timestamp is corrupt, keep it anyway
                updated_items.append(item)
        else:
            # If no archived_at timestamp, add one now and keep it
            item["archived_at"] = now.isoformat()
            updated_items.append(item)
            
    # Save the cleaned archive back if some items were removed
    if len(updated_items) < len(items):
        save_archive(updated_items)
        
    return updated_items

def save_archive(items):
    """Saves the archive list to the JSON file."""
    path = get_archive_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)
        return True
    except Exception:
        return False

def add_to_archive(news_item):
    """Adds a news item to the archive if it doesn't already exist."""
    items = load_archive()
    link = news_item.get("resolved_link") or news_item.get("google_link")
    title = news_item.get("title_original")
    
    exists = False
    for item in items:
        item_link = item.get("resolved_link") or item.get("google_link")
        if item_link == link or item.get("title_original") == title:
            exists = True
            break
            
    if not exists:
        new_item = news_item.copy()
        new_item["archived_at"] = datetime.now(timezone.utc).isoformat()
        items.append(new_item)
        save_archive(items)
        return True
    return False

def remove_from_archive(news_item):
    """Removes a news item from the archive by matching link or title."""
    items = load_archive()
    link = news_item.get("resolved_link") or news_item.get("google_link")
    title = news_item.get("title_original")
    
    updated_items = [
        item for item in items 
        if (item.get("resolved_link") or item.get("google_link")) != link and item.get("title_original") != title
    ]
    
    if len(updated_items) < len(items):
        save_archive(updated_items)
        return True
    return False

def is_archived(news_item):
    """Checks if a news item is already archived."""
    items = load_archive()
    link = news_item.get("resolved_link") or news_item.get("google_link")
    title = news_item.get("title_original")
    
    for item in items:
        item_link = item.get("resolved_link") or item.get("google_link")
        if item_link == link or item.get("title_original") == title:
            return True
    return False
