
#!/usr/bin/env python3
"""
Main entry point for the ESCUDO Discord bot.
This file contains the Discord bot functionality.
"""

import os
import discord
import logging
from discord.ext import commands
import asyncio
import json
from config import CONFIG
from datetime import datetime
import platform
import psutil

# ANSI color codes for beautiful console output
class Colors:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    MAGENTA = '\033[35m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

def print_banner():
    """Print beautiful ESCUDO banner with system information"""
    banner = f"""
{Colors.PURPLE}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║    ███████╗███████╗ ██████╗██╗   ██╗██████╗  ██████╗                        ║
║    ██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔═══██╗                       ║
║    █████╗  ███████╗██║     ██║   ██║██║  ██║██║   ██║                       ║
║    ██╔══╝  ╚════██║██║     ██║   ██║██║  ██║██║   ██║                       ║
║    ███████╗███████║╚██████╗╚██████╔╝██████╔╝╚██████╔╝                       ║
║    ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝  ╚═════╝                        ║
║                                                                               ║
║                        {Colors.CYAN}🛡️  PROTECTION & MODERATION BOT  🛡️{Colors.PURPLE}                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}"""
    print(banner)

def print_system_info():
    """Print detailed system information in organized sections"""
    print(f"\n{Colors.PURPLE}{Colors.BOLD}{'='*80}")
    print(f"                           SYSTEM INFORMATION")
    print(f"{'='*80}{Colors.END}")
    
    # Bot Information Section
    print(f"\n{Colors.CYAN}{Colors.BOLD}🤖 BOT CONFIGURATION{Colors.END}")
    print(f"{Colors.GRAY}├─{Colors.END} {Colors.WHITE}Bot Name:{Colors.END} {Colors.GREEN}ESCUDO Protection Bot{Colors.END}")
    print(f"{Colors.GRAY}├─{Colors.END} {Colors.WHITE}Prefix:{Colors.END} {Colors.YELLOW}{CONFIG['prefix']}{Colors.END}")
    print(f"{Colors.GRAY}├─{Colors.END} {Colors.WHITE}Version:{Colors.END} {Colors.CYAN}v2.0.0{Colors.END}")
    print(f"{Colors.GRAY}└─{Colors.END} {Colors.WHITE}Status:{Colors.END} {Colors.GREEN}Initializing...{Colors.END}")
    
    # System Information Section
    print(f"\n{Colors.MAGENTA}{Colors.BOLD}💻 SYSTEM DETAILS{Colors.END}")
    print(f"{Colors.GRAY}├─{Colors.END} {Colors.WHITE}Platform:{Colors.END} {Colors.CYAN}{platform.system()} {platform.release()}{Colors.END}")
    print(f"{Colors.GRAY}├─{Colors.END} {Colors.WHITE}Architecture:{Colors.END} {Colors.CYAN}{platform.machine()}{Colors.END}")
    print(f"{Colors.GRAY}├─{Colors.END} {Colors.WHITE}Python Version:{Colors.END} {Colors.YELLOW}{platform.python_version()}{Colors.END}")
    print(f"{Colors.GRAY}├─{Colors.END} {Colors.WHITE}CPU Cores:{Colors.END} {Colors.GREEN}{psutil.cpu_count()}{Colors.END}")
    
    # Memory usage
    memory = psutil.virtual_memory()
    memory_used = round(memory.used / 1024 / 1024 / 1024, 2)
    memory_total = round(memory.total / 1024 / 1024 / 1024, 2)
    print(f"{Colors.GRAY}└─{Colors.END} {Colors.WHITE}Memory:{Colors.END} {Colors.GREEN}{memory_used}GB{Colors.END}/{Colors.CYAN}{memory_total}GB{Colors.END}")
    
    # Features Section
    print(f"\n{Colors.BLUE}{Colors.BOLD}✨ FEATURES OVERVIEW{Colors.END}")
    features = [
        ("🔰 Antinuke Protection", "Advanced server protection system"),
        ("🔨 Moderation Tools", "Complete moderation suite"),
        ("🛠️ Utility Commands", "Server management utilities"),
        ("🔊 Voice Management", "Voice channel controls"),
        ("➕ Join to Create", "Dynamic voice channels"),
        ("👥 Self Roles", "User role management"),
        ("😈 Fun Commands", "Entertainment features")
    ]
    
    for i, (feature, description) in enumerate(features):
        prefix = "├─" if i < len(features) - 1 else "└─"
        print(f"{Colors.GRAY}{prefix}{Colors.END} {Colors.PURPLE}{feature}{Colors.END} - {Colors.WHITE}{description}{Colors.END}")

