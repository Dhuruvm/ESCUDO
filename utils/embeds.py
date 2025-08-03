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
import discord
from config import CONFIG

def help_menu_embed(ctx, bot):
    """Create the main help menu embed"""
    embed = discord.Embed(
        title="Help Menu",
        description="Select a category below to view commands",
        color=CONFIG["embed_color"]
    )
    
    categories = {
        "🔰": "Antinuke - Protect your server from raids",
        "🛡️": "No Prefix - Commands without prefix",
        "🔨": "Moderation - Moderation tools",
        "🛠️": "Utils - Utility commands",
        "🔊": "Voice - Voice channel management",
        "😈": "Other - Fun and misc commands",
        "➕": "Join to Create - Dynamic voice channels",
        "👥": "Self Roles - Self-assignable roles"
    }
    
    for emoji, description in categories.items():
        embed.add_field(name=f"{emoji} {description.split(' - ')[0]}", 
                       value=description.split(' - ')[1], inline=False)
    
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    return embed

def category_help_embed(ctx, category, commands_list):
    """Create a category-specific help embed"""
    embed = discord.Embed(
        title=f"{category.title()} Commands",
        description=f"Commands in the {category} category",
        color=CONFIG["embed_color"]
    )
    
    if commands_list:
        command_text = ""
        for cmd in commands_list:
            command_text += f"`{CONFIG['prefix']}{cmd.name}` - {cmd.help or 'No description'}\n"
        embed.add_field(name="Commands", value=command_text, inline=False)
    else:
        embed.add_field(name="Commands", value="No commands available", inline=False)
    
    embed.set_footer(text=f"Use {CONFIG['prefix']}help <command> for more info")
    return embed

def command_help_embed(ctx, command):
    """Create a command-specific help embed"""
    embed = discord.Embed(
        title=f"Command: {command.name}",
        description=command.help or "No description available",
        color=CONFIG["embed_color"]
    )
    
    if command.aliases:
        embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=True)
    
    embed.add_field(name="Usage", value=f"`{CONFIG['prefix']}{command.name}`", inline=True)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    return embed

def success_embed(title, description):
    """Create a success embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=CONFIG["success_color"]
    )

def error_embed(title, description):
    """Create an error embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=CONFIG["error_color"]
    )

def warning_embed(title, description):
    """Create a warning embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=CONFIG["warning_color"]
    )

def info_embed(title, description):
    """Create an info embed"""
    return discord.Embed(
        title=title,
        description=description,
        color=CONFIG["info_color"]
    )
import discord
from config import CONFIG

def create_embed(title=None, description=None, color=None):
    """Create a basic embed with default styling"""
    if color is None:
        color = CONFIG.get("embed_color", discord.Color.blue())
    
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

def success_embed(title, description=None):
    """Create a success embed with green color"""
    embed = discord.Embed(title=title, description=description, color=discord.Color.green())
    return embed

def error_embed(title, description=None):
    """Create an error embed with red color"""
    embed = discord.Embed(title=title, description=description, color=discord.Color.red())
    return embed

def info_embed(title, description=None):
    """Create an info embed with blue color"""
    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    return embed

def warning_embed(title, description=None):
    """Create a warning embed with yellow color"""
    embed = discord.Embed(title=title, description=description, color=discord.Color.yellow())
    return embed

def help_menu_embed(ctx, bot):
    """Create the main help menu embed"""
    embed = create_embed(
        title="Help Menu",
        description="Select a category by clicking the reactions below:",
        color=CONFIG.get("embed_color", discord.Color.blue())
    )
    
    embed.add_field(
        name="Categories",
        value="🔰 **Antinuke** - Server protection\n"
              "🔨 **Moderation** - Moderation tools\n" 
              "🛠️ **Utils** - Utility commands\n"
              "🔊 **Voice** - Voice management\n"
              "😈 **Other** - Fun commands\n"
              "➕ **JoinToCreate** - Dynamic voice channels\n"
              "👥 **SelfRoles** - Self-assignable roles\n"
              "🔮 **ShadowClone** - Personal bot clones",
        inline=False
    )
    
    embed.set_footer(text=f"Use {CONFIG['prefix']}help <command> for specific command info")
    return embed

def category_help_embed(ctx, category, commands_list):
    """Create a category help embed"""
    embed = create_embed(
        title=f"{category.title()} Commands",
        description=f"Commands in the {category} category:",
        color=CONFIG.get("embed_color", discord.Color.blue())
    )
    
    if commands_list:
        commands_text = []
        for cmd in commands_list:
            cmd_help = cmd.help or "No description available"
            commands_text.append(f"`{CONFIG['prefix']}{cmd.name}` - {cmd_help}")
        
        embed.add_field(
            name="Available Commands",
            value="\n".join(commands_text[:10]),  # Limit to 10 commands per page
            inline=False
        )
        
        if len(commands_list) > 10:
            embed.set_footer(text=f"Showing 10 of {len(commands_list)} commands")
    else:
        embed.add_field(
            name="No Commands",
            value="No commands available in this category.",
            inline=False
        )
    
    return embed

def command_help_embed(ctx, command):
    """Create a specific command help embed"""
    embed = create_embed(
        title=f"Command: {command.name}",
        description=command.help or "No description available",
        color=CONFIG.get("embed_color", discord.Color.blue())
    )
    
    # Add usage information
    usage = f"{CONFIG['prefix']}{command.name}"
    if command.usage:
        usage += f" {command.usage}"
    
    embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
    
    # Add aliases if any
    if command.aliases:
        embed.add_field(
            name="Aliases", 
            value=", ".join([f"`{alias}`" for alias in command.aliases]), 
            inline=False
        )
    
    # Add category
    if command.cog_name:
        embed.add_field(name="Category", value=command.cog_name, inline=True)
    
    return embed
