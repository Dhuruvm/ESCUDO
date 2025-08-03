import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta
from config import CONFIG
from utils.helpers import (
    is_whitelisted, add_to_whitelist, remove_from_whitelist, reset_whitelist,
    get_whitelisted_users, get_guild_config, update_guild_config,
    is_nightmode_active
)
from utils.embeds import success_embed, error_embed, info_embed, warning_embed
from utils.permission import (
    owner_only, extra_owner_only, admin_only, mod_only, 
    antinuke_whitelisted_only, developer_only, 
    is_owner, is_extra_owner, is_admin, is_mod
)

class Antinuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.antinuke_events = {}
        self.nightmode_check.start()
    
    def cog_unload(self):
        self.nightmode_check.cancel()
    
    @tasks.loop(minutes=5)
    async def nightmode_check(self):
        """Check and enforce nightmode settings for all guilds"""
        for guild in self.bot.guilds:
            try:
                if is_nightmode_active(guild.id):
                    # Lock all channels during nightmode
                    config = get_guild_config(guild.id)
                    ignored_channels = config.get("ignored_channels", [])
                    
                    for channel in guild.text_channels:
                        if str(channel.id) not in ignored_channels:
                            # Lock channel for @everyone
                            try:
                                await channel.set_permissions(guild.default_role, send_messages=False)
                            except discord.Forbidden:
                                continue
            except Exception as e:
                continue
    
    @nightmode_check.before_loop
    async def before_nightmode_check(self):
        await self.bot.wait_until_ready()
    
    @commands.command(name="antinuke", aliases=["an"], help="Toggle antinuke protection")
    @admin_only()
    async def antinuke(self, ctx, status: str = None):
        """Toggle antinuke protection for the server"""
        config = get_guild_config(ctx.guild.id)
        
        if status is None:
            # Display current status
            status = "enabled" if config.get("antinuke", {}).get("enabled", True) else "disabled"
            await ctx.send(embed=info_embed(
                title="Antinuke Status",
                description=f"Antinuke protection is currently **{status}**."
            ))
            return
        
        if status.lower() not in ["on", "off", "enable", "disable", "enabled", "disabled"]:
            await ctx.send(embed=error_embed(
                title="Invalid Option",
                description="Please use `on`/`off` or `enable`/`disable`."
            ))
            return
        
        # Update antinuke status
        enabled = status.lower() in ["on", "enable", "enabled"]
        config["antinuke"]["enabled"] = enabled
        update_guild_config(ctx.guild.id, config)
        
        await ctx.send(embed=success_embed(
            title="Antinuke Updated",
            description=f"Antinuke protection is now **{'enabled' if enabled else 'disabled'}**."
        ))
    
    @commands.command(name="whitelist", aliases=["wl"], help="Whitelist a user from antinuke")
    @admin_only()
    async def whitelist(self, ctx, user: discord.User):
        """Whitelist a user from the antinuke system"""
        if add_to_whitelist(ctx.guild.id, user.id):
            await ctx.send(embed=success_embed(
                title="User Whitelisted",
                description=f"✅ {user.mention} has been whitelisted from antinuke detection."
            ))
        else:
            await ctx.send(embed=info_embed(
                title="Already Whitelisted",
                description=f"{user.mention} is already whitelisted."
            ))
    
    @commands.command(name="unwhitelist", aliases=["unwl"], help="Remove a user from the whitelist")
    @admin_only()
    async def unwhitelist(self, ctx, user: discord.User):
        """Remove a user from the antinuke whitelist"""
        if remove_from_whitelist(ctx.guild.id, user.id):
            await ctx.send(embed=success_embed(
                title="User Unwhitelisted",
                description=f"✅ {user.mention} has been removed from the whitelist."
            ))
        else:
            await ctx.send(embed=error_embed(
                title="Not Whitelisted",
                description=f"{user.mention} is not on the whitelist."
            ))
    
    @commands.command(name="wlisted", aliases=["wlist"], help="List all whitelisted users")
    @admin_only()
    async def wlisted(self, ctx):
        """Show all users whitelisted from antinuke"""
        whitelisted = get_whitelisted_users(ctx.guild.id)
        
        if not whitelisted:
            await ctx.send(embed=info_embed(
                title="Whitelist Empty",
                description="No users are currently whitelisted."
            ))
            return
        
        users = []
        for user_id in whitelisted:
            user = self.bot.get_user(int(user_id))
            if user:
                users.append(f"• {user.mention} ({user.name}#{user.discriminator}) - ID: {user.id}")
            else:
                users.append(f"• Unknown User - ID: {user_id}")
        
        embed = info_embed(
            title="Whitelisted Users",
            description="\n".join(users[:20])  # Show only first 20 users
        )
        
        if len(users) > 20:
            embed.set_footer(text=f"Showing 20/{len(users)} whitelisted users")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="whitelistreset", aliases=["wlreset"], help="Reset the whitelist")
    @admin_only()
    async def whitelistreset(self, ctx):
        """Reset the entire antinuke whitelist"""
        # Extra confirmation for this destructive action
        confirm_msg = await ctx.send(embed=warning_embed(
            title="Reset Whitelist",
            description="⚠️ Are you sure you want to reset the entire whitelist? This cannot be undone.\n\nReact with ✅ to confirm or ❌ to cancel."
        ))
        
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                reset_whitelist(ctx.guild.id)
                await ctx.send(embed=success_embed(
                    title="Whitelist Reset",
                    description="✅ The whitelist has been reset."
                ))
            else:
                await ctx.send(embed=info_embed(
                    title="Action Cancelled",
                    description="Whitelist reset cancelled."
                ))
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Action Cancelled",
                description="Whitelist reset timed out."
            ))
    
    @commands.command(name="nightmode", aliases=["nm"], help="Configure nightmode for the server")
    @admin_only()
    async def nightmode(self, ctx, status: str = None, start_hour: int = None, end_hour: int = None):
        """Configure nightmode which locks channels during specified hours"""
        config = get_guild_config(ctx.guild.id)
        
        if status is None:
            # Display current nightmode configuration
            nm_config = config.get("nightmode", {})
            status = "enabled" if nm_config.get("enabled", False) else "disabled"
            start = nm_config.get("start_hour", 22)
            end = nm_config.get("end_hour", 6)
            
            await ctx.send(embed=info_embed(
                title="Nightmode Configuration",
                description=f"Status: **{status}**\nStart Hour: **{start}:00**\nEnd Hour: **{end}:00**"
            ))
            return
        
        if status.lower() not in ["on", "off", "enable", "disable", "enabled", "disabled", "setup"]:
            await ctx.send(embed=error_embed(
                title="Invalid Option",
                description="Please use `on`/`off`, `enable`/`disable`, or `setup <start_hour> <end_hour>`."
            ))
            return
        
        if status.lower() == "setup":
            if start_hour is None or end_hour is None:
                await ctx.send(embed=error_embed(
                    title="Missing Hours",
                    description="Please specify both start and end hours (0-23)."
                ))
                return
            
            if not (0 <= start_hour <= 23) or not (0 <= end_hour <= 23):
                await ctx.send(embed=error_embed(
                    title="Invalid Hours",
                    description="Hours must be between 0 and 23."
                ))
                return
            
            config["nightmode"]["start_hour"] = start_hour
            config["nightmode"]["end_hour"] = end_hour
            update_guild_config(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Nightmode Setup",
                description=f"✅ Nightmode configured:\nStart Hour: **{start_hour}:00**\nEnd Hour: **{end_hour}:00**"
            ))
            return
        
        # Update nightmode status
        enabled = status.lower() in ["on", "enable", "enabled"]
        config["nightmode"]["enabled"] = enabled
        update_guild_config(ctx.guild.id, config)
        
        await ctx.send(embed=success_embed(
            title="Nightmode Updated",
            description=f"✅ Nightmode is now **{'enabled' if enabled else 'disabled'}**."
        ))
    
    @commands.command(name="extraowner", help="Add extra owners for this server")
    @owner_only()
    async def extraowner(self, ctx, user: discord.User, action: str = "add"):
        """Add or remove extra owners for the current server"""
        guild_id = str(ctx.guild.id)
        
        if guild_id not in CONFIG["extra_owners"]:
            CONFIG["extra_owners"][guild_id] = []
        
        if action.lower() in ["add", "+"]:
            if user.id in CONFIG["extra_owners"][guild_id]:
                await ctx.send(embed=info_embed(
                    title="Already an Owner",
                    description=f"{user.mention} is already an extra owner."
                ))
                return
            
            CONFIG["extra_owners"][guild_id].append(user.id)
            await ctx.send(embed=success_embed(
                title="Extra Owner Added",
                description=f"✅ {user.mention} has been added as an extra owner."
            ))
        
        elif action.lower() in ["remove", "-", "delete", "del"]:
            if user.id not in CONFIG["extra_owners"][guild_id]:
                await ctx.send(embed=error_embed(
                    title="Not an Owner",
                    description=f"{user.mention} is not an extra owner."
                ))
                return
            
            CONFIG["extra_owners"][guild_id].remove(user.id)
            await ctx.send(embed=success_embed(
                title="Extra Owner Removed",
                description=f"✅ {user.mention} has been removed from extra owners."
            ))
        
        else:
            await ctx.send(embed=error_embed(
                title="Invalid Action",
                description="Please specify either `add` or `remove`."
            ))
    
    @commands.command(name="mainrole", help="Set a main role for admins or mods")
    @admin_only()
    async def mainrole(self, ctx, role_type: str, role: discord.Role = None):
        """Set a main role for admins or moderators"""
        if role_type.lower() not in ["admin", "mod"]:
            await ctx.send(embed=error_embed(
                title="Invalid Role Type",
                description="Please specify either `admin` or `mod`."
            ))
            return
        
        config = get_guild_config(ctx.guild.id)
        role_key = "admin_roles" if role_type.lower() == "admin" else "mod_roles"
        
        if role is None:
            # Show current roles
            roles = config.get(role_key, [])
            role_mentions = []
            
            for role_id in roles:
                r = ctx.guild.get_role(int(role_id))
                if r:
                    role_mentions.append(f"• {r.mention}")
            
            if not role_mentions:
                await ctx.send(embed=info_embed(
                    title=f"{role_type.title()} Roles",
                    description=f"No {role_type} roles are currently set."
                ))
            else:
                await ctx.send(embed=info_embed(
                    title=f"{role_type.title()} Roles",
                    description="\n".join(role_mentions)
                ))
            return
        
        # Add the role
        if role_key not in config:
            config[role_key] = []
        
        if str(role.id) not in config[role_key]:
            config[role_key].append(str(role.id))
            update_guild_config(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title=f"{role_type.title()} Role Added",
                description=f"✅ {role.mention} has been added as a {role_type} role."
            ))
        else:
            # Remove the role if it's already in the list
            config[role_key].remove(str(role.id))
            update_guild_config(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title=f"{role_type.title()} Role Removed",
                description=f"✅ {role.mention} has been removed from {role_type} roles."
            ))
    
    @commands.command(name="admin", aliases=["adminrole"], help="Add or remove admin roles")
    @admin_only()
    async def admin(self, ctx, role: discord.Role = None):
        """Add or remove admin roles (alias for mainrole admin)"""
        await self.mainrole(ctx, "admin", role)
    
    @commands.command(name="mod", aliases=["modrole"], help="Add or remove moderator roles")
    @admin_only()
    async def mod(self, ctx, role: discord.Role = None):
        """Add or remove moderator roles (alias for mainrole mod)"""
        await self.mainrole(ctx, "mod", role)
    
    # Event listeners for antinuke
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        """Trigger when a user is banned"""
        if not guild or not user:
            return
        
        config = get_guild_config(guild.id)
        if not config.get("antinuke", {}).get("enabled", True):
            return
        
        # Check audit logs to see who banned the user
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    # Check if the banner is whitelisted
                    if is_whitelisted(guild.id, entry.user.id) or entry.user.id == self.bot.user.id:
                        return
                    
                    # Unban the user if possible
                    try:
                        await guild.unban(user, reason="ESCUDO Antinuke: Unauthorized ban")
                    except discord.HTTPException:
                        pass
                    
                    # Take action against the banner
                    try:
                        await entry.user.ban(reason="ESCUDO Antinuke: Unauthorized ban")
                    except discord.HTTPException:
                        pass
                    
                    # Log the incident to a defined log channel if available
                    log_embed = warning_embed(
                        title="⚠️ Antinuke Triggered",
                        description=f"**Action:** Unauthorized ban\n**Target:** {user} ({user.id})\n**Perpetrator:** {entry.user} ({entry.user.id})\n**Action Taken:** Banned perpetrator, unbanned target"
                    )
                    
                    # Try to find a log channel
                    log_channel = discord.utils.get(guild.text_channels, name="escudo-logs")
                    if log_channel:
                        await log_channel.send(embed=log_embed)
        except discord.HTTPException:
            pass
    
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Trigger when a channel is deleted"""
        guild = channel.guild
        if not guild:
            return
        
        config = get_guild_config(guild.id)
        if not config.get("antinuke", {}).get("enabled", True):
            return
        
        # Check audit logs
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    # Check if the user is whitelisted
                    if is_whitelisted(guild.id, entry.user.id) or entry.user.id == self.bot.user.id:
                        return
                    
                    # Take action against the user
                    try:
                        await entry.user.ban(reason="ESCUDO Antinuke: Unauthorized channel deletion")
                    except discord.HTTPException:
                        pass
                    
                    # Try to create the channel again
                    try:
                        if isinstance(channel, discord.TextChannel):
                            await guild.create_text_channel(
                                name=channel.name,
                                category=channel.category,
                                position=channel.position,
                                topic=channel.topic,
                                nsfw=channel.nsfw,
                                reason="ESCUDO Antinuke: Channel restoration"
                            )
                        elif isinstance(channel, discord.VoiceChannel):
                            await guild.create_voice_channel(
                                name=channel.name,
                                category=channel.category,
                                position=channel.position,
                                bitrate=channel.bitrate,
                                user_limit=channel.user_limit,
                                reason="ESCUDO Antinuke: Channel restoration"
                            )
                    except discord.HTTPException:
                        pass
                    
                    # Log the incident
                    log_embed = warning_embed(
                        title="⚠️ Antinuke Triggered",
                        description=f"**Action:** Unauthorized channel deletion\n**Channel:** {channel.name} ({channel.id})\n**Perpetrator:** {entry.user} ({entry.user.id})\n**Action Taken:** Banned perpetrator, attempted to restore channel"
                    )
                    
                    log_channel = discord.utils.get(guild.text_channels, name="escudo-logs")
                    if log_channel:
                        await log_channel.send(embed=log_embed)
        except discord.HTTPException:
            pass
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """Trigger when a role is deleted"""
        guild = role.guild
        if not guild:
            return
        
        config = get_guild_config(guild.id)
        if not config.get("antinuke", {}).get("enabled", True):
            return
        
        # Check audit logs
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    # Check if the user is whitelisted
                    if is_whitelisted(guild.id, entry.user.id) or entry.user.id == self.bot.user.id:
                        return
                    
                    # Take action against the user
                    try:
                        await entry.user.ban(reason="ESCUDO Antinuke: Unauthorized role deletion")
                    except discord.HTTPException:
                        pass
                    
                    # Try to create the role again
                    try:
                        await guild.create_role(
                            name=role.name,
                            permissions=role.permissions,
                            colour=role.colour,
                            hoist=role.hoist,
                            mentionable=role.mentionable,
                            reason="ESCUDO Antinuke: Role restoration"
                        )
                    except discord.HTTPException:
                        pass
                    
                    # Log the incident
                    log_embed = warning_embed(
                        title="⚠️ Antinuke Triggered",
                        description=f"**Action:** Unauthorized role deletion\n**Role:** {role.name} ({role.id})\n**Perpetrator:** {entry.user} ({entry.user.id})\n**Action Taken:** Banned perpetrator, attempted to restore role"
                    )
                    
                    log_channel = discord.utils.get(guild.text_channels, name="escudo-logs")
                    if log_channel:
                        await log_channel.send(embed=log_embed)
        except discord.HTTPException:
            pass
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Trigger when a member's roles change (to detect admin role additions)"""
        # Check for dangerous permission changes
        if before.guild_permissions == after.guild_permissions:
            return
        
        guild = after.guild
        config = get_guild_config(guild.id)
        if not config.get("antinuke", {}).get("enabled", True):
            return
        
        # Check if they gained administrator permissions
        if not before.guild_permissions.administrator and after.guild_permissions.administrator:
            # Check audit logs to see who gave them the permissions
            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                    if entry.target.id == after.id:
                        # Check if the user is whitelisted
                        if is_whitelisted(guild.id, entry.user.id) or entry.user.id == self.bot.user.id:
                            return
                        
                        # Take action against the user
                        try:
                            await entry.user.ban(reason="ESCUDO Antinuke: Unauthorized admin permission grant")
                        except discord.HTTPException:
                            pass
                        
                        # Remove the admin roles from the target
                        for role in after.roles:
                            if role.permissions.administrator:
                                try:
                                    await after.remove_roles(role, reason="ESCUDO Antinuke: Removing unauthorized admin role")
                                except discord.HTTPException:
                                    pass
                        
                        # Log the incident
                        log_embed = warning_embed(
                            title="⚠️ Antinuke Triggered",
                            description=f"**Action:** Unauthorized admin permission grant\n**Target:** {after} ({after.id})\n**Perpetrator:** {entry.user} ({entry.user.id})\n**Action Taken:** Banned perpetrator, removed admin roles from target"
                        )
                        
                        log_channel = discord.utils.get(guild.text_channels, name="escudo-logs")
                        if log_channel:
                            await log_channel.send(embed=log_embed)
            except discord.HTTPException:
                pass

async def setup(bot):
    await bot.add_cog(Antinuke(bot))