def print_startup_progress(step, total, message):
    """Print beautiful progress indicators"""
    percentage = int((step / total) * 100)
    bar_length = 40
    filled_length = int(bar_length * step // total)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    print(f"\r{Colors.PURPLE}[{bar}] {percentage:3d}% {Colors.CYAN}{message}{Colors.END}", end='', flush=True)
    if step == total:
        print()  # New line after completion

def print_status_update(message, status="INFO"):
    """Print formatted status messages"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if status == "SUCCESS":
        color = Colors.GREEN
        icon = "✅"
    elif status == "ERROR":
        color = Colors.RED
        icon = "❌"
    elif status == "WARNING":
        color = Colors.YELLOW
        icon = "⚠️"
    else:
        color = Colors.CYAN
        icon = "ℹ️"
    
    print(f"{Colors.GRAY}[{timestamp}]{Colors.END} {color}{icon} {message}{Colors.END}")

# Configure logging with custom formatter
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_colors = {
            'DEBUG': Colors.GRAY,
            'INFO': Colors.CYAN,
            'WARNING': Colors.YELLOW,
            'ERROR': Colors.RED,
            'CRITICAL': Colors.RED + Colors.BOLD
        }
        
        color = log_colors.get(record.levelname, Colors.WHITE)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        return f"{Colors.GRAY}[{timestamp}]{Colors.END} {color}[{record.levelname}]{Colors.END} {Colors.WHITE}{record.getMessage()}{Colors.END}"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger('ESCUDO')

# Create custom handler with colored formatter
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger.handlers = [handler]

# Also configure discord.py logger
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.WARNING)  # Reduce discord.py verbosity

# Initialize bot with intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=commands.when_mentioned_or(CONFIG['prefix']), intents=intents)

# Remove default help command to use custom help
bot.remove_command('help')

# Command count tracking
bot.command_count = 0
bot.np_command_count = 0
bot.dev_command_count = 0

# Load all cogs
async def load_cogs():
    cogs = [
        'cogs.antinuke',
        'cogs.moderation', 
        'cogs.utils',
        'cogs.voice',
        'cogs.others',
        'cogs.jointoCreate',
        'cogs.selfroles',
        'cogs.help'
    ]
    
    total_cogs = len(cogs)
    loaded = 0
    
    for i, cog in enumerate(cogs):
        try:
            print_startup_progress(i, total_cogs, f"Loading {cog.split('.')[-1]}...")
            await bot.load_extension(cog)
            loaded += 1
            await asyncio.sleep(0.1)  # Small delay for visual effect
        except Exception as e:
            print_status_update(f"Failed to load {cog}: {e}", "ERROR")
    
    print_startup_progress(total_cogs, total_cogs, f"Loaded {loaded}/{total_cogs} modules successfully!")
    print()

@bot.event
async def on_ready():
    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 CONNECTION ESTABLISHED 🎉{Colors.END}")
    print(f"{Colors.PURPLE}{'─' * 50}{Colors.END}")
    
    # Bot status information
    print(f"{Colors.WHITE}Bot Username:{Colors.END} {Colors.PURPLE}{bot.user.name}{Colors.END}")
    print(f"{Colors.WHITE}Bot ID:{Colors.END} {Colors.CYAN}{bot.user.id}{Colors.END}")
    print(f"{Colors.WHITE}Guild Count:{Colors.END} {Colors.GREEN}{len(bot.guilds)}{Colors.END}")
    print(f"{Colors.WHITE}User Count:{Colors.END} {Colors.GREEN}{sum(guild.member_count for guild in bot.guilds)}{Colors.END}")
    print(f"{Colors.WHITE}Commands Loaded:{Colors.END} {Colors.YELLOW}{bot.command_count}{Colors.END}")
    
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name=f"{CONFIG['prefix']}help | ESCUDO Protection"
    ))
    
    print(f"\n{Colors.PURPLE}{Colors.BOLD}🛡️  ESCUDO PROTECTION BOT IS NOW ONLINE!  🛡️{Colors.END}")
    print(f"{Colors.GRAY}Ready to protect and moderate your Discord servers!{Colors.END}")
    print(f"{Colors.PURPLE}{'═' * 80}{Colors.END}\n")

@bot.event
async def setup_hook():
    print_banner()
    print_system_info()
    
    print(f"\n{Colors.PURPLE}{Colors.BOLD}🚀 INITIALIZATION SEQUENCE{Colors.END}")
    print(f"{Colors.PURPLE}{'─' * 50}{Colors.END}")
    
    await load_cogs()
    
    # Count commands
    for command in bot.commands:
        bot.command_count += 1
        if command.name not in CONFIG['developer_commands']:
            bot.np_command_count += 1
        else:
            bot.dev_command_count += 1
    
    print_status_update(f"Command statistics calculated", "SUCCESS")
    print_status_update(f"Total Commands: {bot.command_count}", "INFO")
    print_status_update(f"Public Commands: {bot.np_command_count}", "INFO")
    print_status_update(f"Developer Commands: {bot.dev_command_count}", "INFO")
            
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Add test response for any message starting with "test"
    if message.content.lower().startswith("test"):
        await message.channel.send("Bot is responding to 'test'!")
    
    # This is required to process commands!
    await bot.process_commands(message)
    

    
@bot.command(name="test")
async def test_command(ctx):
    """Test command to check if the bot is working"""
    embed = discord.Embed(
        title="✅ Bot Test",
        description="The bot is working correctly!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Commands Loaded", value=f"`{bot.command_count}` commands", inline=True)
    embed.add_field(name="Prefix", value=f"`{CONFIG['prefix']}`", inline=True)
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)
    
@bot.command(name="hello")
async def hello(ctx):
    """Says hello to the user"""
    await ctx.send(f"👋 Hello {ctx.author.mention}! How can I help you today?")
    
@bot.event
async def on_command_error(ctx, error):
    print_status_update(f"Command error in {ctx.command}: {error}", "ERROR")
    await ctx.send(f"❌ Command error: {error}")

@bot.event
async def on_guild_join(guild):
    print_status_update(f"Joined new guild: {guild.name} ({guild.id})", "SUCCESS")

@bot.event
async def on_guild_remove(guild):
    print_status_update(f"Left guild: {guild.name} ({guild.id})", "WARNING")

def main():
    token = os.getenv("DISCORD_TOKEN","MTQwMTQ4NjY4ODY0NzM4NTEwOQ.GPlN28.4SxcLUXT1fnS9oRKRyU_lN_N1E6r8gbOFfHvR0")
    if not token:
        print_status_update("Discord token not found! Please set the DISCORD_TOKEN environment variable.", "ERROR")
        print(f"\n{Colors.RED}{Colors.BOLD}❌ STARTUP FAILED ❌{Colors.END}")
        print(f"{Colors.GRAY}Please configure your Discord bot token in the environment variables.{Colors.END}")
        return
    
    print_status_update("Starting Discord bot connection...", "INFO")
    try:
        bot.run(token)
    except Exception as e:
        print_status_update(f"Failed to start bot: {e}", "ERROR")

# Create an app object for gunicorn to use 
# This will be completely ignored when the bot runs
class FakeApp:
    def __call__(self, environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'ESCUDO Discord Bot is running']
        
    def run(self, host="0.0.0.0", port=5000, debug=True):
        """
        Mock run method to make the FakeApp compatible with Flask's interface.
        This is only called when running directly, not through gunicorn.
        """
        print(f"Mock web server running on {host}:{port}")
        print("The actual Discord bot is running in the background.")
        # Just keep the process alive
        import time
        while True:
            time.sleep(60)

app = FakeApp()

if __name__ == "__main__":
    # Run the Discord bot
    main()
