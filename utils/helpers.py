import discord
import json
import os
from datetime import datetime
import asyncio
from config import CONFIG

# File path for JSON storage
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# Data files
WHITELIST_FILE = os.path.join(DATA_DIR, "whitelist.json")
SERVER_CONFIG_FILE = os.path.join(DATA_DIR, "server_config.json")
JOIN_TO_CREATE_FILE = os.path.join(DATA_DIR, "join_to_create.json")
SELF_ROLES_FILE = os.path.join(DATA_DIR, "self_roles.json")
SNIPE_CACHE = {}  # In-memory cache for snipe feature

# Ensure data files exist
def ensure_data_files():
    files = {
        WHITELIST_FILE: {"guilds": {}},
        SERVER_CONFIG_FILE: {"guilds": {}},
        JOIN_TO_CREATE_FILE: {"channels": {}},
        SELF_ROLES_FILE: {"guilds": {}}
    }
    
    for file_path, default_data in files.items():
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump(default_data, f, indent=4)

ensure_data_files()

# General file operations
def load_json(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        default_data = {"guilds": {}} if "whitelist" in file_path or "server_config" in file_path or "self_roles" in file_path else {"channels": {}}
        save_json(file_path, default_data)
        return default_data

def save_json(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Server configuration helpers
def get_guild_config(guild_id):
    data = load_json(SERVER_CONFIG_FILE)
    guild_id = str(guild_id)
    
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = {
            "prefix": CONFIG["prefix"],
            "mod_roles": [],
            "admin_roles": [],
            "muted_role": None,
            "ignored_channels": [],
            "media_channels": [],
            "antinuke": {
                "enabled": True,
                "bypass_enabled": False
            },
            "nightmode": {
                "enabled": False,
                "start_hour": 22,
                "end_hour": 6
            }
        }
        save_json(SERVER_CONFIG_FILE, data)
    
    return data["guilds"][guild_id]

def update_guild_config(guild_id, config_data):
    data = load_json(SERVER_CONFIG_FILE)
    guild_id = str(guild_id)
    data["guilds"][guild_id] = config_data
    save_json(SERVER_CONFIG_FILE, data)

# Whitelist operations
def is_whitelisted(guild_id, user_id):
    data = load_json(WHITELIST_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"]:
        return False
    
    return user_id in data["guilds"][guild_id]

def add_to_whitelist(guild_id, user_id):
    data = load_json(WHITELIST_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = []
    
    if user_id not in data["guilds"][guild_id]:
        data["guilds"][guild_id].append(user_id)
        save_json(WHITELIST_FILE, data)
        return True
    return False

def remove_from_whitelist(guild_id, user_id):
    data = load_json(WHITELIST_FILE)
    guild_id, user_id = str(guild_id), str(user_id)
    
    if guild_id not in data["guilds"]:
        return False
    
    if user_id in data["guilds"][guild_id]:
        data["guilds"][guild_id].remove(user_id)
        save_json(WHITELIST_FILE, data)
        return True
    return False

def reset_whitelist(guild_id):
    data = load_json(WHITELIST_FILE)
    guild_id = str(guild_id)
    
    if guild_id in data["guilds"]:
        data["guilds"][guild_id] = []
        save_json(WHITELIST_FILE, data)
        return True
    return False

def get_whitelisted_users(guild_id):
    data = load_json(WHITELIST_FILE)
    guild_id = str(guild_id)
    
    if guild_id not in data["guilds"]:
        return []
    
    return data["guilds"][guild_id]

# Join to Create helpers
def get_join_to_create_config(guild_id):
    data = load_json(JOIN_TO_CREATE_FILE)
    guild_id = str(guild_id)
    
    if guild_id not in data["channels"]:
        data["channels"][guild_id] = {
            "setup_channel": None,
            "temp_channels": [],
            "category": None
        }
        save_json(JOIN_TO_CREATE_FILE, data)
    
    return data["channels"][guild_id]

def update_join_to_create_config(guild_id, config_data):
    data = load_json(JOIN_TO_CREATE_FILE)
    guild_id = str(guild_id)
    data["channels"][guild_id] = config_data
    save_json(JOIN_TO_CREATE_FILE, data)

def add_temp_channel(guild_id, channel_id):
    config = get_join_to_create_config(guild_id)
    if str(channel_id) not in config["temp_channels"]:
        config["temp_channels"].append(str(channel_id))
        update_join_to_create_config(guild_id, config)

def remove_temp_channel(guild_id, channel_id):
    config = get_join_to_create_config(guild_id)
    if str(channel_id) in config["temp_channels"]:
        config["temp_channels"].remove(str(channel_id))
        update_join_to_create_config(guild_id, config)

# Self Roles helpers
def get_self_roles(guild_id):
    data = load_json(SELF_ROLES_FILE)
    guild_id = str(guild_id)
    
    if guild_id not in data["guilds"]:
        data["guilds"][guild_id] = {
            "messages": {}
        }
        save_json(SELF_ROLES_FILE, data)
    
    return data["guilds"][guild_id]

def update_self_roles(guild_id, config_data):
    data = load_json(SELF_ROLES_FILE)
    guild_id = str(guild_id)
    data["guilds"][guild_id] = config_data
    save_json(SELF_ROLES_FILE, data)

# Snipe feature helpers
def add_snipe(channel_id, message):
    channel_id = str(channel_id)
    if channel_id not in SNIPE_CACHE:
        SNIPE_CACHE[channel_id] = []
    
    # Keep only the last 10 deleted messages
    if len(SNIPE_CACHE[channel_id]) >= 10:
        SNIPE_CACHE[channel_id].pop(0)
    
    SNIPE_CACHE[channel_id].append({
        'content': message.content,
        'author': str(message.author),
        'author_id': message.author.id,
        'timestamp': message.created_at.timestamp(),
        'has_attachments': len(message.attachments) > 0
    })

def get_snipe(channel_id):
    channel_id = str(channel_id)
    if channel_id in SNIPE_CACHE and SNIPE_CACHE[channel_id]:
        return SNIPE_CACHE[channel_id][-1]
    return None

# Permission checks
def is_mod(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    
    config = get_guild_config(ctx.guild.id)
    mod_roles = config.get("mod_roles", [])
    
    for role in ctx.author.roles:
        if str(role.id) in mod_roles:
            return True
    
    return False

def is_admin(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    
    config = get_guild_config(ctx.guild.id)
    admin_roles = config.get("admin_roles", [])
    
    for role in ctx.author.roles:
        if str(role.id) in admin_roles:
            return True
    
    return False

def is_owner(ctx):
    if ctx.author.id in CONFIG["owner_ids"]:
        return True
    
    guild_id = str(ctx.guild.id)
    if guild_id in CONFIG["extra_owners"] and ctx.author.id in CONFIG["extra_owners"][guild_id]:
        return True
    
    return False

# Antinuke helpers
def is_nightmode_active(guild_id):
    config = get_guild_config(guild_id)
    nightmode = config.get("nightmode", {})
    
    if not nightmode.get("enabled", False):
        return False
    
    now = datetime.now()
    current_hour = now.hour
    
    start_hour = nightmode.get("start_hour", 22)
    end_hour = nightmode.get("end_hour", 6)
    
    if start_hour < end_hour:
        return start_hour <= current_hour < end_hour
    else:
        return current_hour >= start_hour or current_hour < end_hour

# Utils
async def temp_message(ctx, content, seconds=5):
    """Send a temporary message that deletes itself after a specified time"""
    msg = await ctx.send(content)
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except discord.HTTPException:
        pass
import json
import os
from config import CONFIG

def ensure_data_files():
    """Ensure all required data files exist"""
    os.makedirs("data", exist_ok=True)
    
    files = [
        "data/server_config.json",
        "data/warnings.json", 
        "data/mutes.json",
        "data/join_to_create.json",
        "data/self_roles.json",
        "data/whitelist.json"
    ]
    
    for file_path in files:
        if not os.path.exists(file_path):
            with open(file_path, 'w') as f:
                json.dump({}, f)

def is_owner(ctx):
    """Check if user is bot owner"""
    return ctx.author.id in CONFIG["owner_ids"]

def is_admin(ctx):
    """Check if user has admin permissions"""
    return ctx.author.guild_permissions.administrator or is_owner(ctx)

def is_mod(ctx):
    """Check if user has mod permissions"""
    return (ctx.author.guild_permissions.manage_messages or 
            ctx.author.guild_permissions.manage_guild or 
            is_admin(ctx))

def get_guild_config(guild_id):
    """Get guild configuration"""
    ensure_data_files()
    try:
        with open("data/server_config.json", "r") as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    except:
        return {}

def update_guild_config(guild_id, config):
    """Update guild configuration"""
    ensure_data_files()
    try:
        with open("data/server_config.json", "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    data[str(guild_id)] = config
    
    with open("data/server_config.json", "w") as f:
        json.dump(data, f, indent=2)

def get_join_to_create_config(guild_id):
    """Get join to create configuration"""
    ensure_data_files()
    try:
        with open("data/join_to_create.json", "r") as f:
            data = json.load(f)
        return data.get(str(guild_id), {})
    except:
        return {}

def update_join_to_create_config(guild_id, config):
    """Update join to create configuration"""
    ensure_data_files()
    try:
        with open("data/join_to_create.json", "r") as f:
            data = json.load(f)
    except:
        data = {}
    
    data[str(guild_id)] = config
    
    with open("data/join_to_create.json", "w") as f:
        json.dump(data, f, indent=2)

def add_temp_channel(guild_id, channel_id, user_id):
    """Add temporary channel to tracking"""
    config = get_join_to_create_config(guild_id)
    if "temp_channels" not in config:
        config["temp_channels"] = {}
    config["temp_channels"][str(channel_id)] = user_id
    update_join_to_create_config(guild_id, config)

def remove_temp_channel(guild_id, channel_id):
    """Remove temporary channel from tracking"""
    config = get_join_to_create_config(guild_id)
    if "temp_channels" in config and str(channel_id) in config["temp_channels"]:
        del config["temp_channels"][str(channel_id)]
        update_join_to_create_config(guild_id, config)

async def temp_message(ctx, embed, seconds=5):
    """Send a temporary message that deletes after specified seconds"""
    msg = await ctx.send(embed=embed)
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass
