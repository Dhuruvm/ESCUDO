import discord
from discord.ext import commands
import asyncio
import re
from config import CONFIG
from utils.helpers import (
    is_mod, is_admin, is_owner, get_guild_config, update_guild_config,
    get_self_roles, update_self_roles
)
from utils.embeds import (
    success_embed, error_embed, info_embed, warning_embed, create_embed
)

class SelfRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="createrole", aliases=["addrole"], help="Create a self-assignable role")
    @commands.check(is_admin)
    async def createrole(self, ctx, *, role_name):
        """Create a new self-assignable role"""
        # Check if a role with this name already exists
        existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
        if existing_role:
            await ctx.send(embed=error_embed(
                title="Role Exists",
                description=f"A role with the name '{role_name}' already exists. Please use that role or choose a different name."
            ))
            return
        
        # Create the role
        try:
            # Generate a random color for the role
            import random
            color = discord.Color.from_rgb(
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
            
            role = await ctx.guild.create_role(
                name=role_name,
                color=color,
                mentionable=True,
                reason=f"Self-assignable role created by {ctx.author}"
            )
            
            # Get the self-roles config
            config = get_self_roles(ctx.guild.id)
            
            # Initialize self_roles if it doesn't exist
            if "self_roles" not in config:
                config["self_roles"] = []
            
            # Add the role to self-assignable roles
            if str(role.id) not in config["self_roles"]:
                config["self_roles"].append(str(role.id))
                update_self_roles(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Role Created",
                description=f"✅ Created self-assignable role {role.mention}"
            ))
            
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description="I don't have permission to create roles."
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=error_embed(
                title="Role Creation Failed",
                description=f"Failed to create the role: {str(e)}"
            ))
    
    @commands.command(name="deleterole", aliases=["removerole"], help="Delete a self-assignable role")
    @commands.check(is_admin)
    async def deleterole(self, ctx, *, role: discord.Role):
        """Delete a self-assignable role"""
        # Get the self-roles config
        config = get_self_roles(ctx.guild.id)
        
        # Check if the role is self-assignable
        if "self_roles" not in config or str(role.id) not in config.get("self_roles", []):
            await ctx.send(embed=error_embed(
                title="Not Self-Assignable",
                description=f"{role.mention} is not a self-assignable role."
            ))
            return
        
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Confirm Role Deletion",
            description=f"Are you sure you want to delete the role {role.mention}? This will remove the role from all members.\n\nReact with ✅ to confirm or ❌ to cancel."
        ))
        
        await confirmation.add_reaction("✅")
        await confirmation.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirmation.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await ctx.send(embed=info_embed(
                    title="Deletion Cancelled",
                    description=f"Role deletion has been cancelled."
                ))
                return
            
            # Delete the role
            try:
                await role.delete(reason=f"Self-assignable role deleted by {ctx.author}")
                
                # Remove the role from self-assignable roles
                config["self_roles"].remove(str(role.id))
                update_self_roles(ctx.guild.id, config)
                
                # Remove the role from any reaction role messages
                if "messages" in config:
                    for msg_id, msg_data in list(config["messages"].items()):
                        if "roles" in msg_data:
                            for emoji, role_id in list(msg_data["roles"].items()):
                                if role_id == str(role.id):
                                    del msg_data["roles"][emoji]
                            
                            # If no roles left, remove the message
                            if not msg_data["roles"]:
                                del config["messages"][msg_id]
                
                update_self_roles(ctx.guild.id, config)
                
                await ctx.send(embed=success_embed(
                    title="Role Deleted",
                    description=f"✅ Self-assignable role '{role.name}' has been deleted."
                ))
                
            except discord.Forbidden:
                await ctx.send(embed=error_embed(
                    title="Missing Permissions",
                    description="I don't have permission to delete roles."
                ))
            except discord.HTTPException as e:
                await ctx.send(embed=error_embed(
                    title="Role Deletion Failed",
                    description=f"Failed to delete the role: {str(e)}"
                ))
            
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Deletion Cancelled",
                description="Role deletion timed out."
            ))
    
    @commands.command(name="addselfrole", aliases=["selfrole"], help="Add a role to self-assignable roles")
    @commands.check(is_admin)
    async def addselfrole(self, ctx, *, role: discord.Role):
        """Add an existing role to self-assignable roles"""
        # Check if the role is higher than the bot's highest role
        if role.position >= ctx.guild.me.top_role.position:
            await ctx.send(embed=error_embed(
                title="Role Too High",
                description="I cannot manage roles that are higher than or equal to my highest role."
            ))
            return
        
        # Get the self-roles config
        config = get_self_roles(ctx.guild.id)
        
        # Initialize self_roles if it doesn't exist
        if "self_roles" not in config:
            config["self_roles"] = []
        
        # Check if the role is already self-assignable
        if str(role.id) in config["self_roles"]:
            await ctx.send(embed=info_embed(
                title="Already Self-Assignable",
                description=f"{role.mention} is already a self-assignable role."
            ))
            return
        
        # Add the role to self-assignable roles
        config["self_roles"].append(str(role.id))
        update_self_roles(ctx.guild.id, config)
        
        await ctx.send(embed=success_embed(
            title="Role Added",
            description=f"✅ {role.mention} is now a self-assignable role."
        ))
    
    @commands.command(name="removeselfrole", aliases=["rmselfrole"], help="Remove a role from self-assignable roles")
    @commands.check(is_admin)
    async def removeselfrole(self, ctx, *, role: discord.Role):
        """Remove a role from self-assignable roles"""
        # Get the self-roles config
        config = get_self_roles(ctx.guild.id)
        
        # Check if the role is self-assignable
        if "self_roles" not in config or str(role.id) not in config.get("self_roles", []):
            await ctx.send(embed=error_embed(
                title="Not Self-Assignable",
                description=f"{role.mention} is not a self-assignable role."
            ))
            return
        
        # Remove the role from self-assignable roles
        config["self_roles"].remove(str(role.id))
        update_self_roles(ctx.guild.id, config)
        
        # Remove the role from any reaction role messages
        if "messages" in config:
            for msg_id, msg_data in list(config["messages"].items()):
                if "roles" in msg_data:
                    for emoji, role_id in list(msg_data["roles"].items()):
                        if role_id == str(role.id):
                            del msg_data["roles"][emoji]
                    
                    # If no roles left, remove the message
                    if not msg_data["roles"]:
                        del config["messages"][msg_id]
        
        update_self_roles(ctx.guild.id, config)
        
        await ctx.send(embed=success_embed(
            title="Role Removed",
            description=f"✅ {role.mention} is no longer a self-assignable role."
        ))
    
    @commands.command(name="selfroles", aliases=["listroles", "roles"], help="List all self-assignable roles")
    async def selfroles(self, ctx):
        """List all self-assignable roles"""
        # Get the self-roles config
        config = get_self_roles(ctx.guild.id)
        
        # Check if there are any self-assignable roles
        if "self_roles" not in config or not config["self_roles"]:
            await ctx.send(embed=info_embed(
                title="No Self-Assignable Roles",
                description="There are no self-assignable roles set up for this server."
            ))
            return
        
        # Get all self-assignable roles
        roles = []
        for role_id in config["self_roles"]:
            role = ctx.guild.get_role(int(role_id))
            if role:
                roles.append(role)
        
        # Check if any roles were found
        if not roles:
            await ctx.send(embed=info_embed(
                title="No Self-Assignable Roles",
                description="There are no self-assignable roles set up for this server."
            ))
            return
        
        # Create embed with roles list
        embed = info_embed(
            title="Self-Assignable Roles",
            description=f"There are {len(roles)} self-assignable roles in this server:"
        )
        
        # Add roles to the embed, limiting to 25 roles per field
        roles_text = ""
        for i, role in enumerate(roles):
            roles_text += f"{i+1}. {role.mention}\n"
            
            # Create a new field every 25 roles
            if (i + 1) % 25 == 0 or i == len(roles) - 1:
                embed.add_field(name="Roles", value=roles_text, inline=False)
                roles_text = ""
        
        # Add info about how to get roles
        prefix = CONFIG["prefix"]
        embed.set_footer(text=f"Use {prefix}getrole <role name> to get a role!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name="getrole", help="Get or remove a self-assignable role")
    async def getrole(self, ctx, *, role_name):
        """Give yourself or remove a self-assignable role"""
        # Get the self-roles config
        config = get_self_roles(ctx.guild.id)
        
        # Check if there are any self-assignable roles
        if "self_roles" not in config or not config["self_roles"]:
            await ctx.send(embed=error_embed(
                title="No Self-Assignable Roles",
                description="There are no self-assignable roles set up for this server."
            ))
            return
        
        # Find the role
        role = None
        for role_id in config["self_roles"]:
            r = ctx.guild.get_role(int(role_id))
            if r and r.name.lower() == role_name.lower():
                role = r
                break
        
        # If no exact match found, try partial match
        if role is None:
            for role_id in config["self_roles"]:
                r = ctx.guild.get_role(int(role_id))
                if r and role_name.lower() in r.name.lower():
                    role = r
                    break
        
        if role is None:
            await ctx.send(embed=error_embed(
                title="Role Not Found",
                description=f"Could not find a self-assignable role called '{role_name}'."
            ))
            return
        
        # Check if the user already has the role
        if role in ctx.author.roles:
            # Remove the role
            try:
                await ctx.author.remove_roles(role, reason="Self-assignable role removed")
                await ctx.send(embed=success_embed(
                    title="Role Removed",
                    description=f"✅ Removed {role.mention} from you."
                ))
            except discord.Forbidden:
                await ctx.send(embed=error_embed(
                    title="Missing Permissions",
                    description="I don't have permission to remove that role."
                ))
        else:
            # Add the role
            try:
                await ctx.author.add_roles(role, reason="Self-assignable role added")
                await ctx.send(embed=success_embed(
                    title="Role Added",
                    description=f"✅ Added {role.mention} to you."
                ))
            except discord.Forbidden:
                await ctx.send(embed=error_embed(
                    title="Missing Permissions",
                    description="I don't have permission to add that role."
                ))
    
    @commands.command(name="reactionrole", aliases=["rr", "reactrole"], help="Create a reaction role message")
    @commands.check(is_admin)
    async def reactionrole(self, ctx, channel: discord.TextChannel = None):
        """Create a reaction role message"""
        channel = channel or ctx.channel
        
        # Check if the bot has permission to add reactions
        if not channel.permissions_for(ctx.guild.me).add_reactions:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description=f"I don't have permission to add reactions in {channel.mention}."
            ))
            return
        
        # Get the self-roles config
        config = get_self_roles(ctx.guild.id)
        
        # Check if there are any self-assignable roles
        if "self_roles" not in config or not config["self_roles"]:
            await ctx.send(embed=error_embed(
                title="No Self-Assignable Roles",
                description="There are no self-assignable roles set up for this server."
            ))
            return
        
        # Get all self-assignable roles
        roles = []
        for role_id in config["self_roles"]:
            role = ctx.guild.get_role(int(role_id))
            if role:
                roles.append(role)
        
        if not roles:
            await ctx.send(embed=error_embed(
                title="No Self-Assignable Roles",
                description="There are no self-assignable roles set up for this server."
            ))
            return
        
        # Start the setup process
        setup_msg = await ctx.send(embed=info_embed(
            title="Reaction Role Setup",
            description="Let's set up a reaction role message. Please provide a title for the message."
        ))
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        title = "React to get roles"
        description = "React with the emojis below to get the corresponding roles!"
        
        try:
            # Get the title
            await ctx.send("Please provide a title for the reaction role message:")
            title_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            title = title_msg.content
            
            # Get the description
            await ctx.send("Please provide a description for the reaction role message:")
            desc_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
            description = desc_msg.content
            
            # Create the reaction role message
            embed = create_embed(
                title=title,
                description=description,
                color=CONFIG["embed_color"]
            )
            
            # Send the message to the target channel
            reaction_msg = await channel.send(embed=embed)
            
            # Set up reaction-role pairs
            await ctx.send(embed=info_embed(
                title="Reaction Role Setup",
                description="Now let's add roles to the message. For each role, you'll provide an emoji and select a role.\n\nType `done` when you're finished adding roles."
            ))
            
            reaction_roles = {}
            
            while True:
                # Ask for an emoji
                await ctx.send("Please send an emoji to use for a role (or type `done` to finish):")
                emoji_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
                
                if emoji_msg.content.lower() == "done":
                    break
                
                # Extract the emoji
                emoji = emoji_msg.content.strip()
                
                # For custom emojis, extract the ID
                custom_emoji_match = re.match(r'<a?:([a-zA-Z0-9_]+):([0-9]+)>', emoji)
                if custom_emoji_match:
                    emoji_id = custom_emoji_match.group(2)
                    emoji_name = custom_emoji_match.group(1)
                    is_animated = emoji.startswith('<a:')
                    emoji = emoji  # Keep the full emoji string for custom emojis
                
                # Ask for a role
                role_list = "\n".join([f"{i+1}. {role.name}" for i, role in enumerate(roles)])
                await ctx.send(f"Please select a role by number:\n{role_list}")
                
                role_msg = await self.bot.wait_for("message", timeout=60.0, check=check)
                
                try:
                    role_index = int(role_msg.content) - 1
                    if 0 <= role_index < len(roles):
                        selected_role = roles[role_index]
                        
                        # Add the reaction to the message
                        try:
                            await reaction_msg.add_reaction(emoji)
                            
                            # Add to the reaction-role mapping
                            reaction_roles[emoji] = str(selected_role.id)
                            
                            await ctx.send(embed=success_embed(
                                title="Role Added",
                                description=f"Added {emoji} for role {selected_role.mention}"
                            ))
                        except discord.HTTPException:
                            await ctx.send(embed=error_embed(
                                title="Invalid Emoji",
                                description="I couldn't use that emoji. Please try a different one."
                            ))
                    else:
                        await ctx.send(embed=error_embed(
                            title="Invalid Selection",
                            description="Please select a valid role number."
                        ))
                except ValueError:
                    await ctx.send(embed=error_embed(
                        title="Invalid Input",
                        description="Please enter a number."
                    ))
            
            # Save the reaction role message to the config
            if not "messages" in config:
                config["messages"] = {}
            
            config["messages"][str(reaction_msg.id)] = {
                "channel_id": str(channel.id),
                "roles": reaction_roles
            }
            
            update_self_roles(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Reaction Roles Set Up",
                description=f"✅ Reaction role message has been set up in {channel.mention}!"
            ))
            
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Setup Cancelled",
                description="Reaction role setup timed out."
            ))
    
    @commands.command(name="removerr", aliases=["deleterr", "rmrr"], help="Remove a reaction role message")
    @commands.check(is_admin)
    async def removerr(self, ctx, message_id: int = None):
        """Remove a reaction role message"""
        # Get the self-roles config
        config = get_self_roles(ctx.guild.id)
        
        # Check if there are any reaction role messages
        if "messages" not in config or not config["messages"]:
            await ctx.send(embed=error_embed(
                title="No Reaction Role Messages",
                description="There are no reaction role messages set up for this server."
            ))
            return
        
        # If no message ID provided, list all reaction role messages
        if message_id is None:
            embed = info_embed(
                title="Reaction Role Messages",
                description="Here are all the reaction role messages in this server:"
            )
            
            for msg_id, msg_data in config["messages"].items():
                channel_id = msg_data.get("channel_id")
                channel = ctx.guild.get_channel(int(channel_id)) if channel_id else None
                channel_name = channel.mention if channel else "Unknown Channel"
                
                embed.add_field(
                    name=f"Message ID: {msg_id}",
                    value=f"Channel: {channel_name}\nRoles: {len(msg_data.get('roles', {}))}",
                    inline=False
                )
            
            prefix = CONFIG["prefix"]
            embed.set_footer(text=f"Use {prefix}removerr <message_id> to remove a message")
            
            await ctx.send(embed=embed)
            return
        
        # Check if the message exists in the config
        message_id_str = str(message_id)
        if message_id_str not in config["messages"]:
            await ctx.send(embed=error_embed(
                title="Message Not Found",
                description=f"Could not find a reaction role message with ID {message_id}."
            ))
            return
        
        # Ask for confirmation
        confirmation = await ctx.send(embed=warning_embed(
            title="Confirm Removal",
            description=f"Are you sure you want to remove the reaction role message with ID {message_id}?\n\nReact with ✅ to confirm or ❌ to cancel."
        ))
        
        await confirmation.add_reaction("✅")
        await confirmation.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirmation.id
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await ctx.send(embed=info_embed(
                    title="Removal Cancelled",
                    description=f"Removal of reaction role message has been cancelled."
                ))
                return
            
            # Try to find and delete the message
            message_data = config["messages"][message_id_str]
            channel_id = message_data.get("channel_id")
            
            if channel_id:
                channel = ctx.guild.get_channel(int(channel_id))
                if channel:
                    try:
                        message = await channel.fetch_message(int(message_id))
                        await message.delete()
                    except (discord.NotFound, discord.Forbidden):
                        pass
            
            # Remove the message from the config
            del config["messages"][message_id_str]
            update_self_roles(ctx.guild.id, config)
            
            await ctx.send(embed=success_embed(
                title="Message Removed",
                description=f"✅ Reaction role message with ID {message_id} has been removed."
            ))
            
        except asyncio.TimeoutError:
            await ctx.send(embed=info_embed(
                title="Removal Cancelled",
                description="Reaction role message removal timed out."
            ))
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Handle adding roles when users react to reaction role messages"""
        # Skip bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Get the self-roles config for the guild
        config = get_self_roles(payload.guild_id)
        
        # Check if this is a reaction role message
        if "messages" not in config or str(payload.message_id) not in config["messages"]:
            return
        
        message_data = config["messages"][str(payload.message_id)]
        
        # Check if the emoji is registered for a role
        emoji = str(payload.emoji)
        if "roles" not in message_data or emoji not in message_data["roles"]:
            return
        
        # Get the role ID and role
        role_id = message_data["roles"][emoji]
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        role = guild.get_role(int(role_id))
        if not role:
            return
        
        # Get the member
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        # Add the role
        try:
            await member.add_roles(role, reason="Reaction role")
            
            # Try to DM the user
            try:
                await member.send(embed=success_embed(
                    title="Role Added",
                    description=f"You have been given the **{role.name}** role in **{guild.name}**."
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            # Try to remove the reaction if we can't add the role
            channel = guild.get_channel(payload.channel_id)
            if channel:
                try:
                    message = await channel.fetch_message(payload.message_id)
                    await message.remove_reaction(payload.emoji, member)
                except discord.Forbidden:
                    pass
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        """Handle removing roles when users remove reactions from reaction role messages"""
        # Skip bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Get the self-roles config for the guild
        config = get_self_roles(payload.guild_id)
        
        # Check if this is a reaction role message
        if "messages" not in config or str(payload.message_id) not in config["messages"]:
            return
        
        message_data = config["messages"][str(payload.message_id)]
        
        # Check if the emoji is registered for a role
        emoji = str(payload.emoji)
        if "roles" not in message_data or emoji not in message_data["roles"]:
            return
        
        # Get the role ID and role
        role_id = message_data["roles"][emoji]
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        role = guild.get_role(int(role_id))
        if not role:
            return
        
        # Get the member
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        # Remove the role
        try:
            await member.remove_roles(role, reason="Reaction role removed")
            
            # Try to DM the user
            try:
                await member.send(embed=info_embed(
                    title="Role Removed",
                    description=f"The **{role.name}** role has been removed from you in **{guild.name}**."
                ))
            except discord.Forbidden:
                pass
                
        except discord.Forbidden:
            pass

async def setup(bot):
    await bot.add_cog(SelfRoles(bot))
