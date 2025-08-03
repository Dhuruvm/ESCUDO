
import json
import os
from datetime import datetime

# Directory for storing database files
DB_DIR = "data"
os.makedirs(DB_DIR, exist_ok=True)

# Database file for shadow clones
SHADOWCLONES_FILE = os.path.join(DB_DIR, "shadowclones.json")

def ensure_shadowclones_db():
    """Ensure the shadowclones database file exists"""
    if not os.path.exists(SHADOWCLONES_FILE):
        with open(SHADOWCLONES_FILE, 'w') as f:
            json.dump({"clones": {}}, f, indent=4)

ensure_shadowclones_db()

def load_shadowclones_db():
    """Load shadowclones database"""
    try:
        with open(SHADOWCLONES_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        default_data = {"clones": {}}
        save_shadowclones_db(default_data)
        return default_data

def save_shadowclones_db(data):
    """Save shadowclones database"""
    with open(SHADOWCLONES_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def create_shadowclone(user_id, channel_id, webhook_id, webhook_token, name, avatar_url, prefix):
    """Create a new shadow clone entry"""
    data = load_shadowclones_db()
    clone_key = f"{user_id}_{channel_id}"
    
    data["clones"][clone_key] = {
        "user_id": str(user_id),
        "channel_id": str(channel_id),
        "webhook_id": str(webhook_id),
        "webhook_token": webhook_token,
        "name": name,
        "avatar_url": avatar_url,
        "prefix": prefix,
        "created_at": datetime.now().timestamp(),
        "active": True
    }
    
    save_shadowclones_db(data)
    return True

def get_shadowclone(user_id, channel_id):
    """Get a shadow clone by user and channel"""
    data = load_shadowclones_db()
    clone_key = f"{user_id}_{channel_id}"
    return data["clones"].get(clone_key)

def get_shadowclone_by_channel(channel_id):
    """Get all shadow clones in a specific channel"""
    data = load_shadowclones_db()
    clones = []
    for clone_data in data["clones"].values():
        if clone_data["channel_id"] == str(channel_id) and clone_data["active"]:
            clones.append(clone_data)
    return clones

def update_shadowclone(user_id, channel_id, **updates):
    """Update a shadow clone"""
    data = load_shadowclones_db()
    clone_key = f"{user_id}_{channel_id}"
    
    if clone_key not in data["clones"]:
        return False
    
    for key, value in updates.items():
        if key in ["name", "avatar_url", "prefix"]:
            data["clones"][clone_key][key] = value
    
    data["clones"][clone_key]["updated_at"] = datetime.now().timestamp()
    save_shadowclones_db(data)
    return True

def delete_shadowclone(user_id, channel_id):
    """Delete a shadow clone"""
    data = load_shadowclones_db()
    clone_key = f"{user_id}_{channel_id}"
    
    if clone_key not in data["clones"]:
        return False
    
    del data["clones"][clone_key]
    save_shadowclones_db(data)
    return True

def deactivate_shadowclone(user_id, channel_id):
    """Deactivate a shadow clone (for when webhook is deleted)"""
    data = load_shadowclones_db()
    clone_key = f"{user_id}_{channel_id}"
    
    if clone_key not in data["clones"]:
        return False
    
    data["clones"][clone_key]["active"] = False
    save_shadowclones_db(data)
    return True

def get_user_shadowclones(user_id):
    """Get all shadow clones for a user"""
    data = load_shadowclones_db()
    user_clones = []
    for clone_data in data["clones"].values():
        if clone_data["user_id"] == str(user_id) and clone_data["active"]:
            user_clones.append(clone_data)
    return user_clones
