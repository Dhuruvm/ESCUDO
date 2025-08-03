import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
import re
from typing import Optional, Union
from config import CONFIG
from utils.helpers import (
    is_mod, is_admin, is_owner, get_guild_config, update_guild_config,
    temp_message
)
from utils.embeds import (
    success_embed, error_embed, info_embed, warning_embed
)
from utils.db import (
    add_warning, get_warnings, remove_warning, clear_warnings,
    add_mute, remove_mute, is_muted
)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.snipe_messages = {}
        self.mute_tasks = {}
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """Store deleted messages for the snipe command"""
        if message.author.bot:
            return
        
        channel_id = str(message.channel.id)
        
        if channel_id not in self.snipe_messages:
            self.snipe_messages[channel_id] = []
        
        # Keep only the last 10 deleted messages per channel
        if len(self.snipe_messages[channel_id]) >= 10:
            self.snipe_messages[channel_id].pop(0)
        
        self.snipe_messages[channel_id].append({
            'content': message.content or "[No content]",
            'author': message.author,
            'avatar_url': message.author.display_avatar.url,
            'created_at': message.created_at
        })
    
    async def get_mute_role(self, guild):
        """Get or create a mute role for the guild"""
        config = get_guild_config(guild.id)
        muted_role_id = config.get("muted_role")
        
        # If a muted role is saved, try to fetch it
        if muted_role_id:
            role = guild.get_role(int(muted_role_id))
            if role:
                return role
        
        # Try to find an existing "Muted" role
        role = discord.utils.get(guild.roles, name="Muted")
        if role:
            # Save the role ID
            config["muted_role"] = str(role.id)
            update_guild_config(guild.id, config)
            return role
        
        # Create a new mute role
        try:
            muted_role = await guild.create_role(
                name="Muted",
                reason="ESCUDO: Creating muted role"
            )
            
            # Set permission overwrites for the role
            for channel in guild.channels:
                try:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False)
                except discord.Forbidden:
                    continue
            
            # Save the role ID
            config["muted_role"] = str(muted_role.id)
            update_guild_config(guild.id, config)
            
            return muted_role
        except discord.Forbidden:
            return None
    
    async def schedule_unmute(self, guild_id, user_id, duration):
        """Schedule an unmute task for a user"""
        task_key = f"{guild_id}_{user_id}"
        
        # Cancel any existing unmute task for this user
        if task_key in self.mute_tasks:
            self.mute_tasks[task_key].cancel()
        
        # Create a new unmute task
        guild = self.bot.get_guild(int(guild_id))
        if not guild:
            return
        
        async def unmute_task():
            await asyncio.sleep(duration.total_seconds())
            
            # If the bot was restarted, this task might not be valid anymore
            if task_key not in self.mute_tasks:
                return
            
            # Remove the mute
            member = guild.get_member(int(user_id))
            if not member:
                remove_mute(guild_id, user_id)
                return
            
            mute_role = await self.get_mute_role(guild)
            if not mute_role:
                return
            
            try:
                await member.remove_roles(mute_role, reason="ESCUDO: Mute duration expired")
                remove_mute(guild_id, user_id)
                
                # Try to DM the user
                try:
                    await member.send(embed=success_embed(
                        title="Mute Expired",
                        description=f"Your mute in **{guild.name}** has expired."
                    ))
                except discord.Forbidden:
                    pass
                
            except discord.Forbidden:
                pass
            
            # Remove the task from the list
            del self.mute_tasks[task_key]
        
        # Start the task
        task = asyncio.create_task(unmute_task())
        self.mute_tasks[task_key] = task
    
    @commands.command(name="prefix", help="Change the command prefix for this server")
    @commands.check(is_admin)
    async def prefix(self, ctx, new_prefix=None):
        """Change the command prefix for the server"""
        config = get_guild_config(ctx.guild.id)
        
        if new_prefix is None:
            current_prefix = config.get("prefix", CONFIG["prefix"])
            await ctx.send(embed=info_embed(
                title="Current Prefix",
                description=f"The current prefix is `{current_prefix}`"
            ))
            return
        
        # Validate the prefix
        if len(new_prefix) > 3:
            await ctx.send(embed=error_embed(
                title="Invalid Prefix",
                description="Prefix must be 3 characters or less."
            ))
            return
        
        # Update the prefix
        config["prefix"] = new_prefix
        update_guild_config(ctx.guild.id, config)
        
        await ctx.send(embed=success_embed(
            title="Prefix Changed",
            description=f"✅ Prefix has been changed to `{new_prefix}`"
        ))
    
    @commands.command(name="ban", help="Ban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a user from the server"""
        # Check if the user is trying to ban themselves
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed(
                title="Self-Ban Prevented",
                description="You cannot ban yourself."
            ))
            return
        
        # Check if the bot can ban the user
        if not ctx.guild.me.top_role > member.top_role:
            await ctx.send(embed=error_embed(
                title="Cannot Ban",
                description="I don't have permission to ban this user. Their role may be higher than mine."
            ))
            return
        
        try:
            # Send a DM to the user if possible
            try:
                ban_embed = warning_embed(
                    title=f"Banned from {ctx.guild.name}",
                    description=f"You have been banned.\nReason: {reason}"
                )
                await member.send(embed=ban_embed)
            except discord.Forbidden:
                pass
            
            # Ban the user
            await ctx.guild.ban(member, reason=f"{reason} | Banned by {ctx.author}")
            
            await ctx.send(embed=success_embed(
                title="User Banned",
                description=f"✅ {member.mention} was banned successfully.\nReason: {reason}"
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Ban Failed",
                description="I don't have permission to ban this user."
            ))
    
    @commands.command(name="unban", help="Unban a user from the server")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason="No reason provided"):
        """Unban a user from the server by ID"""
        try:
            # Get the ban entry
            user = await self.bot.fetch_user(user_id)
            if not user:
                await ctx.send(embed=error_embed(
                    title="User Not Found",
                    description=f"Could not find a user with ID {user_id}"
                ))
                return
            
            # Check if the user is actually banned
            try:
                ban_entry = await ctx.guild.fetch_ban(user)
            except discord.NotFound:
                await ctx.send(embed=error_embed(
                    title="User Not Banned",
                    description=f"{user} is not banned from this server."
                ))
                return
            
            # Unban the user
            await ctx.guild.unban(user, reason=f"{reason} | Unbanned by {ctx.author}")
            
            await ctx.send(embed=success_embed(
                title="User Unbanned",
                description=f"✅ {user} was unbanned successfully.\nReason: {reason}"
            ))
        except discord.NotFound:
            await ctx.send(embed=error_embed(
                title="User Not Found",
                description=f"Could not find a user with ID {user_id}"
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Unban Failed",
                description="I don't have permission to unban users."
            ))
    
    @commands.command(name="unbanall", help="Unban all users from the server")
    @commands.has_permissions(administrator=True)
    async def unbanall(self, ctx):
        """Unban all users from the server"""
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Unban All Confirmation",
            description="⚠️ Are you sure you want to unban all users? This cannot be undone.\nReact with ✅ to confirm or ❌ to cancel."
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
                    title="Unban All Cancelled",
                    description="Operation has been cancelled."
                ))
                return
            
            # Get all bans
            ban_list = [entry async for entry in ctx.guild.bans()]
            
            if not ban_list:
                await ctx.send(embed=info_embed(
                    title="No Bans",
                    description="There are no banned users in this server."
                ))
                return
            
            unbanned_count = 0
            
            # Send initial progress message
            progress_msg = await ctx.send(embed=info_embed(
                title="Unbanning Users",
                description=f"Unbanning 0/{len(ban_list)} users..."
            ))
            
            # Unban each user
            for entry in ban_list:
                try:
                    await ctx.guild.unban(entry.user, reason=f"Mass unban initiated by {ctx.author}")
                    unbanned_count += 1
                    
                    # Update progress every 5 unbans
                    if unbanned_count % 5 == 0:
                        await progress_msg.edit(embed=info_embed(
                            title="Unbanning Users",
                            description=f"Unbanning {unbanned_count}/{len(ban_list)} users..."
                        ))
                except:
                    continue
            
            await ctx.send(embed=success_embed(
                title="Mass Unban Complete",
                description=f"✅ Successfully unbanned {unbanned_count} users."
            ))
        
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Unban All Cancelled",
                description="Confirmation timed out after 60 seconds."
            ))
    
    @commands.command(name="kick", help="Kick a user from the server")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a user from the server"""
        # Check if the user is trying to kick themselves
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed(
                title="Self-Kick Prevented",
                description="You cannot kick yourself."
            ))
            return
        
        # Check if the bot can kick the user
        if not ctx.guild.me.top_role > member.top_role:
            await ctx.send(embed=error_embed(
                title="Cannot Kick",
                description="I don't have permission to kick this user. Their role may be higher than mine."
            ))
            return
        
        try:
            # Send a DM to the user if possible
            try:
                kick_embed = warning_embed(
                    title=f"Kicked from {ctx.guild.name}",
                    description=f"You have been kicked.\nReason: {reason}"
                )
                await member.send(embed=kick_embed)
            except discord.Forbidden:
                pass
            
            # Kick the user
            await ctx.guild.kick(member, reason=f"{reason} | Kicked by {ctx.author}")
            
            await ctx.send(embed=success_embed(
                title="User Kicked",
                description=f"✅ {member.mention} was kicked successfully.\nReason: {reason}"
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Kick Failed",
                description="I don't have permission to kick this user."
            ))
    
    @commands.command(name="warn", help="Warn a user")
    @commands.check(is_mod)
    async def warn(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Warn a user for breaking rules"""
        # Check if the user is trying to warn themselves
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed(
                title="Self-Warn Prevented",
                description="You cannot warn yourself."
            ))
            return
        
        # Add the warning
        warning_id = add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
        
        # Send a DM to the user if possible
        try:
            warn_embed = warning_embed(
                title=f"Warning in {ctx.guild.name}",
                description=f"You have received a warning.\nReason: {reason}"
            )
            await member.send(embed=warn_embed)
        except discord.Forbidden:
            pass
        
        await ctx.send(embed=success_embed(
            title="User Warned",
            description=f"✅ {member.mention} was warned successfully.\nWarning ID: {warning_id}\nReason: {reason}"
        ))
    
    @commands.command(name="warnings", aliases=["warns"], help="View a user's warnings")
    @commands.check(is_mod)
    async def warnings(self, ctx, member: discord.Member):
        """View all warnings for a user"""
        warnings = get_warnings(ctx.guild.id, member.id)
        
        if not warnings:
            await ctx.send(embed=info_embed(
                title="No Warnings",
                description=f"{member.mention} has no warnings."
            ))
            return
        
        # Create embed for warnings
        embed = info_embed(
            title=f"Warnings for {member}",
            description=f"{member.mention} has {len(warnings)} warning(s)"
        )
        
        for warning in warnings:
            moderator = ctx.guild.get_member(int(warning["moderator_id"]))
            moderator_name = moderator.mention if moderator else "Unknown Moderator"
            
            time = datetime.fromtimestamp(warning["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            
            embed.add_field(
                name=f"Warning ID: {warning['id']}",
                value=f"**Reason:** {warning['reason']}\n**Moderator:** {moderator_name}\n**Time:** {time}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="unwarn", help="Remove a warning from a user")
    @commands.check(is_mod)
    async def unwarn(self, ctx, member: discord.Member, warning_id: int):
        """Remove a specific warning from a user"""
        if remove_warning(ctx.guild.id, member.id, warning_id):
            await ctx.send(embed=success_embed(
                title="Warning Removed",
                description=f"✅ Warning #{warning_id} has been removed from {member.mention}"
            ))
        else:
            await ctx.send(embed=error_embed(
                title="Warning Not Found",
                description=f"Could not find warning #{warning_id} for {member.mention}"
            ))
    
    @commands.command(name="clearwarns", aliases=["clearwarnings"], help="Clear all warnings from a user")
    @commands.check(is_admin)
    async def clearwarns(self, ctx, member: discord.Member):
        """Clear all warnings for a user"""
        if clear_warnings(ctx.guild.id, member.id):
            await ctx.send(embed=success_embed(
                title="Warnings Cleared",
                description=f"✅ All warnings have been cleared for {member.mention}"
            ))
        else:
            await ctx.send(embed=info_embed(
                title="No Warnings",
                description=f"{member.mention} has no warnings to clear."
            ))
    
    @commands.command(name="mute", help="Mute a user")
    @commands.check(is_mod)
    async def mute(self, ctx, member: discord.Member, duration: Optional[str] = None, *, reason="No reason provided"):
        """Mute a user for a specified duration"""
        # Check if the user is trying to mute themselves
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed(
                title="Self-Mute Prevented",
                description="You cannot mute yourself."
            ))
            return
        
        # Check if the user is already muted
        if is_muted(ctx.guild.id, member.id):
            await ctx.send(embed=error_embed(
                title="Already Muted",
                description=f"{member.mention} is already muted."
            ))
            return
        
        # Parse duration if provided
        expire_time = None
        if duration:
            time_units = {
                's': 1,               # seconds
                'm': 60,              # minutes
                'h': 60 * 60,         # hours
                'd': 60 * 60 * 24,    # days
                'w': 60 * 60 * 24 * 7 # weeks
            }
            
            match = re.match(r"^(\d+)([smhdw])$", duration)
            if not match:
                await ctx.send(embed=error_embed(
                    title="Invalid Duration",
                    description="Duration must be in the format `<number><unit>` (e.g. 10s, 5m, 2h, 1d, 1w)"
                ))
                return
            
            amount, unit = match.groups()
            seconds = int(amount) * time_units[unit]
            expire_time = datetime.now() + timedelta(seconds=seconds)
            
            # Don't allow mutes longer than 28 days
            max_seconds = 60 * 60 * 24 * 28
            if seconds > max_seconds:
                await ctx.send(embed=error_embed(
                    title="Duration Too Long",
                    description="Mute duration cannot be longer than 28 days."
                ))
                return
        
        # Get the mute role
        mute_role = await self.get_mute_role(ctx.guild)
        if not mute_role:
            await ctx.send(embed=error_embed(
                title="Mute Role Error",
                description="Could not create or find a Muted role."
            ))
            return
        
        try:
            # Add the mute role
            await member.add_roles(mute_role, reason=f"{reason} | Muted by {ctx.author}")
            
            # Add mute to database
            add_mute(
                ctx.guild.id, member.id, ctx.author.id, reason,
                expire_time.timestamp() if expire_time else None
            )
            
            # Schedule unmute if duration is provided
            if expire_time:
                duration_delta = expire_time - datetime.now()
                await self.schedule_unmute(str(ctx.guild.id), str(member.id), duration_delta)
            
            # Send a DM to the user if possible
            try:
                mute_embed = warning_embed(
                    title=f"Muted in {ctx.guild.name}",
                    description=f"You have been muted.\nReason: {reason}"
                )
                if expire_time:
                    mute_embed.add_field(name="Duration", value=f"Until {expire_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                await member.send(embed=mute_embed)
            except discord.Forbidden:
                pass
            
            # Success message
            if expire_time:
                await ctx.send(embed=success_embed(
                    title="User Muted",
                    description=f"✅ {member.mention} was muted successfully.\nDuration: {duration}\nReason: {reason}"
                ))
            else:
                await ctx.send(embed=success_embed(
                    title="User Muted",
                    description=f"✅ {member.mention} was muted successfully.\nDuration: Permanent\nReason: {reason}"
                ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Mute Failed",
                description="I don't have permission to mute this user."
            ))
    
    @commands.command(name="unmute", help="Unmute a user")
    @commands.check(is_mod)
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Unmute a previously muted user"""
        # Check if the user is actually muted
        if not is_muted(ctx.guild.id, member.id):
            await ctx.send(embed=error_embed(
                title="Not Muted",
                description=f"{member.mention} is not muted."
            ))
            return
        
        # Get the mute role
        mute_role = await self.get_mute_role(ctx.guild)
        if not mute_role:
            await ctx.send(embed=error_embed(
                title="Mute Role Error",
                description="Could not find the Muted role."
            ))
            return
        
        try:
            # Remove the mute role
            await member.remove_roles(mute_role, reason=f"{reason} | Unmuted by {ctx.author}")
            
            # Remove mute from database
            remove_mute(ctx.guild.id, member.id)
            
            # Cancel any scheduled unmute task
            task_key = f"{ctx.guild.id}_{member.id}"
            if task_key in self.mute_tasks:
                self.mute_tasks[task_key].cancel()
                del self.mute_tasks[task_key]
            
            # Send a DM to the user if possible
            try:
                unmute_embed = success_embed(
                    title=f"Unmuted in {ctx.guild.name}",
                    description=f"You have been unmuted.\nReason: {reason}"
                )
                await member.send(embed=unmute_embed)
            except discord.Forbidden:
                pass
            
            await ctx.send(embed=success_embed(
                title="User Unmuted",
                description=f"✅ {member.mention} was unmuted successfully.\nReason: {reason}"
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Unmute Failed",
                description="I don't have permission to unmute this user."
            ))
    
    @commands.command(name="unmuteall", help="Unmute all users in the server")
    @commands.has_permissions(administrator=True)
    async def unmuteall(self, ctx):
        """Unmute all muted users in the server"""
        # Get the mute role
        mute_role = await self.get_mute_role(ctx.guild)
        if not mute_role:
            await ctx.send(embed=error_embed(
                title="Mute Role Error",
                description="Could not find the Muted role."
            ))
            return
        
        # Find all members with the mute role
        muted_members = [member for member in ctx.guild.members if mute_role in member.roles]
        
        if not muted_members:
            await ctx.send(embed=info_embed(
                title="No Muted Users",
                description="There are no muted users in this server."
            ))
            return
        
        unmuted_count = 0
        
        # Unmute each member
        for member in muted_members:
            try:
                await member.remove_roles(mute_role, reason=f"Mass unmute initiated by {ctx.author}")
                remove_mute(ctx.guild.id, member.id)
                
                # Cancel any scheduled unmute task
                task_key = f"{ctx.guild.id}_{member.id}"
                if task_key in self.mute_tasks:
                    self.mute_tasks[task_key].cancel()
                    del self.mute_tasks[task_key]
                
                unmuted_count += 1
            except discord.Forbidden:
                continue
        
        await ctx.send(embed=success_embed(
            title="Mass Unmute Complete",
            description=f"✅ Successfully unmuted {unmuted_count} users."
        ))
    
    @commands.command(name="chatban", aliases=["textmute"], help="Ban a user from sending messages")
    @commands.check(is_mod)
    async def chatban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Prevent a user from sending messages in text channels"""
        # Check if the user is trying to chatban themselves
        if member.id == ctx.author.id:
            await ctx.send(embed=error_embed(
                title="Self-Chatban Prevented",
                description="You cannot chatban yourself."
            ))
            return
        
        try:
            # Set permissions in all text channels
            for channel in ctx.guild.text_channels:
                try:
                    await channel.set_permissions(member, send_messages=False, reason=f"{reason} | Chatbanned by {ctx.author}")
                except discord.Forbidden:
                    continue
            
            # Send a DM to the user if possible
            try:
                chatban_embed = warning_embed(
                    title=f"Chat Banned in {ctx.guild.name}",
                    description=f"You have been banned from sending messages.\nReason: {reason}"
                )
                await member.send(embed=chatban_embed)
            except discord.Forbidden:
                pass
            
            await ctx.send(embed=success_embed(
                title="User Chat Banned",
                description=f"✅ {member.mention} was banned from sending messages.\nReason: {reason}"
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Chat Ban Failed",
                description="I don't have permission to manage channel permissions."
            ))
    
    @commands.command(name="chatunban", aliases=["textunmute"], help="Unban a user from text channels")
    @commands.check(is_mod)
    async def chatunban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Allow a user to send messages in text channels again"""
        try:
            # Reset permissions in all text channels
            for channel in ctx.guild.text_channels:
                try:
                    # Get the current overwrite
                    overwrite = channel.overwrites_for(member)
                    
                    # If send_messages is not None (explicitly set), reset it
                    if overwrite.send_messages is not None:
                        overwrite.send_messages = None
                        
                        # If the overwrite becomes empty, remove it completely
                        if overwrite.is_empty():
                            await channel.set_permissions(member, overwrite=None, reason=f"{reason} | Chat unbanned by {ctx.author}")
                        else:
                            await channel.set_permissions(member, overwrite=overwrite, reason=f"{reason} | Chat unbanned by {ctx.author}")
                except discord.Forbidden:
                    continue
            
            # Send a DM to the user if possible
            try:
                chatunban_embed = success_embed(
                    title=f"Chat Unbanned in {ctx.guild.name}",
                    description=f"You can now send messages again.\nReason: {reason}"
                )
                await member.send(embed=chatunban_embed)
            except discord.Forbidden:
                pass
            
            await ctx.send(embed=success_embed(
                title="User Chat Unbanned",
                description=f"✅ {member.mention} can now send messages again.\nReason: {reason}"
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Chat Unban Failed",
                description="I don't have permission to manage channel permissions."
            ))
    
    @commands.command(name="nick", aliases=["nickname"], help="Change a user's nickname")
    @commands.check(is_mod)
    async def nick(self, ctx, member: discord.Member, *, new_nickname=None):
        """Change a user's nickname"""
        try:
            await member.edit(nick=new_nickname, reason=f"Nickname changed by {ctx.author}")
            
            if new_nickname:
                await ctx.send(embed=success_embed(
                    title="Nickname Changed",
                    description=f"✅ {member.mention}'s nickname has been changed to **{new_nickname}**"
                ))
            else:
                await ctx.send(embed=success_embed(
                    title="Nickname Reset",
                    description=f"✅ {member.mention}'s nickname has been reset"
                ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Nickname Change Failed",
                description="I don't have permission to change that user's nickname. They might have a higher role than me."
            ))
    
    @commands.command(name="purge", aliases=["clear"], help="Delete a specified number of messages")
    @commands.check(is_mod)
    async def purge(self, ctx, amount: int):
        """Delete a specified number of messages from the channel"""
        if amount <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Amount",
                description="Please specify a positive number."
            ))
            return
        
        if amount > 100:
            await ctx.send(embed=error_embed(
                title="Amount Too Large",
                description="You can only purge up to 100 messages at once."
            ))
            return
        
        # Delete the command message first
        await ctx.message.delete()
        
        # Delete the specified number of messages
        deleted = await ctx.channel.purge(limit=amount)
        
        # Send a confirmation message that will delete itself after 5 seconds
        await temp_message(ctx, embed=success_embed(
            title="Messages Purged",
            description=f"✅ Successfully deleted {len(deleted)} messages."
        ), seconds=5)
    
    @commands.command(name="purgebots", help="Delete messages from bots")
    @commands.check(is_mod)
    async def purgebots(self, ctx, amount: int = 100):
        """Delete messages from bots in the channel"""
        if amount <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Amount",
                description="Please specify a positive number."
            ))
            return
        
        if amount > 100:
            await ctx.send(embed=error_embed(
                title="Amount Too Large",
                description="You can only purge up to 100 messages at once."
            ))
            return
        
        # Delete the command message first
        await ctx.message.delete()
        
        # Delete messages from bots
        def is_bot(message):
            return message.author.bot
        
        deleted = await ctx.channel.purge(limit=amount, check=is_bot)
        
        # Send a confirmation message that will delete itself after 5 seconds
        await temp_message(ctx, embed=success_embed(
            title="Bot Messages Purged",
            description=f"✅ Successfully deleted {len(deleted)} bot messages."
        ), seconds=5)
    
    @commands.command(name="purgeuser", aliases=["clearuser"], help="Delete messages from a specific user")
    @commands.check(is_mod)
    async def purgeuser(self, ctx, user: discord.Member, amount: int = 100):
        """Delete messages from a specific user in the channel"""
        if amount <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Amount",
                description="Please specify a positive number."
            ))
            return
        
        if amount > 100:
            await ctx.send(embed=error_embed(
                title="Amount Too Large",
                description="You can only purge up to 100 messages at once."
            ))
            return
        
        # Delete the command message first
        await ctx.message.delete()
        
        # Delete messages from the specified user
        def is_user(message):
            return message.author.id == user.id
        
        deleted = await ctx.channel.purge(limit=amount, check=is_user)
        
        # Send a confirmation message that will delete itself after 5 seconds
        await temp_message(ctx, embed=success_embed(
            title="User Messages Purged",
            description=f"✅ Successfully deleted {len(deleted)} messages from {user.mention}."
        ), seconds=5)
    
    @commands.command(name="purgecontains", aliases=["clearcontains"], help="Delete messages containing specific text")
    @commands.check(is_mod)
    async def purgecontains(self, ctx, text: str, amount: int = 100):
        """Delete messages containing specific text"""
        if amount <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Amount",
                description="Please specify a positive number."
            ))
            return
        
        if amount > 100:
            await ctx.send(embed=error_embed(
                title="Amount Too Large",
                description="You can only purge up to 100 messages at once."
            ))
            return
        
        # Delete the command message first
        await ctx.message.delete()
        
        # Delete messages containing the specified text
        def contains_text(message):
            return text.lower() in message.content.lower()
        
        deleted = await ctx.channel.purge(limit=amount, check=contains_text)
        
        # Send a confirmation message that will delete itself after 5 seconds
        await temp_message(ctx, embed=success_embed(
            title="Messages Purged",
            description=f"✅ Successfully deleted {len(deleted)} messages containing '{text}'."
        ), seconds=5)
    
    @commands.command(name="purgeemoji", aliases=["clearemoji"], help="Delete messages containing emojis")
    @commands.check(is_mod)
    async def purgeemoji(self, ctx, amount: int = 100):
        """Delete messages containing emojis"""
        if amount <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Amount",
                description="Please specify a positive number."
            ))
            return
        
        if amount > 100:
            await ctx.send(embed=error_embed(
                title="Amount Too Large",
                description="You can only purge up to 100 messages at once."
            ))
            return
        
        # Delete the command message first
        await ctx.message.delete()
        
        # Emoji pattern to match both Unicode emojis and Discord custom emojis
        emoji_pattern = re.compile(r'<a?:[a-zA-Z0-9_]+:\d+>|[\U00010000-\U0010ffff]', flags=re.UNICODE)
        
        # Delete messages containing emojis
        def contains_emoji(message):
            return bool(emoji_pattern.search(message.content))
        
        deleted = await ctx.channel.purge(limit=amount, check=contains_emoji)
        
        # Send a confirmation message that will delete itself after 5 seconds
        await temp_message(ctx, embed=success_embed(
            title="Emoji Messages Purged",
            description=f"✅ Successfully deleted {len(deleted)} messages containing emojis."
        ), seconds=5)
    
    @commands.command(name="purgeimage", aliases=["clearimage"], help="Delete messages containing images")
    @commands.check(is_mod)
    async def purgeimage(self, ctx, amount: int = 100):
        """Delete messages containing images/attachments"""
        if amount <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Amount",
                description="Please specify a positive number."
            ))
            return
        
        if amount > 100:
            await ctx.send(embed=error_embed(
                title="Amount Too Large",
                description="You can only purge up to 100 messages at once."
            ))
            return
        
        # Delete the command message first
        await ctx.message.delete()
        
        # Delete messages containing attachments or embeds with images
        def has_image(message):
            # Check for attachments
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith("image/"):
                        return True
            
            # Check for embeds with images
            if message.embeds:
                for embed in message.embeds:
                    if embed.image or embed.thumbnail:
                        return True
            
            return False
        
        deleted = await ctx.channel.purge(limit=amount, check=has_image)
        
        # Send a confirmation message that will delete itself after 5 seconds
        await temp_message(ctx, embed=success_embed(
            title="Image Messages Purged",
            description=f"✅ Successfully deleted {len(deleted)} messages containing images."
        ), seconds=5)
    
    @commands.command(name="snipe", help="See the last deleted message in the channel")
    @commands.check(is_mod)
    async def snipe(self, ctx):
        """View the last message deleted in the current channel"""
        channel_id = str(ctx.channel.id)
        
        if channel_id not in self.snipe_messages or not self.snipe_messages[channel_id]:
            await ctx.send(embed=error_embed(
                title="No Sniped Messages",
                description="There are no deleted messages to snipe in this channel."
            ))
            return
        
        # Get the most recent deleted message
        message = self.snipe_messages[channel_id][-1]
        
        # Create and send the embed
        embed = discord.Embed(
            description=message["content"],
            color=CONFIG["embed_color"],
            timestamp=message["created_at"]
        )
        
        embed.set_author(name=f"{message['author']}", icon_url=message["avatar_url"])
        embed.set_footer(text=f"Sniped by {ctx.author}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="role", help="Add or remove a role from a user")
    @commands.check(is_mod)
    async def role(self, ctx, member: discord.Member, *, role: discord.Role):
        """Add or remove a role from a user"""
        # Check if the bot has permission to manage roles
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage roles."
            ))
            return
        
        # Check if the role is higher than the bot's highest role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send(embed=error_embed(
                title="Role Too High",
                description="I can't assign or remove roles that are higher than or equal to my highest role."
            ))
            return
        
        try:
            if role in member.roles:
                # Remove the role
                await member.remove_roles(role, reason=f"Role removed by {ctx.author}")
                await ctx.send(embed=success_embed(
                    title="Role Removed",
                    description=f"✅ Removed {role.mention} from {member.mention}"
                ))
            else:
                # Add the role
                await member.add_roles(role, reason=f"Role added by {ctx.author}")
                await ctx.send(embed=success_embed(
                    title="Role Added",
                    description=f"✅ Added {role.mention} to {member.mention}"
                ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Role Assignment Failed",
                description="I don't have permission to assign or remove that role."
            ))
    
    @commands.command(name="roleall", help="Add a role to all members")
    @commands.has_permissions(administrator=True)
    async def roleall(self, ctx, *, role: discord.Role):
        """Add a role to all members in the server"""
        # Check if the bot has permission to manage roles
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage roles."
            ))
            return
        
        # Check if the role is higher than the bot's highest role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send(embed=error_embed(
                title="Role Too High",
                description="I can't assign roles that are higher than or equal to my highest role."
            ))
            return
        
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Role All Confirmation",
            description=f"⚠️ Are you sure you want to add {role.mention} to all members? This will affect {len(ctx.guild.members)} members.\n\nReact with ✅ to confirm or ❌ to cancel."
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
                    title="Role All Cancelled",
                    description="Operation has been cancelled."
                ))
                return
            
            # Count members who don't already have the role
            members_to_add = [member for member in ctx.guild.members if role not in member.roles]
            
            if not members_to_add:
                await ctx.send(embed=info_embed(
                    title="No Members",
                    description=f"All members already have the {role.mention} role."
                ))
                return
            
            added_count = 0
            
            # Send initial progress message
            progress_msg = await ctx.send(embed=info_embed(
                title="Adding Roles",
                description=f"Adding role to 0/{len(members_to_add)} members..."
            ))
            
            # Add role to each member
            for member in members_to_add:
                try:
                    await member.add_roles(role, reason=f"Mass role add initiated by {ctx.author}")
                    added_count += 1
                    
                    # Update progress every 5 members
                    if added_count % 5 == 0:
                        await progress_msg.edit(embed=info_embed(
                            title="Adding Roles",
                            description=f"Adding role to {added_count}/{len(members_to_add)} members..."
                        ))
                except:
                    continue
            
            await ctx.send(embed=success_embed(
                title="Mass Role Add Complete",
                description=f"✅ Successfully added {role.mention} to {added_count} members."
            ))
        
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Role All Cancelled",
                description="Confirmation timed out after 60 seconds."
            ))
    
    @commands.command(name="rolehumans", help="Add a role to all human members")
    @commands.has_permissions(administrator=True)
    async def rolehumans(self, ctx, *, role: discord.Role):
        """Add a role to all human (non-bot) members in the server"""
        # Check if the bot has permission to manage roles
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage roles."
            ))
            return
        
        # Check if the role is higher than the bot's highest role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send(embed=error_embed(
                title="Role Too High",
                description="I can't assign roles that are higher than or equal to my highest role."
            ))
            return
        
        # Count human members who don't already have the role
        members_to_add = [member for member in ctx.guild.members if not member.bot and role not in member.roles]
        
        if not members_to_add:
            await ctx.send(embed=info_embed(
                title="No Members",
                description=f"All human members already have the {role.mention} role."
            ))
            return
        
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Role Humans Confirmation",
            description=f"⚠️ Are you sure you want to add {role.mention} to all human members? This will affect {len(members_to_add)} members.\n\nReact with ✅ to confirm or ❌ to cancel."
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
                    title="Role Humans Cancelled",
                    description="Operation has been cancelled."
                ))
                return
            
            added_count = 0
            
            # Send initial progress message
            progress_msg = await ctx.send(embed=info_embed(
                title="Adding Roles",
                description=f"Adding role to 0/{len(members_to_add)} human members..."
            ))
            
            # Add role to each human member
            for member in members_to_add:
                try:
                    await member.add_roles(role, reason=f"Mass role add to humans initiated by {ctx.author}")
                    added_count += 1
                    
                    # Update progress every 5 members
                    if added_count % 5 == 0:
                        await progress_msg.edit(embed=info_embed(
                            title="Adding Roles",
                            description=f"Adding role to {added_count}/{len(members_to_add)} human members..."
                        ))
                except:
                    continue
            
            await ctx.send(embed=success_embed(
                title="Mass Role Add Complete",
                description=f"✅ Successfully added {role.mention} to {added_count} human members."
            ))
        
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Role Humans Cancelled",
                description="Confirmation timed out after 60 seconds."
            ))
    
    @commands.command(name="rolebots", help="Add a role to all bots")
    @commands.has_permissions(administrator=True)
    async def rolebots(self, ctx, *, role: discord.Role):
        """Add a role to all bot members in the server"""
        # Check if the bot has permission to manage roles
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage roles."
            ))
            return
        
        # Check if the role is higher than the bot's highest role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send(embed=error_embed(
                title="Role Too High",
                description="I can't assign roles that are higher than or equal to my highest role."
            ))
            return
        
        # Count bot members who don't already have the role
        members_to_add = [member for member in ctx.guild.members if member.bot and role not in member.roles]
        
        if not members_to_add:
            await ctx.send(embed=info_embed(
                title="No Members",
                description=f"All bot members already have the {role.mention} role."
            ))
            return
        
        # Add role to each bot member
        added_count = 0
        for member in members_to_add:
            try:
                await member.add_roles(role, reason=f"Mass role add to bots initiated by {ctx.author}")
                added_count += 1
            except:
                continue
        
        await ctx.send(embed=success_embed(
            title="Mass Role Add Complete",
            description=f"✅ Successfully added {role.mention} to {added_count} bot members."
        ))
    
    @commands.command(name="lock", help="Lock a channel")
    @commands.check(is_mod)
    async def lock(self, ctx, channel: discord.TextChannel = None):
        """Lock a channel to prevent regular users from sending messages"""
        channel = channel or ctx.channel
        
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # Prevent @everyone from sending messages
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=False)
            await ctx.send(embed=success_embed(
                title="Channel Locked",
                description=f"✅ {channel.mention} has been locked."
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Lock Failed",
                description="I don't have permission to lock this channel."
            ))
    
    @commands.command(name="unlock", help="Unlock a channel")
    @commands.check(is_mod)
    async def unlock(self, ctx, channel: discord.TextChannel = None):
        """Unlock a channel to allow regular users to send messages"""
        channel = channel or ctx.channel
        
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # Allow @everyone to send messages
        try:
            await channel.set_permissions(ctx.guild.default_role, send_messages=None)
            await ctx.send(embed=success_embed(
                title="Channel Unlocked",
                description=f"✅ {channel.mention} has been unlocked."
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Unlock Failed",
                description="I don't have permission to unlock this channel."
            ))
    
    @commands.command(name="lockall", help="Lock all channels")
    @commands.has_permissions(administrator=True)
    async def lockall(self, ctx):
        """Lock all text channels in the server"""
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Lock All Confirmation",
            description=f"⚠️ Are you sure you want to lock all text channels? This will prevent regular users from sending messages.\n\nReact with ✅ to confirm or ❌ to cancel."
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
                    title="Lock All Cancelled",
                    description="Operation has been cancelled."
                ))
                return
            
            # Lock all text channels
            locked_count = 0
            progress_msg = await ctx.send(embed=info_embed(
                title="Locking Channels",
                description=f"Locking 0/{len(ctx.guild.text_channels)} channels..."
            ))
            
            for channel in ctx.guild.text_channels:
                try:
                    await channel.set_permissions(ctx.guild.default_role, send_messages=False)
                    locked_count += 1
                    
                    # Update progress every 5 channels
                    if locked_count % 5 == 0:
                        await progress_msg.edit(embed=info_embed(
                            title="Locking Channels",
                            description=f"Locking {locked_count}/{len(ctx.guild.text_channels)} channels..."
                        ))
                except:
                    continue
            
            await ctx.send(embed=success_embed(
                title="Mass Lock Complete",
                description=f"✅ Successfully locked {locked_count} text channels."
            ))
        
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Lock All Cancelled",
                description="Confirmation timed out after 60 seconds."
            ))
    
    @commands.command(name="unlockall", help="Unlock all channels")
    @commands.has_permissions(administrator=True)
    async def unlockall(self, ctx):
        """Unlock all text channels in the server"""
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Unlock All Confirmation",
            description=f"⚠️ Are you sure you want to unlock all text channels? This will allow regular users to send messages.\n\nReact with ✅ to confirm or ❌ to cancel."
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
                    title="Unlock All Cancelled",
                    description="Operation has been cancelled."
                ))
                return
            
            # Unlock all text channels
            unlocked_count = 0
            progress_msg = await ctx.send(embed=info_embed(
                title="Unlocking Channels",
                description=f"Unlocking 0/{len(ctx.guild.text_channels)} channels..."
            ))
            
            for channel in ctx.guild.text_channels:
                try:
                    await channel.set_permissions(ctx.guild.default_role, send_messages=None)
                    unlocked_count += 1
                    
                    # Update progress every 5 channels
                    if unlocked_count % 5 == 0:
                        await progress_msg.edit(embed=info_embed(
                            title="Unlocking Channels",
                            description=f"Unlocking {unlocked_count}/{len(ctx.guild.text_channels)} channels..."
                        ))
                except:
                    continue
            
            await ctx.send(embed=success_embed(
                title="Mass Unlock Complete",
                description=f"✅ Successfully unlocked {unlocked_count} text channels."
            ))
        
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Unlock All Cancelled",
                description="Confirmation timed out after 60 seconds."
            ))
    
    @commands.command(name="hide", help="Hide a channel from regular users")
    @commands.check(is_mod)
    async def hide(self, ctx, channel: discord.TextChannel = None):
        """Hide a channel from regular users"""
        channel = channel or ctx.channel
        
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # Hide the channel from @everyone
        try:
            await channel.set_permissions(ctx.guild.default_role, view_channel=False)
            await ctx.send(embed=success_embed(
                title="Channel Hidden",
                description=f"✅ {channel.mention} has been hidden from regular users."
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Hide Failed",
                description="I don't have permission to hide this channel."
            ))
    
    @commands.command(name="unhide", help="Unhide a channel")
    @commands.check(is_mod)
    async def unhide(self, ctx, channel: discord.TextChannel = None):
        """Unhide a channel for regular users"""
        channel = channel or ctx.channel
        
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # Unhide the channel for @everyone
        try:
            await channel.set_permissions(ctx.guild.default_role, view_channel=None)
            await ctx.send(embed=success_embed(
                title="Channel Unhidden",
                description=f"✅ {channel.mention} has been unhidden for regular users."
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Unhide Failed",
                description="I don't have permission to unhide this channel."
            ))
    
    @commands.command(name="hideall", help="Hide all channels from regular users")
    @commands.has_permissions(administrator=True)
    async def hideall(self, ctx):
        """Hide all channels from regular users"""
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Hide All Confirmation",
            description=f"⚠️ Are you sure you want to hide all channels? Regular users won't be able to see any channels.\n\nReact with ✅ to confirm or ❌ to cancel."
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
                    title="Hide All Cancelled",
                    description="Operation has been cancelled."
                ))
                return
            
            # Hide all channels
            hidden_count = 0
            progress_msg = await ctx.send(embed=info_embed(
                title="Hiding Channels",
                description=f"Hiding 0/{len(ctx.guild.channels)} channels..."
            ))
            
            for channel in ctx.guild.channels:
                try:
                    await channel.set_permissions(ctx.guild.default_role, view_channel=False)
                    hidden_count += 1
                    
                    # Update progress every 5 channels
                    if hidden_count % 5 == 0:
                        await progress_msg.edit(embed=info_embed(
                            title="Hiding Channels",
                            description=f"Hiding {hidden_count}/{len(ctx.guild.channels)} channels..."
                        ))
                except:
                    continue
            
            await ctx.send(embed=success_embed(
                title="Mass Hide Complete",
                description=f"✅ Successfully hidden {hidden_count} channels."
            ))
        
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Hide All Cancelled",
                description="Confirmation timed out after 60 seconds."
            ))
    
    @commands.command(name="unhideall", help="Unhide all channels")
    @commands.has_permissions(administrator=True)
    async def unhideall(self, ctx):
        """Unhide all channels for regular users"""
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Unhide All Confirmation",
            description=f"⚠️ Are you sure you want to unhide all channels? Regular users will be able to see all channels.\n\nReact with ✅ to confirm or ❌ to cancel."
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
                    title="Unhide All Cancelled",
                    description="Operation has been cancelled."
                ))
                return
            
            # Unhide all channels
            unhidden_count = 0
            progress_msg = await ctx.send(embed=info_embed(
                title="Unhiding Channels",
                description=f"Unhiding 0/{len(ctx.guild.channels)} channels..."
            ))
            
            for channel in ctx.guild.channels:
                try:
                    await channel.set_permissions(ctx.guild.default_role, view_channel=None)
                    unhidden_count += 1
                    
                    # Update progress every 5 channels
                    if unhidden_count % 5 == 0:
                        await progress_msg.edit(embed=info_embed(
                            title="Unhiding Channels",
                            description=f"Unhiding {unhidden_count}/{len(ctx.guild.channels)} channels..."
                        ))
                except:
                    continue
            
            await ctx.send(embed=success_embed(
                title="Mass Unhide Complete",
                description=f"✅ Successfully unhidden {unhidden_count} channels."
            ))
        
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Unhide All Cancelled",
                description="Confirmation timed out after 60 seconds."
            ))
    
    @commands.command(name="slowmode", aliases=["slow"], help="Set slowmode for a channel")
    @commands.check(is_mod)
    async def slowmode(self, ctx, seconds: int = None, channel: discord.TextChannel = None):
        """Set slowmode (rate limiting) for a channel"""
        channel = channel or ctx.channel
        
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # If no seconds are provided, show the current slowmode
        if seconds is None:
            current = channel.slowmode_delay
            if current == 0:
                await ctx.send(embed=info_embed(
                    title="Current Slowmode",
                    description=f"{channel.mention} has no slowmode set."
                ))
            else:
                await ctx.send(embed=info_embed(
                    title="Current Slowmode",
                    description=f"{channel.mention} has a slowmode of {current} seconds."
                ))
            return
        
        # Validate the slowmode value
        if seconds < 0:
            await ctx.send(embed=error_embed(
                title="Invalid Value",
                description="Slowmode seconds cannot be negative."
            ))
            return
        
        if seconds > 21600:  # Discord's maximum is 6 hours (21600 seconds)
            await ctx.send(embed=error_embed(
                title="Invalid Value",
                description="Slowmode cannot be more than 6 hours (21600 seconds)."
            ))
            return
        
        # Set the slowmode
        try:
            await channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                await ctx.send(embed=success_embed(
                    title="Slowmode Disabled",
                    description=f"✅ Slowmode has been disabled for {channel.mention}"
                ))
            else:
                await ctx.send(embed=success_embed(
                    title="Slowmode Set",
                    description=f"✅ Slowmode has been set to {seconds} seconds for {channel.mention}"
                ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Slowmode Failed",
                description="I don't have permission to set slowmode for this channel."
            ))
    
    @commands.command(name="ignore", help="Ignore a channel for moderation commands")
    @commands.check(is_admin)
    async def ignore(self, ctx, channel: discord.TextChannel = None):
        """Add a channel to the ignored list for moderation commands"""
        channel = channel or ctx.channel
        config = get_guild_config(ctx.guild.id)
        
        if "ignored_channels" not in config:
            config["ignored_channels"] = []
        
        channel_id = str(channel.id)
        
        if channel_id in config["ignored_channels"]:
            # Remove from ignored channels
            config["ignored_channels"].remove(channel_id)
            update_guild_config(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Channel Unignored",
                description=f"✅ {channel.mention} will no longer be ignored for moderation commands."
            ))
        else:
            # Add to ignored channels
            config["ignored_channels"].append(channel_id)
            update_guild_config(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Channel Ignored",
                description=f"✅ {channel.mention} will now be ignored for moderation commands."
            ))
    
    @commands.command(name="list", aliases=["ignored"], help="List ignored channels")
    @commands.check(is_mod)
    async def list_ignored(self, ctx):
        """List all channels that are ignored for moderation commands"""
        config = get_guild_config(ctx.guild.id)
        ignored_channels = config.get("ignored_channels", [])
        
        if not ignored_channels:
            await ctx.send(embed=info_embed(
                title="No Ignored Channels",
                description="There are no channels being ignored for moderation commands."
            ))
            return
        
        # Create a list of channel mentions
        channel_mentions = []
        for channel_id in ignored_channels:
            channel = ctx.guild.get_channel(int(channel_id))
            if channel:
                channel_mentions.append(f"• {channel.mention}")
        
        if not channel_mentions:
            await ctx.send(embed=info_embed(
                title="No Valid Ignored Channels",
                description="There are no valid channels being ignored for moderation commands."
            ))
            return
        
        await ctx.send(embed=info_embed(
            title="Ignored Channels",
            description="\n".join(channel_mentions)
        ))
    
    @commands.command(name="mediachannel", aliases=["media"], help="Set a channel as media-only")
    @commands.check(is_admin)
    async def mediachannel(self, ctx, channel: discord.TextChannel = None):
        """Set or unset a channel as media-only (images, videos, links only)"""
        channel = channel or ctx.channel
        config = get_guild_config(ctx.guild.id)
        
        if "media_channels" not in config:
            config["media_channels"] = []
        
        channel_id = str(channel.id)
        
        if channel_id in config["media_channels"]:
            # Remove from media channels
            config["media_channels"].remove(channel_id)
            update_guild_config(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Media Channel Disabled",
                description=f"✅ {channel.mention} is no longer a media-only channel."
            ))
        else:
            # Add to media channels
            config["media_channels"].append(channel_id)
            update_guild_config(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Media Channel Enabled",
                description=f"✅ {channel.mention} is now a media-only channel. Only messages with images, videos, or links will be allowed."
            ))
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check messages in media-only channels"""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Get guild config
        config = get_guild_config(message.guild.id)
        media_channels = config.get("media_channels", [])
        
        # Check if this is a media channel
        if str(message.channel.id) in media_channels:
            # Check if the message has any attachments, embeds, or links
            has_media = False
            
            # Check for attachments
            if message.attachments:
                has_media = True
            
            # Check for embeds
            if message.embeds:
                has_media = True
            
            # Check for links in content
            if message.content:
                # Simple URL detection regex
                url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
                if url_pattern.search(message.content):
                    has_media = True
            
            # If no media, delete the message
            if not has_media:
                try:
                    await message.delete()
                    
                    # Send a warning DM to the user
                    try:
                        await message.author.send(embed=warning_embed(
                            title="Message Deleted",
                            description=f"Your message in {message.channel.mention} was deleted because it did not contain any media (images, videos, or links).\n\nThis channel is set to media-only mode."
                        ))
                    except discord.Forbidden:
                        pass
                except discord.Forbidden:
                    pass
    
    @commands.command(name="sanatise", aliases=["sanitize", "clean"], help="Clean a channel of unwanted messages")
    @commands.check(is_admin)
    async def sanatise(self, ctx, limit: int = 100, *, content_type=None):
        """Clean a channel of unwanted message types"""
        if limit <= 0:
            await ctx.send(embed=error_embed(
                title="Invalid Limit",
                description="Please specify a positive number."
            ))
            return
        
        if limit > 100:
            await ctx.send(embed=error_embed(
                title="Limit Too Large",
                description="You can only clean up to 100 messages at once."
            ))
            return
        
        # Delete the command message
        await ctx.message.delete()
        
        valid_types = ["bot", "human", "image", "embed", "link", "emoji", "text"]
        
        if content_type and content_type.lower() not in valid_types:
            await ctx.send(embed=error_embed(
                title="Invalid Type",
                description=f"Valid types are: {', '.join(valid_types)}"
            ))
            return
        
        # Create a check function based on the content type
        def check_message(message):
            if content_type == "bot":
                return message.author.bot
            elif content_type == "human":
                return not message.author.bot
            elif content_type == "image":
                has_image = False
                # Check for attachments
                if message.attachments:
                    for attachment in message.attachments:
                        if attachment.content_type and attachment.content_type.startswith("image/"):
                            has_image = True
                            break
                
                # Check for embeds with images
                if message.embeds:
                    for embed in message.embeds:
                        if embed.image or embed.thumbnail:
                            has_image = True
                            break
                
                return has_image
            elif content_type == "embed":
                return bool(message.embeds)
            elif content_type == "link":
                # Simple URL detection regex
                url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
                return bool(url_pattern.search(message.content))
            elif content_type == "emoji":
                # Emoji pattern to match both Unicode emojis and Discord custom emojis
                emoji_pattern = re.compile(r'<a?:[a-zA-Z0-9_]+:\d+>|[\U00010000-\U0010ffff]', flags=re.UNICODE)
                return bool(emoji_pattern.search(message.content))
            elif content_type == "text":
                # Only text with no attachments or embeds
                return not (message.attachments or message.embeds) and message.content
            else:
                # If no type specified, clean all messages
                return True
        
        try:
            # Purge messages based on the check
            deleted = await ctx.channel.purge(limit=limit, check=check_message)
            
            # Send a confirmation message that will delete itself after 5 seconds
            if content_type:
                await temp_message(ctx, embed=success_embed(
                    title="Channel Cleaned",
                    description=f"✅ Successfully deleted {len(deleted)} messages of type '{content_type}'."
                ), seconds=5)
            else:
                await temp_message(ctx, embed=success_embed(
                    title="Channel Cleaned",
                    description=f"✅ Successfully deleted {len(deleted)} messages."
                ), seconds=5)
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Clean Failed",
                description="I don't have permission to delete messages in this channel."
            ))

async def setup(bot):
    await bot.add_cog(Moderation(bot))
