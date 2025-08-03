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
    """Self-assignable role system with reaction roles"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="addselfrole", aliases=["asr"], help="Add a role to self-assignable roles")
    @commands.check(is_admin)
    async def add_self_role(self, ctx, role: discord.Role):
        """Add a role to the self-assignable roles list"""
        # Check if role is higher than bot's highest role
        if role >= ctx.guild.me.top_role:
            await ctx.send(embed=error_embed(
                title="Role Too High",
                description="I cannot manage this role as it's higher than or equal to my highest role."
            ))
            return

        # Check if role is @everyone
        if role.is_default():
            await ctx.send(embed=error_embed(
                title="Invalid Role",
                description="Cannot add @everyone as a self-assignable role."
            ))
            return

        # Get current self roles
        self_roles = get_self_roles(ctx.guild.id)

        # Check if role is already in self roles
        if str(role.id) in self_roles:
            await ctx.send(embed=warning_embed(
                title="Role Already Added",
                description=f"{role.mention} is already a self-assignable role."
            ))
            return

        # Add the role
        self_roles[str(role.id)] = {
            "name": role.name,
            "added_by": ctx.author.id,
            "added_at": discord.utils.utcnow().timestamp()
        }

        update_self_roles(ctx.guild.id, self_roles)

        await ctx.send(embed=success_embed(
            title="Self Role Added",
            description=f"✅ {role.mention} has been added to self-assignable roles.\nUsers can now use `,iam {role.name}` to get this role."
        ))

    @commands.command(name="removeselfrole", aliases=["rsr"], help="Remove a role from self-assignable roles")
    @commands.check(is_admin)
    async def remove_self_role(self, ctx, role: discord.Role):
        """Remove a role from the self-assignable roles list"""
        self_roles = get_self_roles(ctx.guild.id)

        if str(role.id) not in self_roles:
            await ctx.send(embed=error_embed(
                title="Role Not Found",
                description=f"{role.mention} is not a self-assignable role."
            ))
            return

        # Remove the role
        del self_roles[str(role.id)]
        update_self_roles(ctx.guild.id, self_roles)

        await ctx.send(embed=success_embed(
            title="Self Role Removed",
            description=f"✅ {role.mention} has been removed from self-assignable roles."
        ))

    @commands.command(name="selfroles", aliases=["sr", "roles"], help="List all self-assignable roles")
    async def list_self_roles(self, ctx):
        """List all self-assignable roles"""
        self_roles = get_self_roles(ctx.guild.id)

        if not self_roles:
            await ctx.send(embed=info_embed(
                title="No Self Roles",
                description="There are no self-assignable roles set up in this server."
            ))
            return

        embed = create_embed(
            title="Self-Assignable Roles",
            description="Here are all the roles you can assign to yourself:",
            color=CONFIG["embed_color"]
        )

        role_list = []
        for role_id, role_data in self_roles.items():
            role = ctx.guild.get_role(int(role_id))
            if role:
                role_list.append(f"• {role.mention} - `{CONFIG['prefix']}iam {role.name}`")
            else:
                # Role was deleted, remove from database
                del self_roles[role_id]

        if role_list:
            embed.add_field(
                name=f"Available Roles ({len(role_list)})",
                value="\n".join(role_list),
                inline=False
            )

            embed.add_field(
                name="How to use",
                value=f"Use `{CONFIG['prefix']}iam <role name>` to get a role\n"
                      f"Use `{CONFIG['prefix']}iamnot <role name>` to remove a role",
                inline=False
            )
        else:
            embed.description = "All self-assignable roles have been deleted from the server."

        # Update database if any roles were removed
        update_self_roles(ctx.guild.id, self_roles)

        await ctx.send(embed=embed)

    @commands.command(name="iam", help="Assign yourself a role")
    async def i_am(self, ctx, *, role_name):
        """Assign a self-assignable role to the user"""
        self_roles = get_self_roles(ctx.guild.id)

        if not self_roles:
            await ctx.send(embed=error_embed(
                title="No Self Roles",
                description="There are no self-assignable roles in this server."
            ))
            return

        # Find the role by name (case insensitive)
        target_role = None
        for role_id in self_roles:
            role = ctx.guild.get_role(int(role_id))
            if role and role.name.lower() == role_name.lower():
                target_role = role
                break

        if not target_role:
            await ctx.send(embed=error_embed(
                title="Role Not Found",
                description=f"Could not find a self-assignable role named `{role_name}`.\n"
                           f"Use `{CONFIG['prefix']}selfroles` to see available roles."
            ))
            return

        # Check if user already has the role
        if target_role in ctx.author.roles:
            await ctx.send(embed=warning_embed(
                title="Already Have Role",
                description=f"You already have the {target_role.mention} role."
            ))
            return

        try:
            await ctx.author.add_roles(target_role, reason="Self-assigned role")
            await ctx.send(embed=success_embed(
                title="Role Assigned",
                description=f"✅ You have been given the {target_role.mention} role!"
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Permission Error",
                description="I don't have permission to assign this role. Please contact an administrator."
            ))
        except discord.HTTPException:
            await ctx.send(embed=error_embed(
                title="Error",
                description="An error occurred while assigning the role. Please try again."
            ))

    @commands.command(name="iamnot", help="Remove a role from yourself")
    async def i_am_not(self, ctx, *, role_name):
        """Remove a self-assignable role from the user"""
        self_roles = get_self_roles(ctx.guild.id)

        if not self_roles:
            await ctx.send(embed=error_embed(
                title="No Self Roles",
                description="There are no self-assignable roles in this server."
            ))
            return

        # Find the role by name (case insensitive)
        target_role = None
        for role_id in self_roles:
            role = ctx.guild.get_role(int(role_id))
            if role and role.name.lower() == role_name.lower():
                target_role = role
                break

        if not target_role:
            await ctx.send(embed=error_embed(
                title="Role Not Found",
                description=f"Could not find a self-assignable role named `{role_name}`.\n"
                           f"Use `{CONFIG['prefix']}selfroles` to see available roles."
            ))
            return

        # Check if user has the role
        if target_role not in ctx.author.roles:
            await ctx.send(embed=warning_embed(
                title="Don't Have Role",
                description=f"You don't have the {target_role.mention} role."
            ))
            return

        try:
            await ctx.author.remove_roles(target_role, reason="Self-removed role")
            await ctx.send(embed=success_embed(
                title="Role Removed",
                description=f"✅ The {target_role.mention} role has been removed from you!"
            ))
        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Permission Error",
                description="I don't have permission to remove this role. Please contact an administrator."
            ))
        except discord.HTTPException:
            await ctx.send(embed=error_embed(
                title="Error",
                description="An error occurred while removing the role. Please try again."
            ))

    @commands.command(name="reactionrole", aliases=["rr"], help="Create a reaction role message")
    @commands.check(is_admin)
    async def reaction_role(self, ctx, channel: discord.TextChannel = None):
        """Create a reaction role message in the specified channel"""
        if not channel:
            channel = ctx.channel

        self_roles = get_self_roles(ctx.guild.id)

        if not self_roles:
            await ctx.send(embed=error_embed(
                title="No Self Roles",
                description="You need to add some self-assignable roles first using `addselfrole`."
            ))
            return

        # Create the reaction role embed
        embed = create_embed(
            title="🎭 Self-Assignable Roles",
            description="React to this message to get or remove roles!",
            color=CONFIG["embed_color"]
        )

        # Add roles to embed and prepare reactions
        role_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        reactions_to_add = []
        role_mapping = {}

        role_text = []
        for i, (role_id, role_data) in enumerate(self_roles.items()):
            if i >= 10:  # Limit to 10 roles
                break

            role = ctx.guild.get_role(int(role_id))
            if role:
                emoji = role_emojis[i]
                role_text.append(f"{emoji} {role.mention}")
                reactions_to_add.append(emoji)
                role_mapping[emoji] = role.id

        embed.add_field(
            name="Available Roles",
            value="\n".join(role_text) if role_text else "No valid roles found",
            inline=False
        )

        embed.set_footer(text="Click the reactions below to get or remove roles!")

        try:
            # Send the message
            message = await channel.send(embed=embed)

            # Add reactions
            for emoji in reactions_to_add:
                await message.add_reaction(emoji)

            # Store the reaction role message data
            config = get_guild_config(ctx.guild.id)
            if "reaction_roles" not in config:
                config["reaction_roles"] = {}

            config["reaction_roles"][str(message.id)] = {
                "channel_id": channel.id,
                "role_mapping": role_mapping,
                "created_by": ctx.author.id,
                "created_at": discord.utils.utcnow().timestamp()
            }

            update_guild_config(ctx.guild.id, config)

            await ctx.send(embed=success_embed(
                title="Reaction Roles Created",
                description=f"✅ Reaction role message has been created in {channel.mention}!"
            ))

        except discord.Forbidden:
            await ctx.send(embed=error_embed(
                title="Permission Error",
                description=f"I don't have permission to send messages or add reactions in {channel.mention}."
            ))
        except discord.HTTPException as e:
            await ctx.send(embed=error_embed(
                title="Error",
                description=f"An error occurred while creating the reaction role message: {str(e)}"
            ))

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reaction role additions"""
        await self.handle_reaction_role(reaction, user, add_role=True)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        """Handle reaction role removals"""
        await self.handle_reaction_role(reaction, user, add_role=False)

    async def handle_reaction_role(self, reaction, user, add_role=True):
        """Handle reaction role logic"""
        # Ignore bot reactions
        if user.bot:
            return

        # Get guild and message
        message = reaction.message
        guild = message.guild

        if not guild:
            return

        # Get guild config
        config = get_guild_config(guild.id)
        reaction_roles = config.get("reaction_roles", {})

        # Check if this message has reaction roles
        message_data = reaction_roles.get(str(message.id))
        if not message_data:
            return

        # Get the role mapping
        role_mapping = message_data.get("role_mapping", {})
        emoji = str(reaction.emoji)

        if emoji not in role_mapping:
            return

        # Get the role
        role_id = role_mapping[emoji]
        role = guild.get_role(role_id)

        if not role:
            return

        # Get the member
        member = guild.get_member(user.id)
        if not member:
            return

        try:
            if add_role:
                if role not in member.roles:
                    await member.add_roles(role, reason="Reaction role")
            else:
                if role in member.roles:
                    await member.remove_roles(role, reason="Reaction role removed")
        except (discord.Forbidden, discord.HTTPException):
            pass

async def setup(bot):
    await bot.add_cog(SelfRoles(bot))