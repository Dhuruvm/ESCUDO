
import discord
from discord.ext import commands
import asyncio
import re
from urllib.parse import urlparse
from config import CONFIG
from utils.helpers import (
    is_mod, is_admin, is_owner, get_guild_config, update_guild_config
)
from utils.embeds import (
    success_embed, error_embed, info_embed, warning_embed, create_embed
)
from utils.webhook_db import (
    create_shadowclone, get_shadowclone, get_shadowclone_by_channel,
    update_shadowclone, delete_shadowclone, deactivate_shadowclone,
    get_user_shadowclones
)
from utils.command_router import CommandRouter

class ShadowClone(commands.Cog):
    """Shadow Clone system - Create personalized webhook clones of ESCUDO"""
    
    def __init__(self, bot):
        self.bot = bot
        self.command_router = CommandRouter(bot)
    
    @discord.slash_command(name="shadowclone", description="Manage your shadow clones")
    async def shadowclone(self, ctx):
        """Base command for shadow clone management"""
        pass
    
    @shadowclone.command(name="create", description="Create a new shadow clone")
    async def create_shadowclone(
        self, 
        ctx,
        name: discord.Option(str, description="Name for your shadow clone", max_length=80),
        prefix: discord.Option(str, description="Command prefix for your clone", max_length=5),
        avatar_url: discord.Option(str, description="Avatar URL for your clone", required=False)
    ):
        """Create a new shadow clone in the current channel"""
        await ctx.defer()
        
        # Validate prefix
        if len(prefix) < 1:
            await ctx.followup.send(embed=error_embed(
                title="Invalid Prefix",
                description="Prefix must be at least 1 character long."
            ))
            return
        
        # Check for special characters that might cause issues
        if any(char in prefix for char in [' ', '\n', '\t']):
            await ctx.followup.send(embed=error_embed(
                title="Invalid Prefix",
                description="Prefix cannot contain spaces or special whitespace characters."
            ))
            return
        
        # Validate avatar URL if provided
        if avatar_url:
            if not self.is_valid_url(avatar_url):
                await ctx.followup.send(embed=error_embed(
                    title="Invalid Avatar URL",
                    description="Please provide a valid image URL."
                ))
                return
        else:
            # Use default ESCUDO avatar
            avatar_url = self.bot.user.display_avatar.url
        
        # Check if user already has a clone in this channel
        existing_clone = get_shadowclone(ctx.author.id, ctx.channel.id)
        if existing_clone:
            await ctx.followup.send(embed=error_embed(
                title="Clone Already Exists",
                description=f"You already have a shadow clone in this channel named **{existing_clone['name']}**.\nUse `/shadowclone delete` to remove it first or `/shadowclone update` to modify it."
            ))
            return
        
        # Check if user has reached clone limit (5 clones max per user)
        user_clones = get_user_shadowclones(ctx.author.id)
        if len(user_clones) >= 5:
            await ctx.followup.send(embed=error_embed(
                title="Clone Limit Reached",
                description="You can only have up to 5 shadow clones. Delete some existing clones first."
            ))
            return
        
        try:
            # Create webhook
            webhook = await ctx.channel.create_webhook(
                name=f"ShadowClone-{name}",
                reason=f"Shadow clone created by {ctx.author}"
            )
            
            # Store in database
            success = create_shadowclone(
                user_id=ctx.author.id,
                channel_id=ctx.channel.id,
                webhook_id=webhook.id,
                webhook_token=webhook.token,
                name=name,
                avatar_url=avatar_url,
                prefix=prefix
            )
            
            if success:
                embed = success_embed(
                    title="🔮 Shadow Clone Created!",
                    description=f"Your shadow clone **{name}** has been successfully created!"
                )
                
                embed.add_field(name="Clone Name", value=name, inline=True)
                embed.add_field(name="Prefix", value=f"`{prefix}`", inline=True)
                embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
                embed.add_field(name="Usage", value=f"Use `{prefix}help` to see available commands", inline=False)
                
                embed.set_thumbnail(url=avatar_url)
                embed.set_footer(text="Your clone will respond to commands with your custom prefix!")
                
                await ctx.followup.send(embed=embed)
                
                # Send a test message from the clone
                await asyncio.sleep(1)
                test_embed = info_embed(
                    title="👋 Hello!",
                    description=f"I'm **{name}**, your new shadow clone! Use `{prefix}help` to get started."
                )
                
                await webhook.send(
                    embed=test_embed,
                    username=name,
                    avatar_url=avatar_url
                )
                
            else:
                await webhook.delete()
                await ctx.followup.send(embed=error_embed(
                    title="Database Error",
                    description="Failed to save clone data. Please try again."
                ))
                
        except discord.Forbidden:
            await ctx.followup.send(embed=error_embed(
                title="Permission Error",
                description="I don't have permission to create webhooks in this channel."
            ))
        except discord.HTTPException as e:
            await ctx.followup.send(embed=error_embed(
                title="Webhook Creation Failed",
                description=f"Failed to create webhook: {str(e)}"
            ))
    
    @shadowclone.command(name="delete", description="Delete your shadow clone")
    async def delete_shadowclone(self, ctx):
        """Delete the user's shadow clone in the current channel"""
        await ctx.defer()
        
        # Check if user has a clone in this channel
        clone_data = get_shadowclone(ctx.author.id, ctx.channel.id)
        if not clone_data:
            await ctx.followup.send(embed=error_embed(
                title="No Clone Found",
                description="You don't have a shadow clone in this channel."
            ))
            return
        
        try:
            # Try to delete the webhook
            webhook = await self.bot.fetch_webhook(clone_data["webhook_id"])
            await webhook.delete()
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            # Webhook might already be deleted
            pass
        
        # Remove from database
        success = delete_shadowclone(ctx.author.id, ctx.channel.id)
        
        if success:
            embed = success_embed(
                title="🗑️ Shadow Clone Deleted",
                description=f"Your shadow clone **{clone_data['name']}** has been successfully deleted."
            )
            await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send(embed=error_embed(
                title="Deletion Failed",
                description="Failed to delete clone data. Please try again."
            ))
    
    @shadowclone.command(name="update", description="Update your shadow clone")
    async def update_shadowclone(
        self,
        ctx,
        name: discord.Option(str, description="New name for your clone", required=False),
        prefix: discord.Option(str, description="New prefix for your clone", required=False),
        avatar_url: discord.Option(str, description="New avatar URL for your clone", required=False)
    ):
        """Update the user's shadow clone in the current channel"""
        await ctx.defer()
        
        # Check if user has a clone in this channel
        clone_data = get_shadowclone(ctx.author.id, ctx.channel.id)
        if not clone_data:
            await ctx.followup.send(embed=error_embed(
                title="No Clone Found",
                description="You don't have a shadow clone in this channel."
            ))
            return
        
        # Prepare updates
        updates = {}
        
        if name:
            if len(name) > 80:
                await ctx.followup.send(embed=error_embed(
                    title="Invalid Name",
                    description="Name cannot exceed 80 characters."
                ))
                return
            updates["name"] = name
        
        if prefix:
            if len(prefix) < 1 or len(prefix) > 5:
                await ctx.followup.send(embed=error_embed(
                    title="Invalid Prefix",
                    description="Prefix must be between 1 and 5 characters."
                ))
                return
            if any(char in prefix for char in [' ', '\n', '\t']):
                await ctx.followup.send(embed=error_embed(
                    title="Invalid Prefix",
                    description="Prefix cannot contain spaces or special whitespace characters."
                ))
                return
            updates["prefix"] = prefix
        
        if avatar_url:
            if not self.is_valid_url(avatar_url):
                await ctx.followup.send(embed=error_embed(
                    title="Invalid Avatar URL",
                    description="Please provide a valid image URL."
                ))
                return
            updates["avatar_url"] = avatar_url
        
        if not updates:
            await ctx.followup.send(embed=error_embed(
                title="No Updates",
                description="Please provide at least one field to update."
            ))
            return
        
        # Update in database
        success = update_shadowclone(ctx.author.id, ctx.channel.id, **updates)
        
        if success:
            # Get updated data
            updated_clone = get_shadowclone(ctx.author.id, ctx.channel.id)
            
            embed = success_embed(
                title="🔮 Shadow Clone Updated!",
                description="Your shadow clone has been successfully updated!"
            )
            
            embed.add_field(name="Clone Name", value=updated_clone["name"], inline=True)
            embed.add_field(name="Prefix", value=f"`{updated_clone['prefix']}`", inline=True)
            embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
            
            embed.set_thumbnail(url=updated_clone["avatar_url"])
            
            await ctx.followup.send(embed=embed)
        else:
            await ctx.followup.send(embed=error_embed(
                title="Update Failed",
                description="Failed to update clone data. Please try again."
            ))
    
    @shadowclone.command(name="list", description="List your shadow clones")
    async def list_shadowclones(self, ctx):
        """List all shadow clones for the user"""
        await ctx.defer()
        
        user_clones = get_user_shadowclones(ctx.author.id)
        
        if not user_clones:
            await ctx.followup.send(embed=info_embed(
                title="No Shadow Clones",
                description="You don't have any shadow clones yet. Use `/shadowclone create` to create one!"
            ))
            return
        
        embed = create_embed(
            title="🔮 Your Shadow Clones",
            description=f"You have {len(user_clones)}/5 shadow clones:",
            color=CONFIG["embed_color"]
        )
        
        for i, clone in enumerate(user_clones, 1):
            channel = self.bot.get_channel(int(clone["channel_id"]))
            channel_name = channel.mention if channel else "Unknown Channel"
            
            embed.add_field(
                name=f"{i}. {clone['name']}",
                value=f"**Prefix:** `{clone['prefix']}`\n**Channel:** {channel_name}",
                inline=True
            )
        
        embed.set_footer(text="Use /shadowclone update or /shadowclone delete to manage your clones")
        
        await ctx.followup.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for messages that match shadow clone prefixes"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Ignore DMs
        if not message.guild:
            return
        
        # Get all shadow clones in this channel
        clones = get_shadowclone_by_channel(message.channel.id)
        
        if not clones:
            return
        
        # Check if message starts with any clone prefix
        for clone_data in clones:
            prefix = clone_data["prefix"]
            
            if message.content.startswith(prefix):
                # Extract command and arguments
                content = message.content[len(prefix):].strip()
                
                if not content:
                    continue
                
                parts = content.split()
                command_name = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                try:
                    # Get the webhook
                    webhook = await self.bot.fetch_webhook(clone_data["webhook_id"])
                    
                    # Route the command
                    await self.command_router.route_command(
                        webhook, clone_data, command_name, args, message
                    )
                    
                except (discord.NotFound, discord.Forbidden):
                    # Webhook was deleted, deactivate the clone
                    deactivate_shadowclone(clone_data["user_id"], clone_data["channel_id"])
                except discord.HTTPException:
                    # Other webhook errors
                    pass
                
                # Only respond to the first matching prefix
                break
    
    def is_valid_url(self, url):
        """Validate if a URL is properly formatted"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

async def setup(bot):
    await bot.add_cog(ShadowClone(bot))
