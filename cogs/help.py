import discord
from discord.ext import commands
from config import CONFIG
from utils.embeds import help_menu_embed, category_help_embed, command_help_embed
from utils.helpers import is_mod, is_admin, is_owner

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji_categories = {
            "🔰": "antinuke",
            "🛡️": "noprefix",
            "🔨": "moderation",
            "🛠️": "utils",
            "🔊": "voice",
            "😈": "other",
            "➕": "jointocreate",
            "👥": "selfroles"
        }
    
    @commands.command(name="help", aliases=["h"], help="Shows the help menu")
    async def help(self, ctx, *, command_or_category=None):
        """Shows the help menu or information about a specific command/category"""
        prefix = CONFIG["prefix"]
        
        # If no category or command is specified, show the main help menu
        if command_or_category is None:
            embed = help_menu_embed(ctx, self.bot)
            message = await ctx.send(embed=embed)
            
            # Add reactions for navigation
            for emoji in self.emoji_categories:
                await message.add_reaction(emoji)
                
            return
        
        # Check if it's a category
        if command_or_category.lower() in [cat.lower() for cat in self.emoji_categories.values()]:
            category = command_or_category.lower()
            commands_list = [cmd for cmd in self.bot.commands 
                            if cmd.cog_name.lower() == category 
                            and (not cmd.hidden or is_owner(ctx))]
            
            if not commands_list:
                return await ctx.send(f"No commands found in category '{category}'.")
            
            embed = category_help_embed(ctx, category, commands_list)
            await ctx.send(embed=embed)
            return
        
        # Check if it's a command
        for command in self.bot.commands:
            if command.name == command_or_category or command_or_category in command.aliases:
                if command.hidden and not is_owner(ctx):
                    return await ctx.send("That command does not exist.")
                
                embed = command_help_embed(ctx, command)
                await ctx.send(embed=embed)
                return
        
        # If we got here, the command or category wasn't found
        await ctx.send(f"Command or category '{command_or_category}' not found. Use `{prefix}help` to see all available commands.")
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        # Ignore bot's own reactions
        if user.bot:
            return
        
        # Check if reaction is on a help message
        message = reaction.message
        if not message.author.id == self.bot.user.id:
            return
        
        # Check if the message has embeds and the title is "Help Menu"
        if not message.embeds or message.embeds[0].title != "Help Menu":
            return
        
        # Check if the reaction is a valid category
        emoji = str(reaction.emoji)
        if emoji not in self.emoji_categories:
            return
        
        # Get the category from the emoji
        category = self.emoji_categories[emoji]
        
        # Create and send the category help embed
        context = await self.bot.get_context(message)
        context.author = user  # Set the user as the author for permission checks
        
        # Get the commands for that category
        commands_list = [cmd for cmd in self.bot.commands 
                        if cmd.cog_name.lower() == category.lower() 
                        and (not cmd.hidden or is_owner(context))]
        
        embed = category_help_embed(context, category, commands_list)
        
        # Try to remove the user's reaction if we have permissions
        try:
            await reaction.remove(user)
        except discord.Forbidden:
            pass
        
        await message.edit(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
