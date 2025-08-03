
import discord
import asyncio
from utils.embeds import success_embed, error_embed, info_embed, warning_embed

class CommandRouter:
    """Routes and replicates bot commands for shadow clones"""
    
    def __init__(self, bot):
        self.bot = bot
    
    async def route_command(self, webhook, clone_data, command_name, args, original_message):
        """Route a command to the appropriate handler and send via webhook"""
        try:
            # Create a mock context for command processing
            mock_ctx = MockContext(
                bot=self.bot,
                channel=original_message.channel,
                author=original_message.author,
                guild=original_message.guild,
                message=original_message,
                webhook=webhook,
                clone_data=clone_data
            )
            
            # Handle specific commands
            if command_name == "ping":
                await self.handle_ping(mock_ctx)
            elif command_name == "help":
                await self.handle_help(mock_ctx, args)
            elif command_name == "userinfo" or command_name == "user" or command_name == "ui":
                await self.handle_userinfo(mock_ctx, args)
            elif command_name == "serverinfo" or command_name == "server" or command_name == "si":
                await self.handle_serverinfo(mock_ctx)
            elif command_name == "avatar" or command_name == "av":
                await self.handle_avatar(mock_ctx, args)
            elif command_name == "botinfo" or command_name == "bi" or command_name == "info":
                await self.handle_botinfo(mock_ctx)
            elif command_name == "poll":
                await self.handle_poll(mock_ctx, args)
            elif command_name == "8ball":
                await self.handle_8ball(mock_ctx, args)
            else:
                # Default response for unknown commands
                embed = error_embed(
                    title="Unknown Command",
                    description=f"Command `{command_name}` not found. Use `{clone_data['prefix']}help` to see available commands."
                )
                await self.send_webhook_embed(webhook, clone_data, embed)
                
        except Exception as e:
            embed = error_embed(
                title="Command Error",
                description=f"An error occurred while executing the command: {str(e)}"
            )
            await self.send_webhook_embed(webhook, clone_data, embed)
    
    async def send_webhook_embed(self, webhook, clone_data, embed):
        """Send an embed using the webhook"""
        try:
            await webhook.send(
                embed=embed,
                username=clone_data["name"],
                avatar_url=clone_data["avatar_url"]
            )
        except discord.HTTPException:
            pass
    
    async def send_webhook_message(self, webhook, clone_data, content=None, embed=None):
        """Send a message using the webhook"""
        try:
            await webhook.send(
                content=content,
                embed=embed,
                username=clone_data["name"],
                avatar_url=clone_data["avatar_url"]
            )
        except discord.HTTPException:
            pass
    
    async def handle_ping(self, ctx):
        """Handle ping command"""
        import time
        start_time = time.time()
        
        # Simulate latency calculation
        api_latency = round((time.time() - start_time) * 1000)
        websocket_latency = round(self.bot.latency * 1000)
        
        embed = info_embed(
            title="🏓 Pong!",
            description=f"**API Latency:** {api_latency}ms\n**Websocket Latency:** {websocket_latency}ms"
        )
        
        await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)
    
    async def handle_help(self, ctx, args):
        """Handle help command"""
        embed = info_embed(
            title="🔮 Shadow Clone Help",
            description=f"I'm a shadow clone of ESCUDO! My prefix is `{ctx.clone_data['prefix']}`"
        )
        
        embed.add_field(
            name="Available Commands",
            value=f"`{ctx.clone_data['prefix']}ping` - Check latency\n"
                  f"`{ctx.clone_data['prefix']}help` - Show this help\n"
                  f"`{ctx.clone_data['prefix']}userinfo` - User information\n"
                  f"`{ctx.clone_data['prefix']}serverinfo` - Server information\n"
                  f"`{ctx.clone_data['prefix']}avatar` - User avatar\n"
                  f"`{ctx.clone_data['prefix']}botinfo` - Bot information\n"
                  f"`{ctx.clone_data['prefix']}poll` - Create a poll\n"
                  f"`{ctx.clone_data['prefix']}8ball` - Magic 8-ball",
            inline=False
        )
        
        await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)
    
    async def handle_userinfo(self, ctx, args):
        """Handle userinfo command"""
        from utils.embeds import create_embed
        
        # Try to get mentioned user or default to author
        member = ctx.author
        if args and len(args) > 0:
            # Try to parse user mention or ID
            user_arg = args[0].strip('<@!>')
            try:
                member = ctx.guild.get_member(int(user_arg))
                if not member:
                    member = ctx.author
            except ValueError:
                member = ctx.author
        
        embed = create_embed(
            title=f"User Information - {member.display_name}",
            color=member.color
        )
        
        embed.set_thumbnail(url=member.display_avatar.url)
        
        created_at = int(member.created_at.timestamp())
        joined_at = int(member.joined_at.timestamp()) if member.joined_at else "Unknown"
        
        embed.add_field(name="Username", value=f"{member}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Bot", value="Yes" if member.bot else "No", inline=True)
        embed.add_field(name="Created On", value=f"<t:{created_at}:F>\n(<t:{created_at}:R>)", inline=False)
        
        if isinstance(joined_at, int):
            embed.add_field(name="Joined Server", value=f"<t:{joined_at}:F>\n(<t:{joined_at}:R>)", inline=False)
        
        await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)
    
    async def handle_serverinfo(self, ctx):
        """Handle serverinfo command"""
        from utils.embeds import create_embed
        from config import CONFIG
        
        guild = ctx.guild
        
        embed = create_embed(
            title=f"Server Information - {guild.name}",
            color=CONFIG["embed_color"]
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        created_at = int(guild.created_at.timestamp())
        bots = sum(1 for member in guild.members if member.bot)
        humans = guild.member_count - bots
        
        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(name="Owner", value=guild.owner.mention if guild.owner else "Unknown", inline=True)
        embed.add_field(name="Created On", value=f"<t:{created_at}:F>\n(<t:{created_at}:R>)", inline=True)
        embed.add_field(name="Members", value=f"Total: {guild.member_count}\nHumans: {humans}\nBots: {bots}", inline=True)
        
        await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)
    
    async def handle_avatar(self, ctx, args):
        """Handle avatar command"""
        from utils.embeds import create_embed
        
        member = ctx.author
        if args and len(args) > 0:
            user_arg = args[0].strip('<@!>')
            try:
                member = ctx.guild.get_member(int(user_arg))
                if not member:
                    member = ctx.author
            except ValueError:
                member = ctx.author
        
        embed = create_embed(
            title=f"Avatar for {member}",
            color=member.color
        )
        
        embed.set_image(url=member.display_avatar.url)
        
        await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)
    
    async def handle_botinfo(self, ctx):
        """Handle botinfo command"""
        from utils.embeds import create_embed
        from config import CONFIG
        
        embed = create_embed(
            title=f"Shadow Clone Information",
            color=CONFIG["embed_color"]
        )
        
        embed.set_thumbnail(url=ctx.clone_data["avatar_url"])
        
        embed.add_field(name="Clone Name", value=ctx.clone_data["name"], inline=True)
        embed.add_field(name="Prefix", value=ctx.clone_data["prefix"], inline=True)
        embed.add_field(name="Original Bot", value="ESCUDO", inline=True)
        embed.add_field(name="Clone Owner", value=f"<@{ctx.clone_data['user_id']}>", inline=True)
        
        await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)
    
    async def handle_poll(self, ctx, args):
        """Handle poll command"""
        from utils.embeds import create_embed
        
        if not args:
            embed = error_embed(
                title="Poll Error",
                description="Please provide a question for the poll."
            )
            await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)
            return
        
        question = " ".join(args)
        
        embed = create_embed(
            title="📊 Poll",
            description=question
        )
        embed.set_footer(text=f"Poll by {ctx.author}")
        
        # Send the poll and add reactions
        message = await ctx.webhook.send(
            embed=embed,
            username=ctx.clone_data["name"],
            avatar_url=ctx.clone_data["avatar_url"],
            wait=True
        )
        
        await message.add_reaction("👍")
        await message.add_reaction("👎")
    
    async def handle_8ball(self, ctx, args):
        """Handle 8ball command"""
        import random
        
        if not args:
            embed = error_embed(
                title="Magic 8-Ball",
                description="Please ask a question!"
            )
            await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)
            return
        
        responses = [
            "It is certain", "Without a doubt", "Yes definitely", "You may rely on it",
            "As I see it, yes", "Most likely", "Outlook good", "Yes", "Signs point to yes",
            "Reply hazy, try again", "Ask again later", "Better not tell you now",
            "Cannot predict now", "Concentrate and ask again", "Don't count on it",
            "My reply is no", "My sources say no", "Outlook not so good", "Very doubtful"
        ]
        
        question = " ".join(args)
        answer = random.choice(responses)
        
        embed = info_embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** {question}\n**Answer:** {answer}"
        )
        
        await self.send_webhook_embed(ctx.webhook, ctx.clone_data, embed)


class MockContext:
    """Mock context class for command routing"""
    
    def __init__(self, bot, channel, author, guild, message, webhook, clone_data):
        self.bot = bot
        self.channel = channel
        self.author = author
        self.guild = guild
        self.message = message
        self.webhook = webhook
        self.clone_data = clone_data
