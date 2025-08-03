import discord
from discord.ext import commands
import asyncio
import random
import string
import time
from datetime import datetime
import platform
import psutil
import os
from typing import Optional
from config import CONFIG
from utils.helpers import (
    is_mod, is_admin, is_owner, get_guild_config, update_guild_config,
    temp_message
)
from utils.embeds import (
    success_embed, error_embed, info_embed, warning_embed, create_embed
)

class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="ping", help="Check the bot's latency")
    async def ping(self, ctx):
        """Check the bot's latency to Discord"""
        # Calculate the ping time
        start_time = time.time()
        message = await ctx.send("Pinging...")
        end_time = time.time()
        
        # Calculate API latency
        api_latency = round((end_time - start_time) * 1000)
        # Get websocket latency
        websocket_latency = round(self.bot.latency * 1000)
        
        embed = info_embed(
            title="🏓 Pong!",
            description=f"**API Latency:** {api_latency}ms\n**Websocket Latency:** {websocket_latency}ms"
        )
        
        await message.edit(content=None, embed=embed)
    
    @commands.command(name="userinfo", aliases=["user", "ui"], help="Get information about a user")
    async def userinfo(self, ctx, member: Optional[discord.Member] = None):
        """Display information about a user"""
        # If no member specified, use the command author
        member = member or ctx.author
        
        # Create the embed
        embed = create_embed(
            title=f"User Information - {member.display_name}",
            color=member.color
        )
        
        # Add the user's avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Basic user info
        created_at = int(member.created_at.timestamp())
        joined_at = int(member.joined_at.timestamp()) if member.joined_at else "Unknown"
        
        # User information fields
        embed.add_field(name="Username", value=f"{member}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="Created On", value=f"<t:{created_at}:F>\n(<t:{created_at}:R>)", inline=False)
        embed.add_field(name="Joined Server", value=f"<t:{joined_at}:F>\n(<t:{joined_at}:R>)" if isinstance(joined_at, int) else joined_at, inline=False)
        
        # Role information
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        if roles:
            embed.add_field(name=f"Roles [{len(roles)}]", value=" ".join(roles) if len(" ".join(roles)) < 1024 else f"{len(roles)} roles", inline=False)
        
        # Permissions (simplified)
        key_permissions = []
        if member.guild_permissions.administrator:
            key_permissions.append("Administrator")
        else:
            if member.guild_permissions.manage_guild:
                key_permissions.append("Manage Server")
            if member.guild_permissions.ban_members:
                key_permissions.append("Ban Members")
            if member.guild_permissions.kick_members:
                key_permissions.append("Kick Members")
            if member.guild_permissions.manage_channels:
                key_permissions.append("Manage Channels")
            if member.guild_permissions.manage_roles:
                key_permissions.append("Manage Roles")
            if member.guild_permissions.mention_everyone:
                key_permissions.append("Mention Everyone")
            if member.guild_permissions.manage_webhooks:
                key_permissions.append("Manage Webhooks")
            if member.guild_permissions.manage_emojis:
                key_permissions.append("Manage Emojis")
        
        if key_permissions:
            embed.add_field(name="Key Permissions", value=", ".join(key_permissions), inline=False)
        
        # Send the embed
        await ctx.send(embed=embed)
    
    @commands.command(name="serverinfo", aliases=["server", "si"], help="Get information about the server")
    async def serverinfo(self, ctx):
        """Display information about the current server"""
        guild = ctx.guild
        
        # Create the embed
        embed = create_embed(
            title=f"Server Information - {guild.name}",
            color=CONFIG["embed_color"]
        )
        
        # Add the server icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # General server info
        created_at = int(guild.created_at.timestamp())
        
        # Count bots and humans
        bots = sum(1 for member in guild.members if member.bot)
        humans = guild.member_count - bots
        
        # Count channels by type
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        
        # Basic server information
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created On", value=f"<t:{created_at}:F>\n(<t:{created_at}:R>)", inline=True)
        
        # Member information
        embed.add_field(name="Members", value=f"Total: {guild.member_count}\nHumans: {humans}\nBots: {bots}", inline=True)
        
        # Channel information
        embed.add_field(name="Channels", value=f"Text: {text_channels}\nVoice: {voice_channels}\nCategories: {categories}", inline=True)
        
        # Role information
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        
        # Security level
        verification_level = str(guild.verification_level).capitalize()
        embed.add_field(name="Verification Level", value=verification_level, inline=True)
        
        # Boosts
        embed.add_field(name="Boost Level", value=f"Level {guild.premium_tier}", inline=True)
        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        
        # Top roles (up to 10)
        top_roles = [role.mention for role in list(reversed(guild.roles))[:10] if role.name != "@everyone"]
        if top_roles:
            embed.add_field(name=f"Top Roles [{min(len(top_roles), 10)}]", value=" ".join(top_roles), inline=False)
        
        # Server features
        if guild.features:
            features = [f.replace("_", " ").title() for f in guild.features]
            embed.add_field(name="Features", value=", ".join(features), inline=False)
        
        # Send the embed
        await ctx.send(embed=embed)
    
    @commands.command(name="avatar", aliases=["av"], help="Get a user's avatar")
    async def avatar(self, ctx, member: Optional[discord.Member] = None):
        """Display a user's avatar"""
        # If no member specified, use the command author
        member = member or ctx.author
        
        # Create the embed
        embed = create_embed(
            title=f"Avatar for {member}",
            color=member.color
        )
        
        # Set the avatar as the image
        embed.set_image(url=member.display_avatar.url)
        
        # Add links to different formats
        formats = []
        for fmt in ["png", "jpg", "webp"]:
            formats.append(f"[{fmt}]({member.display_avatar.with_format(fmt).url})")
        
        if member.display_avatar.is_animated():
            formats.append(f"[gif]({member.display_avatar.with_format('gif').url})")
        
        embed.add_field(name="Links", value=" | ".join(formats), inline=False)
        
        # Send the embed
        await ctx.send(embed=embed)
    
    @commands.command(name="botinfo", aliases=["bi", "info"], help="Get information about the bot")
    async def botinfo(self, ctx):
        """Display information about the bot"""
        # Get bot information
        bot_user = self.bot.user
        app_info = await self.bot.application_info()
        
        # Create the embed
        embed = create_embed(
            title=f"{bot_user.name} Information",
            color=CONFIG["embed_color"]
        )
        
        # Add the bot's avatar
        embed.set_thumbnail(url=bot_user.display_avatar.url)
        
        # Basic bot info
        created_at = int(bot_user.created_at.timestamp())
        
        # System information
        python_version = platform.python_version()
        discord_version = discord.__version__
        
        # Memory usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        
        # Uptime
        uptime = datetime.now() - datetime.fromtimestamp(process.create_time())
        days, hours, minutes, seconds = (
            uptime.days,
            uptime.seconds // 3600,
            (uptime.seconds // 60) % 60,
            uptime.seconds % 60
        )
        
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        
        # Bot information fields
        embed.add_field(name="Bot ID", value=bot_user.id, inline=True)
        embed.add_field(name="Owner", value=app_info.owner.mention, inline=True)
        embed.add_field(name="Created On", value=f"<t:{created_at}:F>\n(<t:{created_at}:R>)", inline=True)
        
        # Command statistics
        embed.add_field(name="Commands", value=f"Total: {self.bot.command_count}\nUser: {self.bot.np_command_count}\nDev: {self.bot.dev_command_count}", inline=True)
        
        # Server and user counts
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        
        total_users = sum(guild.member_count for guild in self.bot.guilds)
        embed.add_field(name="Users", value=total_users, inline=True)
        
        # Performance statistics
        embed.add_field(name="System", value=f"Python: {python_version}\nDiscord.py: {discord_version}", inline=True)
        embed.add_field(name="Memory", value=f"{memory_usage:.2f} MB", inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        
        # Send the embed
        await ctx.send(embed=embed)
    
    @commands.command(name="invite", help="Get the bot's invite link")
    async def invite(self, ctx):
        """Generate an invite link for the bot"""
        # Create the invite link
        permissions = discord.Permissions(
            # General permissions
            manage_roles=True,
            manage_channels=True,
            manage_webhooks=True,
            manage_guild=True,
            # Text permissions
            manage_messages=True,
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_message_history=True,
            add_reactions=True,
            use_external_emojis=True,
            read_messages=True,
            # Voice permissions
            connect=True,
            speak=True,
            move_members=True,
            deafen_members=True,
            mute_members=True,
            # Member management
            kick_members=True,
            ban_members=True,
            change_nickname=True,
            manage_nicknames=True
        )
        
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        
        # Create the embed
        embed = info_embed(
            title="Invite ESCUDO to your server",
            description=f"Click the link below to invite the bot to your server:\n\n[Invite Link]({invite_url})"
        )
        
        # Send the embed
        await ctx.send(embed=embed)
    
    @commands.command(name="password", aliases=["genpass"], help="Generate a random password")
    async def password(self, ctx, length: int = 12):
        """Generate a random secure password"""
        # Check if the requested length is valid
        if length < 8:
            await ctx.send(embed=error_embed(
                title="Invalid Length",
                description="Password length must be at least 8 characters for security."
            ))
            return
        
        if length > 100:
            await ctx.send(embed=error_embed(
                title="Invalid Length",
                description="Password length cannot exceed 100 characters."
            ))
            return
        
        # Generate a random password with mixed character types
        chars = string.ascii_letters + string.digits + string.punctuation
        password = ""
        
        # Ensure we have at least one of each character type
        password += random.choice(string.ascii_uppercase)  # At least one uppercase
        password += random.choice(string.ascii_lowercase)  # At least one lowercase
        password += random.choice(string.digits)           # At least one digit
        password += random.choice(string.punctuation)      # At least one special char
        
        # Fill the rest of the password
        for _ in range(length - 4):
            password += random.choice(chars)
        
        # Shuffle the password to mix the guaranteed characters
        password_list = list(password)
        random.shuffle(password_list)
        password = "".join(password_list)
        
        # Try to DM the password to the user for privacy
        try:
            await ctx.author.send(embed=info_embed(
                title="Generated Password",
                description=f"Here's your generated password:\n```{password}```\n**Keep this secure!**"
            ))
            
            # Confirm in the channel that the password was sent
            await ctx.send(embed=success_embed(
                title="Password Generated",
                description="I've sent you a DM with your generated password."
            ))
        except discord.Forbidden:
            # If DM fails, send it in the channel but delete after a short time
            warning_msg = await ctx.send(embed=warning_embed(
                title="DM Unavailable",
                description="I couldn't send you a DM. The password will be shown here and will be deleted in 30 seconds for security."
            ))
            
            password_msg = await ctx.send(embed=info_embed(
                title="Generated Password",
                description=f"Here's your generated password:\n```{password}```\n**This message will be deleted in 30 seconds!**"
            ))
            
            # Delete the messages after 30 seconds
            await asyncio.sleep(30)
            try:
                await warning_msg.delete()
                await password_msg.delete()
            except discord.NotFound:
                pass
    
    @commands.command(name="poll", help="Create a poll")
    async def poll(self, ctx, question, *options):
        """Create a poll with reactions for voting"""
        # Check if there are options
        if not options:
            # Simple yes/no poll
            embed = create_embed(
                title="📊 Poll",
                description=question
            )
            embed.set_footer(text=f"Poll by {ctx.author}")
            
            msg = await ctx.send(embed=embed)
            await msg.add_reaction("👍")  # Yes
            await msg.add_reaction("👎")  # No
            return
        
        # Check if there are too many options
        if len(options) > 10:
            await ctx.send(embed=error_embed(
                title="Too Many Options",
                description="You can only have up to 10 options in a poll."
            ))
            return
        
        # Create a poll with multiple options
        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        description = [f"{emoji_numbers[i]} {option}" for i, option in enumerate(options)]
        description = "\n".join(description)
        
        embed = create_embed(
            title="📊 Poll",
            description=f"**{question}**\n\n{description}"
        )
        embed.set_footer(text=f"Poll by {ctx.author}")
        
        msg = await ctx.send(embed=embed)
        
        # Add reactions
        for i in range(len(options)):
            await msg.add_reaction(emoji_numbers[i])
    
    @commands.command(name="countdown", help="Start a countdown timer")
    async def countdown(self, ctx, seconds: int = 10):
        """Start a countdown timer"""
        # Check if the seconds are valid
        if seconds <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Time",
                description="Please provide a positive number of seconds."
            ))
            return
        
        if seconds > 300:  # 5 minute limit
            await ctx.send(embed=error_embed(
                title="Time Too Long",
                description="Countdown cannot exceed 5 minutes (300 seconds)."
            ))
            return
        
        # Create and send the initial embed
        embed = info_embed(
            title="⏱️ Countdown",
            description=f"Time remaining: {seconds} seconds"
        )
        message = await ctx.send(embed=embed)
        
        # Update the countdown
        remaining_time = seconds
        while remaining_time > 0:
            # Sleep for a bit
            await asyncio.sleep(1)
            remaining_time -= 1
            
            # Update the message every 5 seconds or at specific points
            if remaining_time % 5 == 0 or remaining_time <= 10:
                embed.description = f"Time remaining: {remaining_time} seconds"
                await message.edit(embed=embed)
        
        # Final message
        embed = success_embed(
            title="⏱️ Countdown Complete",
            description="Time's up!"
        )
        await message.edit(embed=embed)
    
    @commands.command(name="remind", aliases=["reminder", "remindme"], help="Set a reminder")
    async def remind(self, ctx, time: str, *, reminder: str):
        """Set a reminder for yourself"""
        # Parse the time string
        time_units = {
            's': 1,                # seconds
            'm': 60,               # minutes
            'h': 60 * 60,          # hours
            'd': 60 * 60 * 24,     # days
            'w': 60 * 60 * 24 * 7  # weeks
        }
        
        # Extract the number and unit from the time string
        import re
        match = re.match(r'(\d+)([smhdw])', time.lower())
        
        if not match:
            await ctx.send(embed=error_embed(
                title="Invalid Time Format",
                description="Please use a valid time format like `5m`, `2h`, `1d`, etc."
            ))
            return
        
        amount, unit = match.groups()
        seconds = int(amount) * time_units[unit]
        
        # Check if the time is valid
        if seconds <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Time",
                description="Please provide a positive amount of time."
            ))
            return
        
        if seconds > 2592000:  # 30 day limit
            await ctx.send(embed=error_embed(
                title="Time Too Long",
                description="Reminders cannot exceed 30 days."
            ))
            return
        
        # Confirm the reminder
        await ctx.send(embed=success_embed(
            title="Reminder Set",
            description=f"I'll remind you about: **{reminder}** in **{amount}{unit}**"
        ))
        
        # Wait for the specified time
        await asyncio.sleep(seconds)
        
        # Send the reminder
        try:
            reminder_embed = info_embed(
                title="⏰ Reminder",
                description=f"{ctx.author.mention}, you asked me to remind you:\n\n**{reminder}**"
            )
            
            # Add a timestamp for when the reminder was set
            reminder_time = datetime.now().timestamp() - seconds
            reminder_embed.set_footer(text=f"Reminder set {time} ago")
            
            await ctx.channel.send(content=ctx.author.mention, embed=reminder_embed)
            
            # Also try to DM the user
            try:
                await ctx.author.send(embed=reminder_embed)
            except discord.Forbidden:
                pass
                
        except discord.NotFound:
            # If the channel was deleted, try to DM the user
            try:
                reminder_embed = info_embed(
                    title="⏰ Reminder",
                    description=f"You asked me to remind you:\n\n**{reminder}**"
                )
                
                # Add a timestamp for when the reminder was set
                reminder_time = datetime.now().timestamp() - seconds
                reminder_embed.set_footer(text=f"Reminder set {time} ago")
                
                await ctx.author.send(embed=reminder_embed)
            except discord.Forbidden:
                pass
    
    @commands.command(name="eval", hidden=True, help="Evaluate Python code")
    @commands.check(is_owner)
    async def eval(self, ctx, *, code):
        """Evaluate Python code (Owner only)"""
        # This is a dangerous command, so only bot owners should be able to use it
        
        # Remove code blocks if present
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.split("\n")[1:-1])
        
        # Add return for expressions
        code = f"async def _eval_func():\n{textwrap.indent(code, '    ')}"
        
        # Create the environment
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "channel": ctx.channel,
            "author": ctx.author,
            "guild": ctx.guild,
            "message": ctx.message,
            "discord": discord,
            "asyncio": asyncio,
            "os": os,
            "random": random,
            "time": time,
            "datetime": datetime
        }
        env.update(globals())
        
        try:
            # Execute the code
            exec(code, env)
            func = env["_eval_func"]
            result = await func()
            
            # Format the result
            if result is None:
                await ctx.send(embed=success_embed(
                    title="Code Executed",
                    description="Code executed successfully (no output)."
                ))
            else:
                await ctx.send(embed=info_embed(
                    title="Code Result",
                    description=f"```py\n{result}\n```"
                ))
                
        except Exception as e:
            # Format the error
            await ctx.send(embed=error_embed(
                title="Execution Error",
                description=f"```py\n{type(e).__name__}: {e}\n```"
            ))
    
    # Add the missing import
    import textwrap
    
    @commands.command(name="reload", hidden=True, help="Reload a cog")
    @commands.check(is_owner)
    async def reload(self, ctx, cog=None):
        """Reload a cog or all cogs (Owner only)"""
        if cog is None:
            # Reload all cogs
            reloaded = []
            failed = []
            
            cogs = [
                'cogs.antinuke',
                'cogs.moderation',
                'cogs.utils',
                'cogs.voice',
                'cogs.others',
                'cogs.jointoCreate',
                'cogs.selfroles',
                'cogs.shadowclone',
                'cogs.help'
            ]
            
            for cog_name in cogs:
                try:
                    await self.bot.unload_extension(cog_name)
                    await self.bot.load_extension(cog_name)
                    reloaded.append(cog_name)
                except Exception as e:
                    failed.append(f"{cog_name}: {type(e).__name__} - {e}")
            
            # Create message based on results
            if failed:
                embed = warning_embed(
                    title="Cogs Reloaded",
                    description=f"✅ Successfully reloaded {len(reloaded)}/{len(cogs)} cogs."
                )
                
                # Add failures
                embed.add_field(name="Failed to reload", value="\n".join(failed), inline=False)
            else:
                embed = success_embed(
                    title="All Cogs Reloaded",
                    description=f"✅ Successfully reloaded all {len(reloaded)} cogs."
                )
            
            await ctx.send(embed=embed)
            
        else:
            # Format the cog name
            cog_name = f"cogs.{cog.lower()}" if not cog.startswith("cogs.") else cog
            
            try:
                await self.bot.unload_extension(cog_name)
                await self.bot.load_extension(cog_name)
                await ctx.send(embed=success_embed(
                    title="Cog Reloaded",
                    description=f"✅ Successfully reloaded `{cog_name}`"
                ))
            except Exception as e:
                await ctx.send(embed=error_embed(
                    title="Reload Failed",
                    description=f"Failed to reload `{cog_name}`:\n```py\n{type(e).__name__}: {e}\n```"
                ))
    
    @commands.command(name="shutdown", hidden=True, help="Shut down the bot")
    @commands.check(is_owner)
    async def shutdown(self, ctx):
        """Shut down the bot (Owner only)"""
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Shutdown Confirmation",
            description="⚠️ Are you sure you want to shut down the bot? This will take the bot offline until it is manually restarted.\n\nReact with ✅ to confirm or ❌ to cancel."
        ))
        
        await confirmation.add_reaction("✅")
        await confirmation.add_reaction("❌")
        
        try:
            # Wait for reaction
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirmation.id
            
            reaction, user = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await ctx.send(embed=info_embed(
                    title="Shutdown Cancelled",
                    description="Operation has been cancelled."
                ))
                return
            
            # Shut down the bot
            await ctx.send(embed=success_embed(
                title="Shutting Down",
                description="✅ The bot is shutting down. Goodbye!"
            ))
            
            # Close the bot connection
            await self.bot.close()
            
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Shutdown Cancelled",
                description="Confirmation timed out after 60 seconds."
            ))

async def setup(bot):
    await bot.add_cog(Utils(bot))
