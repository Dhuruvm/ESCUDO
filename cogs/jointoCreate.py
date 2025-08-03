import discord
from discord.ext import commands
import asyncio
import datetime
from config import CONFIG
from utils.helpers import (
    is_mod, is_admin, is_owner, get_guild_config, update_guild_config,
    get_join_to_create_config, update_join_to_create_config,
    add_temp_channel, remove_temp_channel
)
from utils.embeds import (
    success_embed, error_embed, info_embed, warning_embed
)

class JoinToCreate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channels = {}
        self.cooldowns = {}
    
    @commands.command(name="setup", aliases=["setupj2c", "j2csetup"], help="Setup the join to create channel")
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx, channel: discord.VoiceChannel = None, category: discord.CategoryChannel = None):
        """Set up the Join to Create system"""
        # If no channel is specified, create one
        if channel is None:
            # Check if category exists
            if category is None:
                # Try to find existing Join to Create category
                for cat in ctx.guild.categories:
                    if cat.name.lower() == "join to create":
                        category = cat
                        break
                
                # Create a new category if none found
                if category is None:
                    try:
                        category = await ctx.guild.create_category(
                            name="Join to Create",
                            reason="Setting up Join to Create system"
                        )
                    except discord.Forbidden:
                        await ctx.send(embed=error_embed(
                            title="Missing Permissions",
                            description="I don't have permission to create categories."
                        ))
                        return
            
            # Create the Join to Create channel
            try:
                channel = await ctx.guild.create_voice_channel(
                    name="➕ Join to Create",
                    category=category,
                    reason="Setting up Join to Create system"
                )
            except discord.Forbidden:
                await ctx.send(embed=error_embed(
                    title="Missing Permissions",
                    description="I don't have permission to create voice channels."
                ))
                return
        
        # Get the config
        config = get_join_to_create_config(ctx.guild.id)
        
        # Update the config
        config["setup_channel"] = str(channel.id)
        if category:
            config["category"] = str(category.id)
        
        update_join_to_create_config(ctx.guild.id, config)
        
        await ctx.send(embed=success_embed(
            title="Join to Create Setup",
            description=f"✅ Join to Create system has been set up with {channel.mention} as the creation channel."
        ))
    
    @commands.command(name="remove", aliases=["removej2c", "j2cremove"], help="Remove the join to create system")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx):
        """Remove the Join to Create system"""
        # Get the config
        config = get_join_to_create_config(ctx.guild.id)
        
        if not config.get("setup_channel"):
            await ctx.send(embed=error_embed(
                title="Not Set Up",
                description="Join to Create system is not set up for this server."
            ))
            return
        
        # Ask for confirmation
        confirm_msg = await ctx.send(embed=warning_embed(
            title="Confirm Removal",
            description="Are you sure you want to remove the Join to Create system? All temporary channels will be deleted.\n\nReact with ✅ to confirm or ❌ to cancel."
        ))
        
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await ctx.send(embed=info_embed(
                    title="Removal Cancelled",
                    description="Join to Create system removal has been cancelled."
                ))
                return
            
            # Delete all temporary channels
            deleted_count = 0
            for channel_id in config.get("temp_channels", []):
                channel = ctx.guild.get_channel(int(channel_id))
                if channel:
                    try:
                        await channel.delete(reason="Join to Create system removal")
                        deleted_count += 1
                    except discord.Forbidden:
                        continue
            
            # Reset the config
            config["setup_channel"] = None
            config["category"] = None
            config["temp_channels"] = []
            
            update_join_to_create_config(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Join to Create Removed",
                description=f"✅ Join to Create system has been removed. {deleted_count} temporary channels were deleted."
            ))
            
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Removal Cancelled",
                description="Join to Create system removal timed out."
            ))
    
    @commands.command(name="limit", aliases=["vlimit"], help="Set the user limit for your voice channel")
    async def limit(self, ctx, limit: int = None):
        """Set the user limit for your voice channel"""
        # Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description="You need to be in a voice channel to use this command."
            ))
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check if it's a temporary channel
        config = get_join_to_create_config(ctx.guild.id)
        if str(voice_channel.id) not in config.get("temp_channels", []):
            await ctx.send(embed=error_embed(
                title="Not a Temporary Channel",
                description="This command can only be used in Join to Create channels that you own."
            ))
            return
        
        # Check if the user is the channel owner
        owner_id = self.voice_channels.get(str(voice_channel.id))
        if owner_id != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Not Channel Owner",
                description="Only the channel owner can modify the user limit."
            ))
            return
        
        # Check if the limit is valid
        if limit is not None and (limit < 0 or limit > 99):
            await ctx.send(embed=error_embed(
                title="Invalid Limit",
                description="User limit must be between 0 and 99. Use 0 for no limit."
            ))
            return
        
        # Set the limit
        try:
            await voice_channel.edit(user_limit=limit, reason=f"User limit set by {ctx.author}")
            
            if limit == 0:
                await ctx.send(embed=success_embed(
                    title="User Limit Removed",
                    description=f"✅ User limit for {voice_channel.mention} has been removed."
                ))
            else:
                await ctx.send(embed=success_embed(
                    title="User Limit Set",
                    description=f"✅ User limit for {voice_channel.mention} has been set to {limit}."
                ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to edit this voice channel."
            ))
    
    @commands.command(name="name", aliases=["rename", "vname"], help="Rename your voice channel")
    async def name(self, ctx, *, new_name=None):
        """Rename your voice channel"""
        # Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description="You need to be in a voice channel to use this command."
            ))
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check if it's a temporary channel
        config = get_join_to_create_config(ctx.guild.id)
        if str(voice_channel.id) not in config.get("temp_channels", []):
            await ctx.send(embed=error_embed(
                title="Not a Temporary Channel",
                description="This command can only be used in Join to Create channels that you own."
            ))
            return
        
        # Check if the user is the channel owner
        owner_id = self.voice_channels.get(str(voice_channel.id))
        if owner_id != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Not Channel Owner",
                description="Only the channel owner can rename the channel."
            ))
            return
        
        # Check if a new name was provided
        if new_name is None:
            await ctx.send(embed=error_embed(
                title="Missing Name",
                description="Please provide a new name for the channel."
            ))
            return
        
        # Check if the name is too long
        if len(new_name) > 100:
            await ctx.send(embed=error_embed(
                title="Name Too Long",
                description="Channel name cannot exceed 100 characters."
            ))
            return
        
        # Set the name
        try:
            await voice_channel.edit(name=new_name, reason=f"Channel renamed by {ctx.author}")
            
            await ctx.send(embed=success_embed(
                title="Channel Renamed",
                description=f"✅ Voice channel has been renamed to **{new_name}**."
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to rename this voice channel."
            ))
    
    @commands.command(name="vlock", help="Lock your voice channel")
    async def vlock(self, ctx):
        """Lock your voice channel to prevent new users from joining"""
        # Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description="You need to be in a voice channel to use this command."
            ))
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check if it's a temporary channel
        config = get_join_to_create_config(ctx.guild.id)
        if str(voice_channel.id) not in config.get("temp_channels", []):
            await ctx.send(embed=error_embed(
                title="Not a Temporary Channel",
                description="This command can only be used in Join to Create channels that you own."
            ))
            return
        
        # Check if the user is the channel owner
        owner_id = self.voice_channels.get(str(voice_channel.id))
        if owner_id != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Not Channel Owner",
                description="Only the channel owner can lock the channel."
            ))
            return
        
        # Lock the channel
        try:
            await voice_channel.set_permissions(ctx.guild.default_role, connect=False)
            
            await ctx.send(embed=success_embed(
                title="Channel Locked",
                description=f"✅ {voice_channel.mention} has been locked. New users cannot join."
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to set permissions for this voice channel."
            ))
    
    @commands.command(name="vunlock", help="Unlock your voice channel")
    async def vunlock(self, ctx):
        """Unlock your voice channel to allow users to join"""
        # Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description="You need to be in a voice channel to use this command."
            ))
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check if it's a temporary channel
        config = get_join_to_create_config(ctx.guild.id)
        if str(voice_channel.id) not in config.get("temp_channels", []):
            await ctx.send(embed=error_embed(
                title="Not a Temporary Channel",
                description="This command can only be used in Join to Create channels that you own."
            ))
            return
        
        # Check if the user is the channel owner
        owner_id = self.voice_channels.get(str(voice_channel.id))
        if owner_id != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Not Channel Owner",
                description="Only the channel owner can unlock the channel."
            ))
            return
        
        # Unlock the channel
        try:
            await voice_channel.set_permissions(ctx.guild.default_role, connect=None)
            
            await ctx.send(embed=success_embed(
                title="Channel Unlocked",
                description=f"✅ {voice_channel.mention} has been unlocked. Users can join again."
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to set permissions for this voice channel."
            ))
    
    @commands.command(name="claim", aliases=["vclaim"], help="Claim ownership of an abandoned voice channel")
    async def claim(self, ctx):
        """Claim ownership of a voice channel if the owner has left"""
        # Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description="You need to be in a voice channel to use this command."
            ))
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check if it's a temporary channel
        config = get_join_to_create_config(ctx.guild.id)
        if str(voice_channel.id) not in config.get("temp_channels", []):
            await ctx.send(embed=error_embed(
                title="Not a Temporary Channel",
                description="This command can only be used in Join to Create channels."
            ))
            return
        
        # Check if the current owner is in the channel
        channel_id = str(voice_channel.id)
        owner_id = self.voice_channels.get(channel_id)
        
        if owner_id:
            owner = ctx.guild.get_member(owner_id)
            if owner and owner.voice and owner.voice.channel and owner.voice.channel.id == voice_channel.id:
                await ctx.send(embed=error_embed(
                    title="Owner Still Present",
                    description=f"The channel owner ({owner.mention}) is still in the voice channel."
                ))
                return
        
        # Transfer ownership
        self.voice_channels[channel_id] = ctx.author.id
        
        await ctx.send(embed=success_embed(
            title="Channel Claimed",
            description=f"✅ You are now the owner of {voice_channel.mention}."
        ))
    
    @commands.command(name="channelkick", aliases=["ckick"], help="Kick a user from your voice channel")
    async def channelkick(self, ctx, member: discord.Member, *, reason=None):
        """Kick a user from your voice channel"""
        # Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description="You need to be in a voice channel to use this command."
            ))
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check if it's a temporary channel
        config = get_join_to_create_config(ctx.guild.id)
        if str(voice_channel.id) not in config.get("temp_channels", []):
            await ctx.send(embed=error_embed(
                title="Not a Temporary Channel",
                description="This command can only be used in Join to Create channels that you own."
            ))
            return
        
        # Check if the user is the channel owner
        owner_id = self.voice_channels.get(str(voice_channel.id))
        if owner_id != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Not Channel Owner",
                description="Only the channel owner can kick users from the channel."
            ))
            return
        
        # Check if the member is in the voice channel
        if not member.voice or member.voice.channel.id != voice_channel.id:
            await ctx.send(embed=error_embed(
                title="Not in Voice Channel",
                description=f"{member.mention} is not in your voice channel."
            ))
            return
        
        # Check if the member is the owner
        if member.id == owner_id:
            await ctx.send(embed=error_embed(
                title="Cannot Kick Owner",
                description="You cannot kick the channel owner."
            ))
            return
        
        # Kick the member
        try:
            # Create a temporary voice channel
            temp_channel = await ctx.guild.create_voice_channel(
                name="Kick Channel",
                reason=f"Temporary channel for voice kicking"
            )
            
            # Move the user to the temporary channel
            await member.move_to(temp_channel, reason=f"Kicked from voice channel by {ctx.author}")
            
            # Delete the temporary channel
            await temp_channel.delete(reason=f"Temporary voice kick channel")
            
            # Prevent the user from rejoining
            await voice_channel.set_permissions(member, connect=False)
            
            # Send success message
            await ctx.send(embed=success_embed(
                title="User Kicked",
                description=f"✅ {member.mention} has been kicked from your voice channel."
            ))
            
            # Try to DM the user
            try:
                await member.send(embed=warning_embed(
                    title=f"Kicked from Voice Channel",
                    description=f"You were kicked from **{voice_channel.name}** in **{ctx.guild.name}**.\nReason: {reason or 'No reason provided'}"
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to move or set permissions for users."
            ))
    
    @commands.command(name="permit", aliases=["allow", "vpermit"], help="Allow a user to join your locked voice channel")
    async def permit(self, ctx, member: discord.Member):
        """Allow a specific user to join your locked voice channel"""
        # Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description="You need to be in a voice channel to use this command."
            ))
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check if it's a temporary channel
        config = get_join_to_create_config(ctx.guild.id)
        if str(voice_channel.id) not in config.get("temp_channels", []):
            await ctx.send(embed=error_embed(
                title="Not a Temporary Channel",
                description="This command can only be used in Join to Create channels that you own."
            ))
            return
        
        # Check if the user is the channel owner
        owner_id = self.voice_channels.get(str(voice_channel.id))
        if owner_id != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Not Channel Owner",
                description="Only the channel owner can permit users to join the channel."
            ))
            return
        
        # Permit the user
        try:
            await voice_channel.set_permissions(member, connect=True)
            
            await ctx.send(embed=success_embed(
                title="User Permitted",
                description=f"✅ {member.mention} can now join your voice channel even if it's locked."
            ))
            
            # Try to DM the user
            try:
                await member.send(embed=info_embed(
                    title=f"Voice Channel Access Granted",
                    description=f"You have been granted access to join **{voice_channel.name}** in **{ctx.guild.name}**."
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to set permissions for this voice channel."
            ))
    
    @commands.command(name="deny", aliases=["vdeny"], help="Deny a user from joining your voice channel")
    async def deny(self, ctx, member: discord.Member, *, reason=None):
        """Deny a specific user from joining your voice channel"""
        # Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description="You need to be in a voice channel to use this command."
            ))
            return
        
        voice_channel = ctx.author.voice.channel
        
        # Check if it's a temporary channel
        config = get_join_to_create_config(ctx.guild.id)
        if str(voice_channel.id) not in config.get("temp_channels", []):
            await ctx.send(embed=error_embed(
                title="Not a Temporary Channel",
                description="This command can only be used in Join to Create channels that you own."
            ))
            return
        
        # Check if the user is the channel owner
        owner_id = self.voice_channels.get(str(voice_channel.id))
        if owner_id != ctx.author.id and not ctx.author.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Not Channel Owner",
                description="Only the channel owner can deny users from joining the channel."
            ))
            return
        
        # Check if the member is the owner
        if member.id == owner_id:
            await ctx.send(embed=error_embed(
                title="Cannot Deny Owner",
                description="You cannot deny the channel owner."
            ))
            return
        
        # Deny the user
        try:
            await voice_channel.set_permissions(member, connect=False)
            
            # Kick the user if they're already in the channel
            if member.voice and member.voice.channel and member.voice.channel.id == voice_channel.id:
                # Create a temporary voice channel
                temp_channel = await ctx.guild.create_voice_channel(
                    name="Kick Channel",
                    reason=f"Temporary channel for voice kicking"
                )
                
                # Move the user to the temporary channel
                await member.move_to(temp_channel, reason=f"Denied access to voice channel by {ctx.author}")
                
                # Delete the temporary channel
                await temp_channel.delete(reason=f"Temporary voice kick channel")
            
            await ctx.send(embed=success_embed(
                title="User Denied",
                description=f"✅ {member.mention} has been denied access to your voice channel."
            ))
            
            # Try to DM the user
            try:
                await member.send(embed=warning_embed(
                    title=f"Voice Channel Access Denied",
                    description=f"Your access to **{voice_channel.name}** in **{ctx.guild.name}** has been denied.\nReason: {reason or 'No reason provided'}"
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to set permissions for this voice channel."
            ))
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Listener for voice state changes to handle Join to Create functionality"""
        # Skip if both channels are the same (e.g., mute/deafen)
        if before.channel == after.channel:
            return
        
        # Handle channel creation
        if after.channel:
            config = get_join_to_create_config(member.guild.id)
            setup_channel_id = config.get("setup_channel")
            
            # Check if the user joined the setup channel
            if setup_channel_id and str(after.channel.id) == setup_channel_id:
                # Prevent abuse with cooldown
                if member.id in self.cooldowns and (datetime.datetime.now() - self.cooldowns[member.id]).total_seconds() < 10:
                    try:
                        await member.move_to(None, reason="Join to Create cooldown")
                        return
                    except discord.Forbidden:
                        pass
                
                self.cooldowns[member.id] = datetime.datetime.now()
                
                # Create a new voice channel
                category_id = config.get("category")
                category = None
                if category_id:
                    category = member.guild.get_channel(int(category_id))
                
                try:
                    channel_name = f"{member.display_name}'s Channel"
                    new_channel = await member.guild.create_voice_channel(
                        name=channel_name,
                        category=category,
                        reason=f"Join to Create channel for {member}"
                    )
                    
                    # Move the user to the new channel
                    await member.move_to(new_channel, reason="Join to Create channel")
                    
                    # Add the channel to the temporary channels list
                    config = get_join_to_create_config(member.guild.id)
                    add_temp_channel(member.guild.id, new_channel.id)
                    
                    # Store the channel owner
                    self.voice_channels[str(new_channel.id)] = member.id
                    
                    # Try to DM the user with instructions
                    try:
                        prefix = CONFIG["prefix"]
                        await member.send(embed=info_embed(
                            title="Voice Channel Created",
                            description=f"Your voice channel has been created in **{member.guild.name}**.\n\nYou can use these commands to manage it:\n"
                                        f"`{prefix}name <name>` - Rename your channel\n"
                                        f"`{prefix}limit <number>` - Set user limit (0 for no limit)\n"
                                        f"`{prefix}lock` - Lock your channel\n"
                                        f"`{prefix}unlock` - Unlock your channel\n"
                                        f"`{prefix}permit <user>` - Allow a user to join\n"
                                        f"`{prefix}deny <user>` - Deny a user from joining\n"
                                        f"`{prefix}kick <user>` - Kick a user from your channel"
                        ))
                    except discord.Forbidden:
                        pass
                    
                except discord.Forbidden:
                    try:
                        await member.move_to(None, reason="Join to Create failed - missing permissions")
                    except discord.Forbidden:
                        pass
        
        # Handle channel deletion
        if before.channel:
            config = get_join_to_create_config(member.guild.id)
            
            # Skip the setup channel
            setup_channel_id = config.get("setup_channel")
            if setup_channel_id and str(before.channel.id) == setup_channel_id:
                return
            
            # Check if it's a temporary channel
            if str(before.channel.id) in config.get("temp_channels", []):
                # If the channel is empty, delete it
                if not before.channel.members:
                    try:
                        await before.channel.delete(reason="Empty Join to Create channel")
                        
                        # Remove the channel from the temporary channels list
                        config = get_join_to_create_config(member.guild.id)
                        remove_temp_channel(member.guild.id, before.channel.id)
                        
                        # Remove the channel owner
                        if str(before.channel.id) in self.voice_channels:
                            del self.voice_channels[str(before.channel.id)]
                    except discord.Forbidden:
                        pass

async def setup(bot):
    await bot.add_cog(JoinToCreate(bot))
