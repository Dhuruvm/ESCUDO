import json
import os
from datetime import datetime

# Directory for storing database files
DB_DIR = "data"
os.makedirs(DB_DIR, exist_ok=True)

# Database files
WARNINGS_FILE = os.path.join(DB_DIR, "warnings.json")
MUTES_FILE = os.path.join(DB_DIR, "mutes.json")

# Ensure database files exist
def ensure_db_files():
    files = {
        WARNINGS_FILE: {"guilds": {}},
        MUTES_FILE: {"guilds": {}}
    }
    
    for file_path, default_data in files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=4)

ensure_db_files()

# File operations
def load_db(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        default_data = {"guilds": {}}
        save_db(file_path, default_data)
        return default_data

def save_db(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Warning system
def add_warning(guild_id, user_id, moderator_id, reason):
    data = load_db(WARNINGS_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = {}
    
    if user_id not in data["guilds"][guild_id]:
        data["guilds"][guild_id][user_id] = []
    
    warning_id = len(data["guilds"][guild_id][user_id]) + 1
    
    data["guilds"][guild_id][user_id].append({
        "id": warning_id,
        "moderator_id": str(moderator_id),
        "reason": reason,
        "timestamp": datetime.now().timestamp()
    })
    
    save_db(WARNINGS_FILE, data)
    return warning_id

def get_warnings(guild_id, user_id):
    data = load_db(WARNINGS_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"] or user_id not in data["guilds"][guild_id]:
        return []
    
    return data["guilds"][guild_id][user_id]

def remove_warning(guild_id, user_id, warning_id):
    data = load_db(WARNINGS_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"] or user_id not in data["guilds"][guild_id]:
        return False
    
    for i, warning in enumerate(data["guilds"][guild_id][user_id]):
        if warning["id"] == warning_id:
            data["guilds"][guild_id][user_id].pop(i)
            save_db(WARNINGS_FILE, data)
            return True
    
    return False

def clear_warnings(guild_id, user_id):
    data = load_db(WARNINGS_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"] or user_id not in data["guilds"][guild_id]:
        return False
    
    data["guilds"][guild_id][user_id] = []
    save_db(WARNINGS_FILE, data)
    return True

# Mute system
def add_mute(guild_id, user_id, moderator_id, reason, expire_time=None):
    data = load_db(MUTES_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = {}
    
    data["guilds"][guild_id][user_id] = {
        "moderator_id": str(moderator_id),
        "reason": reason,
        "timestamp": datetime.now().timestamp(),
        "expire_time": expire_time
    }
    
    save_db(MUTES_FILE, data)
    return True

def remove_mute(guild_id, user_id):
    data = load_db(MUTES_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"] or user_id not in data["guilds"][guild_id]:
        return False
    
    del data["guilds"][guild_id][user_id]
    save_db(MUTES_FILE, data)
    return True

def is_muted(guild_id, user_id):
    data = load_db(MUTES_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"] or user_id not in data["guilds"][guild_id]:
        return False
    
    mute_data = data["guilds"][guild_id][user_id]
    if mute_data.get("expire_time") is not None:
        if datetime.now().timestamp() > mute_data["expire_time"]:
            remove_mute(guild_id, user_id)
            return False
    
    return True

def get_expired_mutes():
    data = load_db(MUTES_FILE)
    expired_mutes = []
    current_time = datetime.now().timestamp()
    
    for guild_id, guild_data in data["guilds"].items():
        for user_id, mute_data in list(guild_data.items()):
            if mute_data.get("expire_time") is not None and current_time > mute_data["expire_time"]:
                expired_mutes.append((guild_id, user_id))
                del data["guilds"][guild_id][user_id]
    
    if expired_mutes:
        save_db(MUTES_FILE, data)
    
    return expired_mutes
