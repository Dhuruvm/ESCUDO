import discord
from discord.ext import commands
import asyncio
from config import CONFIG
from utils.helpers import (
    is_mod, is_admin, is_owner, get_guild_config, update_guild_config
)
from utils.embeds import (
    success_embed, error_embed, info_embed, warning_embed
)

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_states = {}
    
    @commands.command(name="voicekick", aliases=["vkick"], help="Kick a user from a voice channel")
    @commands.check(is_mod)
    async def voicekick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a user from their current voice channel"""
        # Check if the user is in a voice channel
        if not member.voice:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description=f"{member.mention} is not in a voice channel."
            ))
            return
        
        # Check if the bot has permission to move members
        if not ctx.guild.me.guild_permissions.move_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to move members."
            ))
            return
        
        # Get the current voice channel
        voice_channel = member.voice.channel
        
        # Create a temporary voice channel to move the user to, then kick them
        try:
            # Create a temporary channel
            temp_channel = await ctx.guild.create_voice_channel(
                name="Kick Channel",
                reason=f"Temporary channel for voice kicking {member}"
            )
            
            # Move the user to the temporary channel
            await member.move_to(temp_channel, reason=f"Voice kicked by {ctx.author}: {reason}")
            
            # Delete the temporary channel (this will disconnect the user)
            await temp_channel.delete(reason=f"Temporary voice kick channel for {member}")
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Voice Kicked",
                description=f"✅ {member.mention} was kicked from {voice_channel.mention}.\nReason: {reason}"
            ))
            
            # Try to DM the user
            try:
                await member.send(embed=warning_embed(
                    title=f"Voice Kicked from {ctx.guild.name}",
                    description=f"You were disconnected from {voice_channel.name}.\nReason: {reason}"
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Voice Kick Failed",
                description=f"I don't have permission to move {member.mention}."
            ))
        except Exception as e:
            await ctx.send(embed=error_embed(
                title="Voice Kick Failed",
                description=f"An error occurred: {str(e)}"
            ))
    
    @commands.command(name="voicemute", aliases=["vmute"], help="Mute a user in voice channels")
    @commands.check(is_mod)
    async def voicemute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Server mute a user in voice channels"""
        # Check if the bot has permission to mute members
        if not ctx.guild.me.guild_permissions.mute_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to mute members."
            ))
            return
        
        # Check if the user is already muted
        if member.voice and member.voice.mute:
            await ctx.send(embed=error_embed(
                title="Already Muted",
                description=f"{member.mention} is already voice muted."
            ))
            return
        
        try:
            # Mute the user
            await member.edit(mute=True, reason=f"Voice muted by {ctx.author}: {reason}")
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Voice Muted",
                description=f"✅ {member.mention} has been voice muted.\nReason: {reason}"
            ))
            
            # Try to DM the user
            try:
                await member.send(embed=warning_embed(
                    title=f"Voice Muted in {ctx.guild.name}",
                    description=f"You have been server muted in voice channels.\nReason: {reason}"
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Voice Mute Failed",
                description=f"I don't have permission to mute {member.mention}."
            ))
    
    @commands.command(name="voiceunmute", aliases=["vunmute"], help="Unmute a user in voice channels")
    @commands.check(is_mod)
    async def voiceunmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Remove server mute from a user in voice channels"""
        # Check if the bot has permission to mute members
        if not ctx.guild.me.guild_permissions.mute_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to unmute members."
            ))
            return
        
        # Check if the user is actually muted
        if member.voice and not member.voice.mute:
            await ctx.send(embed=error_embed(
                title="Not Muted",
                description=f"{member.mention} is not voice muted."
            ))
            return
        
        try:
            # Unmute the user
            await member.edit(mute=False, reason=f"Voice unmuted by {ctx.author}: {reason}")
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Voice Unmuted",
                description=f"✅ {member.mention} has been voice unmuted.\nReason: {reason}"
            ))
            
            # Try to DM the user
            try:
                await member.send(embed=success_embed(
                    title=f"Voice Unmuted in {ctx.guild.name}",
                    description=f"Your server voice mute has been removed.\nReason: {reason}"
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Voice Unmute Failed",
                description=f"I don't have permission to unmute {member.mention}."
            ))
    
    @commands.command(name="voicedeafen", aliases=["vdeafen", "vdeaf"], help="Deafen a user in voice channels")
    @commands.check(is_mod)
    async def voicedeafen(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Server deafen a user in voice channels"""
        # Check if the bot has permission to deafen members
        if not ctx.guild.me.guild_permissions.deafen_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to deafen members."
            ))
            return
        
        # Check if the user is already deafened
        if member.voice and member.voice.deaf:
            await ctx.send(embed=error_embed(
                title="Already Deafened",
                description=f"{member.mention} is already voice deafened."
            ))
            return
        
        try:
            # Deafen the user
            await member.edit(deafen=True, reason=f"Voice deafened by {ctx.author}: {reason}")
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Voice Deafened",
                description=f"✅ {member.mention} has been voice deafened.\nReason: {reason}"
            ))
            
            # Try to DM the user
            try:
                await member.send(embed=warning_embed(
                    title=f"Voice Deafened in {ctx.guild.name}",
                    description=f"You have been server deafened in voice channels.\nReason: {reason}"
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Voice Deafen Failed",
                description=f"I don't have permission to deafen {member.mention}."
            ))
    
    @commands.command(name="voiceundeafen", aliases=["vundeafen", "vundeaf"], help="Undeafen a user in voice channels")
    @commands.check(is_mod)
    async def voiceundeafen(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Remove server deafen from a user in voice channels"""
        # Check if the bot has permission to deafen members
        if not ctx.guild.me.guild_permissions.deafen_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to undeafen members."
            ))
            return
        
        # Check if the user is actually deafened
        if member.voice and not member.voice.deaf:
            await ctx.send(embed=error_embed(
                title="Not Deafened",
                description=f"{member.mention} is not voice deafened."
            ))
            return
        
        try:
            # Undeafen the user
            await member.edit(deafen=False, reason=f"Voice undeafened by {ctx.author}: {reason}")
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Voice Undeafened",
                description=f"✅ {member.mention} has been voice undeafened.\nReason: {reason}"
            ))
            
            # Try to DM the user
            try:
                await member.send(embed=success_embed(
                    title=f"Voice Undeafened in {ctx.guild.name}",
                    description=f"Your server voice deafen has been removed.\nReason: {reason}"
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Voice Undeafen Failed",
                description=f"I don't have permission to undeafen {member.mention}."
            ))
    
    @commands.command(name="voicemoveall", aliases=["moveall"], help="Move all users from one voice channel to another")
    @commands.check(is_mod)
    async def voicemoveall(self, ctx, source: discord.VoiceChannel, destination: discord.VoiceChannel):
        """Move all users from one voice channel to another"""
        # Check if the bot has permission to move members
        if not ctx.guild.me.guild_permissions.move_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to move members."
            ))
            return
        
        # Check if there are users in the source channel
        if not source.members:
            await ctx.send(embed=error_embed(
                title="Empty Channel",
                description=f"{source.mention} is empty. No members to move."
            ))
            return
        
        try:
            # Count the number of members to move
            member_count = len(source.members)
            
            # Move each member to the destination channel
            moved_count = 0
            for member in source.members.copy():  # Use .copy() to prevent modification during iteration
                await member.move_to(destination, reason=f"Mass move by {ctx.author}")
                moved_count += 1
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Members Moved",
                description=f"✅ Successfully moved {moved_count}/{member_count} members from {source.mention} to {destination.mention}."
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Move Failed",
                description="I don't have permission to move some members."
            ))
        except Exception as e:
            await ctx.send(embed=error_embed(
                title="Move Failed",
                description=f"An error occurred: {str(e)}"
            ))
    
    @commands.command(name="voicemove", aliases=["move"], help="Move a user to another voice channel")
    @commands.check(is_mod)
    async def voicemove(self, ctx, member: discord.Member, channel: discord.VoiceChannel):
        """Move a user to another voice channel"""
        # Check if the bot has permission to move members
        if not ctx.guild.me.guild_permissions.move_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to move members."
            ))
            return
        
        # Check if the user is in a voice channel
        if not member.voice:
            await ctx.send(embed=error_embed(
                title="Not in Voice",
                description=f"{member.mention} is not in a voice channel."
            ))
            return
        
        try:
            # Get the current voice channel
            current_channel = member.voice.channel
            
            # Move the member to the new channel
            await member.move_to(channel, reason=f"Moved by {ctx.author}")
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Member Moved",
                description=f"✅ Moved {member.mention} from {current_channel.mention} to {channel.mention}."
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Move Failed",
                description=f"I don't have permission to move {member.mention}."
            ))
        except Exception as e:
            await ctx.send(embed=error_embed(
                title="Move Failed",
                description=f"An error occurred: {str(e)}"
            ))
    
    @commands.command(name="voiceunmuteall", aliases=["vunmuteall"], help="Unmute all users in a voice channel")
    @commands.check(is_mod)
    async def voiceunmuteall(self, ctx, channel: discord.VoiceChannel = None):
        """Unmute all users in a voice channel"""
        # If no channel specified, use the author's channel
        if channel is None:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await ctx.send(embed=error_embed(
                    title="No Channel Specified",
                    description="You need to either specify a voice channel or be in one."
                ))
                return
        
        # Check if the bot has permission to mute members
        if not ctx.guild.me.guild_permissions.mute_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to unmute members."
            ))
            return
        
        # Check if there are users in the channel
        if not channel.members:
            await ctx.send(embed=error_embed(
                title="Empty Channel",
                description=f"{channel.mention} is empty. No members to unmute."
            ))
            return
        
        try:
            # Count the number of muted members
            muted_members = [m for m in channel.members if m.voice.mute]
            
            if not muted_members:
                await ctx.send(embed=info_embed(
                    title="No Muted Members",
                    description=f"There are no muted members in {channel.mention}."
                ))
                return
            
            # Unmute each muted member
            unmuted_count = 0
            for member in muted_members:
                await member.edit(mute=False, reason=f"Mass unmute by {ctx.author}")
                unmuted_count += 1
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Members Unmuted",
                description=f"✅ Successfully unmuted {unmuted_count}/{len(muted_members)} members in {channel.mention}."
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Unmute Failed",
                description="I don't have permission to unmute some members."
            ))
        except Exception as e:
            await ctx.send(embed=error_embed(
                title="Unmute Failed",
                description=f"An error occurred: {str(e)}"
            ))
    
    @commands.command(name="voicemuteall", aliases=["vmuteall"], help="Mute all users in a voice channel")
    @commands.check(is_mod)
    async def voicemuteall(self, ctx, channel: discord.VoiceChannel = None):
        """Mute all users in a voice channel"""
        # If no channel specified, use the author's channel
        if channel is None:
            if ctx.author.voice and ctx.author.voice.channel:
                channel = ctx.author.voice.channel
            else:
                await ctx.send(embed=error_embed(
                    title="No Channel Specified",
                    description="You need to either specify a voice channel or be in one."
                ))
                return
        
        # Check if the bot has permission to mute members
        if not ctx.guild.me.guild_permissions.mute_members:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to mute members."
            ))
            return
        
        # Check if there are users in the channel
        if not channel.members:
            await ctx.send(embed=error_embed(
                title="Empty Channel",
                description=f"{channel.mention} is empty. No members to mute."
            ))
            return
        
        try:
            # Count the number of unmuted members
            unmuted_members = [m for m in channel.members if not m.voice.mute]
            
            if not unmuted_members:
                await ctx.send(embed=info_embed(
                    title="No Unmuted Members",
                    description=f"All members in {channel.mention} are already muted."
                ))
                return
            
            # Mute each unmuted member
            muted_count = 0
            for member in unmuted_members:
                # Skip muting the moderator who issued the command
                if member.id == ctx.author.id:
                    continue
                await member.edit(mute=True, reason=f"Mass mute by {ctx.author}")
                muted_count += 1
            
            # Success message
            await ctx.send(embed=success_embed(
                title="Members Muted",
                description=f"✅ Successfully muted {muted_count}/{len(unmuted_members)} members in {channel.mention}."
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Mute Failed",
                description="I don't have permission to mute some members."
            ))
        except Exception as e:
            await ctx.send(embed=error_embed(
                title="Mute Failed",
                description=f"An error occurred: {str(e)}"
            ))
    
    @commands.command(name="voiceregion", aliases=["vregion"], help="Change the region of a voice channel")
    @commands.check(is_mod)
    async def voiceregion(self, ctx, channel: discord.VoiceChannel, *, region=None):
        """Change the region/RTCRegion of a voice channel"""
        # Check if the bot has permission to manage channels
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to manage channels."
            ))
            return
        
        # If no region is specified, show the current region
        if region is None:
            current_region = channel.rtc_region or "Automatic"
            
            # List all available regions
            regions = ["brazil", "hongkong", "india", "japan", "rotterdam", "russia", "singapore", "southafrica", "sydney", "us-central", "us-east", "us-south", "us-west", "automatic"]
            
            regions_text = ", ".join([f"`{r}`" for r in regions])
            
            await ctx.send(embed=info_embed(
                title="Voice Channel Region",
                description=f"Current region for {channel.mention}: **{current_region}**\n\nAvailable regions: {regions_text}"
            ))
            return
        
        # Check if the specified region is valid
        region = region.lower()
        if region == "auto" or region == "automatic":
            region = None  # None means automatic region
        
        try:
            # Change the region
            await channel.edit(rtc_region=region, reason=f"Region changed by {ctx.author}")
            
            # Success message
            new_region = region or "Automatic"
            await ctx.send(embed=success_embed(
                title="Region Changed",
                description=f"✅ Changed the region of {channel.mention} to **{new_region}**."
            ))
                
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Region Change Failed",
                description="I don't have permission to change the region of this channel."
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=error_embed(
                title="Region Change Failed",
                description=f"An error occurred: {str(e)}\n\nThis might be an invalid region. Try using one of the available regions."
            ))
    
    @commands.command(name="voicetextchannel", aliases=["vtc"], help="Set a text channel for voice channel notifications")
    @commands.check(is_admin)
    async def voicetextchannel(self, ctx, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel = None):
        """Link a text channel to a voice channel for join/leave notifications"""
        config = get_guild_config(ctx.guild.id)
        
        # Initialize voice_text_channels if it doesn't exist
        if "voice_text_channels" not in config:
            config["voice_text_channels"] = {}
        
        voice_id = str(voice_channel.id)
        
        # If text_channel is None, remove the link
        if text_channel is None:
            if voice_id in config["voice_text_channels"]:
                del config["voice_text_channels"][voice_id]
                update_guild_config(ctx.guild.id, config)
                await ctx.send(embed=success_embed(
                    title="Link Removed",
                    description=f"✅ Removed text channel link from {voice_channel.mention}."
                ))
            else:
                await ctx.send(embed=error_embed(
                    title="No Link Found",
                    description=f"{voice_channel.mention} is not linked to any text channel."
                ))
            return
        
        # Set the link
        config["voice_text_channels"][voice_id] = str(text_channel.id)
        update_guild_config(ctx.guild.id, config)
        
        await ctx.send(embed=success_embed(
            title="Link Set",
            description=f"✅ Linked {voice_channel.mention} to {text_channel.mention} for join/leave notifications."
        ))
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Listener for voice state changes to track joins and leaves"""
        # Skip if the member is a bot
        if member.bot:
            return
        
        config = get_guild_config(member.guild.id)
        voice_text_channels = config.get("voice_text_channels", {})
        
        # Check for join events
        if after.channel and (not before.channel or before.channel.id != after.channel.id):
            voice_id = str(after.channel.id)
            if voice_id in voice_text_channels:
                text_channel_id = voice_text_channels[voice_id]
                text_channel = member.guild.get_channel(int(text_channel_id))
                
                if text_channel:
                    embed = info_embed(
                        title="Voice Channel Joined",
                        description=f"{member.mention} joined {after.channel.mention}"
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    await text_channel.send(embed=embed)
        
        # Check for leave events
        if before.channel and (not after.channel or before.channel.id != after.channel.id):
            voice_id = str(before.channel.id)
            if voice_id in voice_text_channels:
                text_channel_id = voice_text_channels[voice_id]
                text_channel = member.guild.get_channel(int(text_channel_id))
                
                if text_channel:
                    embed = info_embed(
                        title="Voice Channel Left",
                        description=f"{member.mention} left {before.channel.mention}"
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    await text_channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Voice(bot))
