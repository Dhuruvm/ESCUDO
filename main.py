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

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG for more verbose logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ESCUDO')
# Also log discord.py events
discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.DEBUG)

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
    logger.info("Loading cogs...")
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
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded {cog} successfully!")
        except Exception as e:
            logger.error(f"Failed to load {cog}: {e}")

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name=f"{CONFIG['prefix']}help | ESCUDO"
    ))
    logger.info("Bot is ready!")

@bot.event
async def setup_hook():
    await load_cogs()
    # Count commands
    for command in bot.commands:
        bot.command_count += 1
        if command.name not in CONFIG['developer_commands']:
            bot.np_command_count += 1
        else:
            bot.dev_command_count += 1
            
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    logger.debug(f"Received message: {message.content} from {message.author}")
    
    # Add test response for any message starting with "test"
    if message.content.lower().startswith("test"):
        await message.channel.send("Bot is responding to 'test'!")
    
    # This is required to process commands!
    await bot.process_commands(message)
    
@bot.command(name="ping")
async def ping(ctx):
    """Simple ping command to test if the bot is responding"""
    logger.debug("Ping command executed")
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot Latency: `{round(bot.latency * 1000)}ms`",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)
    
@bot.command(name="test")
async def test_command(ctx):
    """Test command to check if the bot is working"""
    logger.debug("Test command executed")
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
    logger.debug("Hello command executed")
    await ctx.send(f"👋 Hello {ctx.author.mention}! How can I help you today?")
    
@bot.event
async def on_command_error(ctx, error):
    logger.error(f"Command error: {error}")
    await ctx.send(f"Command error: {error}")

def main():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.error("Discord token not found! Please set the DISCORD_TOKEN environment variable.")
        return
    
    logger.info("Starting Discord bot...")
    bot.run(token)

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