import discord
from discord.ext import commands
from config import CONFIG

# Hardcoded developer ID
DEVELOPER_ID = 1077913091938975744

def is_owner(ctx):
    """Check if the user is the bot owner"""
    if isinstance(ctx, discord.Member):
        user_id = ctx.id
    else:
        user_id = ctx.author.id
    
    # Check if user is developer
    if user_id == DEVELOPER_ID:
        return True
    
    # Check if user is in owner_ids list
    return user_id in CONFIG['owner_ids']

def is_extra_owner(ctx):
    """Check if the user is an extra owner in the current guild"""
    if isinstance(ctx, discord.Member):
        guild_id = ctx.guild.id
        user_id = ctx.id
    else:
        guild_id = ctx.guild.id
        user_id = ctx.author.id
    
    # Always allow the developer and primary owners
    if is_owner(ctx):
        return True
    
    # Check if user is an extra owner for this guild
    extra_owners = CONFIG['extra_owners'].get(str(guild_id), [])
    return user_id in extra_owners

def is_admin(ctx):
    """Check if the user has admin permissions or roles"""
    if isinstance(ctx, discord.Member):
        member = ctx
    else:
        member = ctx.author
    
    # Owner and extra owners are always considered admins
    if is_owner(ctx) or is_extra_owner(ctx):
        return True
    
    # Check if user has admin permissions
    if member.guild_permissions.administrator:
        return True
    
    # Import here to avoid circular imports
    from utils.helpers import get_guild_config
    
    # Check if user has admin role
    config = get_guild_config(member.guild.id)
    admin_roles = config.get('admin_roles', [])
    
    for role in member.roles:
        if str(role.id) in admin_roles:
            return True
    
    return False

def is_mod(ctx):
    """Check if the user has moderator permissions or roles"""
    if isinstance(ctx, discord.Member):
        member = ctx
    else:
        member = ctx.author
    
    # Admins are also considered mods
    if is_admin(ctx):
        return True
    
    # Check if user has mod permissions
    if member.guild_permissions.manage_messages or member.guild_permissions.kick_members:
        return True
    
    # Import here to avoid circular imports
    from utils.helpers import get_guild_config
    
    # Check if user has mod role
    config = get_guild_config(member.guild.id)
    mod_roles = config.get('mod_roles', [])
    
    for role in member.roles:
        if str(role.id) in mod_roles:
            return True
    
    return False

def is_antinuke_whitelisted(ctx):
    """Check if the user is whitelisted for antinuke actions"""
    if isinstance(ctx, discord.Member):
        member = ctx
    else:
        member = ctx.author
    
    # Owners and extra owners are always whitelisted
    if is_owner(ctx) or is_extra_owner(ctx):
        return True
    
    # Import here to avoid circular imports
    from utils.helpers import is_whitelisted
    
    # Check if user is in the whitelist using the helper function
    return is_whitelisted(member.guild.id, member.id)

# Command checks for different permission levels
def owner_only():
    """Decorator for commands that only bot owners can use"""
    async def predicate(ctx):
        if not is_owner(ctx):
            await ctx.send("❌ This command is only available to bot owners.")
            return False
        return True
    return commands.check(predicate)

def extra_owner_only():
    """Decorator for commands that only bot owners and extra owners can use"""
    async def predicate(ctx):
        if not is_extra_owner(ctx):
            await ctx.send("❌ This command is only available to server owners.")
            return False
        return True
    return commands.check(predicate)

def admin_only():
    """Decorator for commands that only admins can use"""
    async def predicate(ctx):
        if not is_admin(ctx):
            await ctx.send("❌ This command requires administrator permissions.")
            return False
        return True
    return commands.check(predicate)

def mod_only():
    """Decorator for commands that only mods can use"""
    async def predicate(ctx):
        if not is_mod(ctx):
            await ctx.send("❌ This command requires moderator permissions.")
            return False
        return True
    return commands.check(predicate)

def antinuke_whitelisted_only():
    """Decorator for actions that only antinuke whitelisted users can perform"""
    async def predicate(ctx):
        if not is_antinuke_whitelisted(ctx):
            await ctx.send("❌ You must be whitelisted to perform this action.")
            return False
        return True
    return commands.check(predicate)

# Special check for developer-only commands
def developer_only():
    """Decorator for commands that only the developer can use"""
    async def predicate(ctx):
        if ctx.author.id != DEVELOPER_ID:
            await ctx.send("❌ This command is only available to the bot developer.")
            return False
        return True
    return commands.check(predicate)