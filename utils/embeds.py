import discord
from datetime import datetime
from config import CONFIG

# Create standard embeds for consistent styling throughout the bot
def create_embed(title=None, description=None, color=None, footer=None, thumbnail=None):
    """Create a standard embed with consistent styling"""
    if color is None:
        color = CONFIG['embed_color']
    
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.now()
    )
    
    if footer:
        embed.set_footer(text=footer)
    else:
        embed.set_footer(text="E.D.I.T.H | Protection Bot")
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
        
    return embed

def success_embed(title=None, description=None, footer=None):
    """Create a success embed"""
    return create_embed(
        title=title if title else "Success",
        description=description,
        color=CONFIG['success_color'],
        footer=footer
    )

def error_embed(title=None, description=None, footer=None):
    """Create an error embed"""
    return create_embed(
        title=title if title else "Error",
        description=description,
        color=CONFIG['error_color'],
        footer=footer
    )

def warning_embed(title=None, description=None, footer=None):
    """Create a warning embed"""
    return create_embed(
        title=title if title else "Warning",
        description=description,
        color=CONFIG['warning_color'],
        footer=footer
    )

def info_embed(title=None, description=None, footer=None):
    """Create an info embed"""
    return create_embed(
        title=title if title else "Information",
        description=description,
        color=CONFIG['info_color'],
        footer=footer
    )

def help_menu_embed(ctx, bot):
    """Create the main help menu embed"""
    prefix = CONFIG["prefix"]
    
    embed = create_embed(
        title="Help Menu",
        color=CONFIG['embed_color']
    )
    
    # Basic information section with a red line on the left
    info_section = (
        f"Prefix :{prefix}\n"
        f"Total Commands :{bot.command_count}\n"
        f"Total Np Commands :{bot.np_command_count}\n"
        f"Only Developers Commands :{bot.dev_command_count}\n"
        f"Basic Antinuke:`True`\n"
        f"For AntiBypass Antinuke:\n"
        f"Use `/antibypass`"
    )
    embed.add_field(name="", value=info_section, inline=False)
    
    # Main Menu section
    main_menu = (
        "**Main Menu**\n"
        "🔰:Antinuke\n"
        "🛡️:No Prefix\n"
        "🔨:Moderation\n"
        "🛠️:Utils\n"
        "🔊:Voice"
    )
    embed.add_field(name="", value=main_menu, inline=False)
    
    # Others Menu section
    others_menu = (
        "**Others Menu**\n"
        "😈:Other\n"
        "➕:Join To Create\n"
        "👥:SelfRoles"
    )
    embed.add_field(name="", value=others_menu, inline=False)
    
    embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
    return embed

def category_help_embed(ctx, category, commands_list):
    """Create a help embed for a specific category"""
    embed = create_embed(
        title=f"{category.title()} Commands",
        color=CONFIG['embed_color']
    )
    
    if not commands_list:
        embed.description = "No commands available in this category."
        return embed
    
    # Group commands by subcategory if they have one
    command_groups = {}
    for cmd in commands_list:
        subcategory = getattr(cmd, "subcategory", "General")
        if subcategory not in command_groups:
            command_groups[subcategory] = []
        command_groups[subcategory].append(cmd)
    
    # Add each group to the embed
    for subcategory, cmds in command_groups.items():
        commands_text = "\n".join([f"`{cmd.name}` - {cmd.help}" for cmd in cmds])
        embed.add_field(name=subcategory, value=commands_text, inline=False)
    
    embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
    return embed

def command_help_embed(ctx, command):
    """Create a detailed help embed for a specific command"""
    prefix = CONFIG["prefix"]
    
    embed = create_embed(
        title=f"Command: {command.name}",
        color=CONFIG['embed_color']
    )
    
    # Command description
    embed.add_field(name="Description", value=command.help, inline=False)
    
    # Command usage
    usage = command.usage or command.name
    embed.add_field(name="Usage", value=f"`{prefix}{usage}`", inline=False)
    
    # Command aliases if any
    if command.aliases:
        aliases = ", ".join([f"`{alias}`" for alias in command.aliases])
        embed.add_field(name="Aliases", value=aliases, inline=False)
    
    # Command cooldown if any
    if command._buckets and command._buckets._cooldown:
        cd = command._buckets._cooldown
        embed.add_field(
            name="Cooldown", 
            value=f"{cd.rate} uses every {cd.per:.0f} seconds", 
            inline=False
        )
    
    embed.set_thumbnail(url=ctx.bot.user.display_avatar.url)
    return embed
