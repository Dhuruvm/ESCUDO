import discord
from discord.ext import commands
import random
import asyncio
import datetime
from config import CONFIG
from utils.helpers import (
    is_mod, is_admin, is_owner, get_guild_config, update_guild_config
)
from utils.embeds import (
    success_embed, error_embed, info_embed, warning_embed, create_embed
)

class Others(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="8ball", aliases=["eightball", "8b"], help="Ask the magic 8ball a question")
    async def eightball(self, ctx, *, question=None):
        """Ask the magic 8ball a question and get a random response"""
        if question is None:
            await ctx.send(embed=error_embed(
                title="Missing Question",
                description="You need to ask a question!"
            ))
            return
        
        responses = [
            # Positive answers
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes – definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            # Neutral answers
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            # Negative answers
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        
        response = random.choice(responses)
        
        embed = create_embed(
            title="🎱 Magic 8Ball",
            description=f"**Question:** {question}\n\n**Answer:** {response}",
            color=CONFIG["embed_color"]
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="roll", aliases=["dice"], help="Roll a dice")
    async def roll(self, ctx, dice: str = "1d6"):
        """Roll dice in NdN format"""
        try:
            # Parse the dice format
            rolls, limit = map(int, dice.split('d'))
        except Exception:
            await ctx.send(embed=error_embed(
                title="Format Error",
                description="Format has to be in NdN format!\nExample: `1d6` (1 dice with 6 sides)"
            ))
            return
        
        # Validate the input
        if rolls < 1 or limit < 1:
            await ctx.send(embed=error_embed(
                title="Invalid Input",
                description="Both number of dice and number of sides must be positive!"
            ))
            return
        
        if rolls > 100:
            await ctx.send(embed=error_embed(
                title="Too Many Dice",
                description="You can roll a maximum of 100 dice at once."
            ))
            return
        
        if limit > 1000:
            await ctx.send(embed=error_embed(
                title="Too Many Sides",
                description="Dice can have a maximum of 1000 sides."
            ))
            return
        
        # Roll the dice
        results = [random.randint(1, limit) for _ in range(rolls)]
        total = sum(results)
        
        # Format the output
        if rolls == 1:
            embed = info_embed(
                title="🎲 Dice Roll",
                description=f"You rolled a **{results[0]}**"
            )
        else:
            individual_rolls = ", ".join(str(r) for r in results)
            embed = info_embed(
                title="🎲 Dice Roll",
                description=f"You rolled {rolls}d{limit}:\n\nResults: {individual_rolls}\nTotal: **{total}**"
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="flip", aliases=["coin"], help="Flip a coin")
    async def flip(self, ctx, number: int = 1):
        """Flip a coin one or more times"""
        # Validate the input
        if number < 1:
            await ctx.send(embed=error_embed(
                title="Invalid Input",
                description="Number of flips must be positive!"
            ))
            return
        
        if number > 100:
            await ctx.send(embed=error_embed(
                title="Too Many Flips",
                description="You can flip a maximum of 100 coins at once."
            ))
            return
        
        # Flip the coins
        flips = [random.choice(["Heads", "Tails"]) for _ in range(number)]
        
        # Count heads and tails
        heads = flips.count("Heads")
        tails = flips.count("Tails")
        
        # Format the output
        if number == 1:
            embed = info_embed(
                title="🪙 Coin Flip",
                description=f"The coin landed on **{flips[0]}**!"
            )
        else:
            embed = info_embed(
                title="🪙 Coin Flip",
                description=f"You flipped {number} coins:\n\nHeads: {heads}\nTails: {tails}"
            )
            
            # If less than 20 flips, show individual results
            if number <= 20:
                result_str = ", ".join(flips)
                embed.add_field(name="Results", value=result_str, inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="choose", aliases=["pick"], help="Let the bot choose between options")
    async def choose(self, ctx, *options):
        """Choose between multiple options"""
        # Check if there are enough options
        if len(options) < 2:
            await ctx.send(embed=error_embed(
                title="Not Enough Options",
                description="Please provide at least 2 options to choose from!"
            ))
            return
        
        # Choose a random option
        choice = random.choice(options)
        
        embed = info_embed(
            title="🤔 Choice Made",
            description=f"I choose: **{choice}**"
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="rps", help="Play rock, paper, scissors with the bot")
    async def rps(self, ctx, user_choice=None):
        """Play Rock, Paper, Scissors with the bot"""
        choices = ["rock", "paper", "scissors"]
        
        # If no choice is provided, show the options
        if user_choice is None:
            await ctx.send(embed=info_embed(
                title="Rock, Paper, Scissors",
                description="Choose one of: `rock`, `paper`, or `scissors`"
            ))
            return
        
        # Validate the user's choice
        user_choice = user_choice.lower()
        if user_choice not in choices:
            await ctx.send(embed=error_embed(
                title="Invalid Choice",
                description="Please choose one of: `rock`, `paper`, or `scissors`"
            ))
            return
        
        # Bot's choice
        bot_choice = random.choice(choices)
        
        # Determine the winner
        if user_choice == bot_choice:
            result = "It's a tie!"
            color = CONFIG["info_color"]
        elif (user_choice == "rock" and bot_choice == "scissors") or \
             (user_choice == "paper" and bot_choice == "rock") or \
             (user_choice == "scissors" and bot_choice == "paper"):
            result = "You win!"
            color = CONFIG["success_color"]
        else:
            result = "I win!"
            color = CONFIG["error_color"]
        
        # Emojis for each choice
        emojis = {
            "rock": "🪨",
            "paper": "📄",
            "scissors": "✂️"
        }
        
        # Create the embed
        embed = create_embed(
            title="Rock, Paper, Scissors",
            description=f"You chose: {emojis[user_choice]} **{user_choice}**\nI chose: {emojis[bot_choice]} **{bot_choice}**\n\n**{result}**",
            color=color
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="say", help="Make the bot say something")
    @commands.check(is_mod)
    async def say(self, ctx, channel: discord.TextChannel = None, *, message=None):
        """Make the bot say something in a specified channel"""
        # Check if a message was provided
        if message is None:
            if channel is None:
                await ctx.send(embed=error_embed(
                    title="Missing Message",
                    description="Please provide a message for me to say!"
                ))
                return
            
            # If no channel specified but a message, use current channel and first argument as message
            message = channel.name + " " + " ".join(ctx.message.content.split()[2:])
            channel = ctx.channel
        
        # Check if the bot has permission to send messages in the target channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description=f"I don't have permission to send messages in {channel.mention}."
            ))
            return
        
        # Delete the command message if possible
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        
        # Send the message to the target channel
        try:
            await channel.send(message)
            
            # If the target channel is different from the current channel, send a confirmation
            if channel.id != ctx.channel.id:
                await ctx.send(embed=success_embed(
                    title="Message Sent",
                    description=f"✅ Message sent to {channel.mention}."
                ))
                
        except discord.HTTPException as e:
            await ctx.send(embed=error_embed(
                title="Message Failed",
                description=f"Failed to send the message: {str(e)}"
            ))
    
    @commands.command(name="embed", help="Make the bot send an embed")
    @commands.check(is_mod)
    async def embed(self, ctx, channel: discord.TextChannel = None, *, content=None):
        """Make the bot send an embed with specified content"""
        # Check if content was provided
        if content is None:
            if channel is None:
                await ctx.send(embed=error_embed(
                    title="Missing Content",
                    description="Please provide content for the embed!"
                ))
                return
            
            # If no channel specified but content, use current channel and first argument as content
            content = channel.name + " " + " ".join(ctx.message.content.split()[2:])
            channel = ctx.channel
        
        # Check if the bot has permission to send messages in the target channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(embed=error_embed(
                title="Missing Permissions",
                description=f"I don't have permission to send messages in {channel.mention}."
            ))
            return
        
        # Parse the content for title and description
        if "||" in content:
            title, description = content.split("||", 1)
        else:
            title = "Embed Message"
            description = content
        
        # Create and send the embed
        embed = create_embed(
            title=title.strip(),
            description=description.strip(),
            color=CONFIG["embed_color"]
        )
        
        embed.set_footer(text=f"Sent by {ctx.author}")
        
        # Delete the command message if possible
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass
        
        # Send the embed to the target channel
        try:
            await channel.send(embed=embed)
            
            # If the target channel is different from the current channel, send a confirmation
            if channel.id != ctx.channel.id:
                await ctx.send(embed=success_embed(
                    title="Embed Sent",
                    description=f"✅ Embed sent to {channel.mention}."
                ))
                
        except discord.HTTPException as e:
            await ctx.send(embed=error_embed(
                title="Embed Failed",
                description=f"Failed to send the embed: {str(e)}"
            ))
    
    @commands.command(name="simplepoll", help="Create a simple poll")
    @commands.check(is_mod)
    async def simplepoll(self, ctx, *, question):
        """Create a simple yes/no poll"""
        # Create the poll embed
        embed = create_embed(
            title="📊 Poll",
            description=question,
            color=CONFIG["embed_color"]
        )
        
        embed.set_footer(text=f"Poll by {ctx.author}")
        
        # Send the poll
        poll_message = await ctx.send(embed=embed)
        
        # Add reactions
        await poll_message.add_reaction("👍")  # Yes
        await poll_message.add_reaction("👎")  # No
    
    @commands.command(name="multipoll", aliases=["advpoll"], help="Create a multiple choice poll")
    @commands.check(is_mod)
    async def multipoll(self, ctx, question, *options):
        """Create a multiple choice poll with up to 10 options"""
        # Check if there are options
        if not options:
            await ctx.send(embed=error_embed(
                title="Missing Options",
                description="Please provide at least one option for the poll!"
            ))
            return
        
        # Check if there are too many options
        if len(options) > 10:
            await ctx.send(embed=error_embed(
                title="Too Many Options",
                description="You can only have up to 10 options in a poll."
            ))
            return
        
        # Create the poll embed
        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        description = [f"{emoji_numbers[i]} {option}" for i, option in enumerate(options)]
        description = "\n".join(description)
        
        embed = create_embed(
            title="📊 Multiple Choice Poll",
            description=f"**{question}**\n\n{description}",
            color=CONFIG["embed_color"]
        )
        
        embed.set_footer(text=f"Poll by {ctx.author}")
        
        # Send the poll
        poll_message = await ctx.send(embed=embed)
        
        # Add reactions
        for i in range(len(options)):
            await poll_message.add_reaction(emoji_numbers[i])
    
    @commands.command(name="ascii", help="Convert text to ASCII art")
    async def ascii(self, ctx, *, text=None):
        """Convert text to ASCII art"""
        if text is None:
            await ctx.send(embed=error_embed(
                title="Missing Text",
                description="Please provide text to convert to ASCII art!"
            ))
            return
        
        # Limit text length to prevent spam
        if len(text) > 50:
            await ctx.send(embed=error_embed(
                title="Text Too Long",
                description="ASCII text is limited to 50 characters."
            ))
            return
        
        # Simple ASCII art conversion
        ascii_art = ""
        for char in text:
            if char.isalpha():
                ascii_art += f"{char} "
            elif char.isdigit():
                ascii_art += f"{char} "
            elif char == " ":
                ascii_art += "   "
            else:
                ascii_art += f"{char} "
        
        # Send the ASCII art in a code block
        await ctx.send(f"```\n{ascii_art}\n```")
    
    @commands.command(name="reverse", help="Reverse the given text")
    async def reverse(self, ctx, *, text=None):
        """Reverse the provided text"""
        if text is None:
            await ctx.send(embed=error_embed(
                title="Missing Text",
                description="Please provide text to reverse!"
            ))
            return
        
        # Reverse the text
        reversed_text = text[::-1]
        
        await ctx.send(embed=info_embed(
            title="Text Reversed",
            description=f"**Original:** {text}\n**Reversed:** {reversed_text}"
        ))
    
    @commands.command(name="emojify", help="Convert text to emoji text")
    async def emojify(self, ctx, *, text=None):
        """Convert text to emoji text (regional indicators)"""
        if text is None:
            await ctx.send(embed=error_embed(
                title="Missing Text",
                description="Please provide text to emojify!"
            ))
            return
        
        # Limit text length to prevent spam
        if len(text) > 100:
            await ctx.send(embed=error_embed(
                title="Text Too Long",
                description="Emojify is limited to 100 characters."
            ))
            return
        
        # Convert to lowercase and replace characters
        text = text.lower()
        char_mapping = {
            'a': '🇦', 'b': '🇧', 'c': '🇨', 'd': '🇩', 'e': '🇪', 'f': '🇫', 'g': '🇬',
            'h': '🇭', 'i': '🇮', 'j': '🇯', 'k': '🇰', 'l': '🇱', 'm': '🇲', 'n': '🇳',
            'o': '🇴', 'p': '🇵', 'q': '🇶', 'r': '🇷', 's': '🇸', 't': '🇹', 'u': '🇺',
            'v': '🇻', 'w': '🇼', 'x': '🇽', 'y': '🇾', 'z': '🇿', ' ': '  ',
            '0': '0️⃣', '1': '1️⃣', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣',
            '5': '5️⃣', '6': '6️⃣', '7': '7️⃣', '8': '8️⃣', '9': '9️⃣'
        }
        
        emojified = ""
        for char in text:
            if char in char_mapping:
                emojified += char_mapping[char] + " "
            else:
                emojified += char + " "
        
        # Check if the result is too long
        if len(emojified) > 2000:
            await ctx.send(embed=error_embed(
                title="Result Too Long",
                description="The emojified text is too long to send."
            ))
            return
        
        await ctx.send(emojified)
    
    @commands.command(name="guildicon", aliases=["servericon", "serveravatar"], help="Show the server icon")
    async def guildicon(self, ctx):
        """Display the server icon in full size"""
        # Check if the server has an icon
        if not ctx.guild.icon:
            await ctx.send(embed=error_embed(
                title="No Server Icon",
                description="This server doesn't have an icon."
            ))
            return
        
        # Create the embed with the server icon
        embed = create_embed(
            title=f"Server Icon - {ctx.guild.name}",
            color=CONFIG["embed_color"]
        )
        
        embed.set_image(url=ctx.guild.icon.url)
        
        # Add links to different formats
        formats = []
        for fmt in ["png", "jpg", "webp"]:
            formats.append(f"[{fmt}]({ctx.guild.icon.with_format(fmt).url})")
        
        if ctx.guild.icon.is_animated():
            formats.append(f"[gif]({ctx.guild.icon.with_format('gif').url})")
        
        embed.add_field(name="Links", value=" | ".join(formats), inline=False)
        
        await ctx.send(embed=embed)
    
    @commands.command(name="urban", help="Look up a word in the Urban Dictionary")
    async def urban(self, ctx, *, word=None):
        """Look up a word in the Urban Dictionary"""
        if word is None:
            await ctx.send(embed=error_embed(
                title="Missing Word",
                description="Please provide a word to look up in the Urban Dictionary!"
            ))
            return
        
        # Send a message indicating the lookup is in progress
        message = await ctx.send(embed=info_embed(
            title="Looking up...",
            description=f"Looking up '{word}' in the Urban Dictionary..."
        ))
        
        # Since we're not making actual API calls, we'll simulate it
        await asyncio.sleep(1)  # Simulate API call time
        
        # For demo purposes, we'll create a mock response
        mock_definitions = [
            {
                "definition": "This would be a real definition from Urban Dictionary, but we're mocking this data for the demo.",
                "example": "Here would be an example usage of the term.",
                "thumbs_up": random.randint(100, 5000),
                "thumbs_down": random.randint(10, 500)
            },
            {
                "definition": "An alternative definition would appear here for the same term.",
                "example": "Another example of usage would be here.",
                "thumbs_up": random.randint(50, 2000),
                "thumbs_down": random.randint(5, 200)
            }
        ]
        
        # If we get a result
        if mock_definitions:
            definition = mock_definitions[0]  # Take the first/top definition
            
            embed = create_embed(
                title=f"Urban Dictionary: {word}",
                description=f"**Definition:**\n{definition['definition']}\n\n**Example:**\n{definition['example']}",
                color=CONFIG["embed_color"]
            )
            
            embed.add_field(name="Votes", value=f"👍 {definition['thumbs_up']} | 👎 {definition['thumbs_down']}")
            embed.set_footer(text="Note: This is a simulated response for demonstration purposes.")
            
            await message.edit(embed=embed)
        else:
            await message.edit(embed=error_embed(
                title="No Results",
                description=f"No definitions found for '{word}'."
            ))
    
    @commands.command(name="afk", help="Set yourself as AFK")
    async def afk(self, ctx, *, reason=None):
        """Set yourself as AFK with an optional reason"""
        # Get the AFK users data
        config = get_guild_config(ctx.guild.id)
        
        if "afk_users" not in config:
            config["afk_users"] = {}
        
        user_id = str(ctx.author.id)
        
        # Set the user as AFK
        config["afk_users"][user_id] = {
            "reason": reason or "AFK",
            "timestamp": datetime.datetime.now().timestamp()
        }
        
        update_guild_config(ctx.guild.id, config)
        
        # Confirm the AFK status
        await ctx.send(embed=success_embed(
            title="AFK Status Set",
            description=f"✅ {ctx.author.mention}, you are now marked as AFK.\nReason: {reason or 'AFK'}"
        ))
        
        # Try to update the nickname to indicate AFK status
        try:
            current_nick = ctx.author.display_name
            if not current_nick.startswith("[AFK] "):
                new_nick = f"[AFK] {current_nick}"
                if len(new_nick) <= 32:  # Discord nickname length limit
                    await ctx.author.edit(nick=new_nick)
        except discord.Forbidden:
            pass  # Ignore if the bot can't change the nickname
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for AFK users when messages are sent"""
        # Ignore messages from bots
        if message.author.bot or not message.guild:
            return
        
        config = get_guild_config(message.guild.id)
        afk_users = config.get("afk_users", {})
        
        # Check if the author was AFK
        user_id = str(message.author.id)
        if user_id in afk_users:
            # Remove the user from AFK list
            del afk_users[user_id]
            config["afk_users"] = afk_users
            update_guild_config(message.guild.id, config)
            
            # Send a welcome back message
            await message.channel.send(embed=info_embed(
                title="AFK Status Removed",
                description=f"Welcome back {message.author.mention}! Your AFK status has been removed."
            ))
            
            # Try to update the nickname back to normal
            try:
                current_nick = message.author.display_name
                if current_nick.startswith("[AFK] "):
                    new_nick = current_nick[6:]  # Remove the [AFK] prefix
                    await message.author.edit(nick=new_nick)
            except discord.Forbidden:
                pass  # Ignore if the bot can't change the nickname
        
        # Check if any mentioned users are AFK
        for mention in message.mentions:
            mention_id = str(mention.id)
            if mention_id in afk_users:
                afk_info = afk_users[mention_id]
                
                # Calculate time since AFK
                afk_time = datetime.datetime.fromtimestamp(afk_info["timestamp"])
                now = datetime.datetime.now()
                delta = now - afk_time
                
                # Format the time
                if delta.days > 0:
                    time_text = f"{delta.days}d {delta.seconds // 3600}h ago"
                elif delta.seconds // 3600 > 0:
                    time_text = f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m ago"
                else:
                    time_text = f"{delta.seconds // 60}m ago"
                
                # Inform that the user is AFK
                await message.channel.send(embed=info_embed(
                    title="User is AFK",
                    description=f"{mention.mention} is AFK: {afk_info['reason']} - {time_text}"
                ))
    
    @commands.command(name="fact", aliases=["randomfact"], help="Get a random fact")
    async def fact(self, ctx):
        """Display a random fact"""
        # List of random facts
        facts = [
            "A day on Venus is longer than a year on Venus.",
            "The Eiffel Tower can be 15 cm taller during the summer due to thermal expansion.",
            "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
            "A group of flamingos is called a 'flamboyance'.",
            "The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.",
            "The average person walks the equivalent of five times around the world in a lifetime.",
            "A giraffe's tongue is approximately 21 inches (53 cm) long and is typically blue-black in color.",
            "The heart of a shrimp is located in its head.",
            "Octopuses have three hearts, nine brains, and blue blood.",
            "A group of unicorns is called a blessing.",
            "Cows have best friends and can become stressed when they are separated.",
            "The fingerprints of koalas are so similar to humans that they have on occasion been confused at crime scenes.",
            "There are more possible iterations of a game of chess than there are atoms in the known universe.",
            "The total weight of all the ants on Earth is approximately the same as the total weight of all the humans on Earth.",
            "A day on Mercury lasts around 176 Earth days."
        ]
        
        fact = random.choice(facts)
        
        embed = info_embed(
            title="🧠 Random Fact",
            description=fact
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="joke", help="Get a random joke")
    async def joke(self, ctx):
        """Display a random joke"""
        # List of random jokes
        jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "I told my wife she was drawing her eyebrows too high. She looked surprised.",
            "What do you call a fake noodle? An impasta!",
            "Why did the scarecrow win an award? Because he was outstanding in his field!",
            "I'm reading a book on anti-gravity. It's impossible to put down!",
            "I used to be a baker, but I couldn't make enough dough.",
            "What do you call a dinosaur with an extensive vocabulary? A thesaurus.",
            "Why don't skeletons fight each other? They don't have the guts.",
            "Did you hear about the mathematician who's afraid of negative numbers? He'll stop at nothing to avoid them.",
            "Why was the math book sad? It had too many problems.",
            "What's the best thing about Switzerland? I don't know, but the flag is a big plus.",
            "Why did the bicycle fall over? Because it was two tired!",
            "How do you organize a space party? You planet!",
            "What's orange and sounds like a parrot? A carrot.",
            "Why don't eggs tell jokes? They'd crack each other up."
        ]
        
        joke = random.choice(jokes)
        
        embed = info_embed(
            title="😂 Random Joke",
            description=joke
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="quote", help="Display a random inspirational quote")
    async def quote(self, ctx):
        """Display a random inspirational quote"""
        # List of inspirational quotes
        quotes = [
            ("The only way to do great work is to love what you do.", "Steve Jobs"),
            ("Life is what happens when you're busy making other plans.", "John Lennon"),
            ("In three words I can sum up everything I've learned about life: it goes on.", "Robert Frost"),
            ("The future belongs to those who believe in the beauty of their dreams.", "Eleanor Roosevelt"),
            ("The purpose of our lives is to be happy.", "Dalai Lama"),
            ("You only live once, but if you do it right, once is enough.", "Mae West"),
            ("The best way to predict the future is to create it.", "Abraham Lincoln"),
            ("Success is not final, failure is not fatal: It is the courage to continue that counts.", "Winston Churchill"),
            ("The only limit to our realization of tomorrow will be our doubts of today.", "Franklin D. Roosevelt"),
            ("The greatest glory in living lies not in never falling, but in rising every time we fall.", "Nelson Mandela"),
            ("It does not matter how slowly you go as long as you do not stop.", "Confucius"),
            ("Everything you've ever wanted is on the other side of fear.", "George Addair"),
            ("Believe you can and you're halfway there.", "Theodore Roosevelt"),
            ("Your time is limited, don't waste it living someone else's life.", "Steve Jobs"),
            ("The only impossible journey is the one you never begin.", "Tony Robbins")
        ]
        
        quote, author = random.choice(quotes)
        
        embed = info_embed(
            title="💭 Inspirational Quote",
            description=f"\"{quote}\"\n\n— *{author}*"
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name="enlarge", aliases=["bigemoji"], help="Enlarge a custom emoji")
    async def enlarge(self, ctx, emoji: str = None):
        """Enlarge a custom emoji"""
        if emoji is None:
            await ctx.send(embed=error_embed(
                title="Missing Emoji",
                description="Please provide a custom emoji to enlarge!"
            ))
            return
        
        # Check if it's a custom emoji
        import re
        custom_emoji = re.match(r'<a?:([a-zA-Z0-9_]+):([0-9]+)>', emoji)
        
        if not custom_emoji:
            await ctx.send(embed=error_embed(
                title="Invalid Emoji",
                description="That's not a valid custom emoji. Please use a custom emoji from a server."
            ))
            return
        
        # Extract emoji details
        emoji_name = custom_emoji.group(1)
        emoji_id = custom_emoji.group(2)
        extension = "gif" if emoji.startswith("<a:") else "png"
        
        # Create the emoji URL
        emoji_url = f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"
        
        # Create an embed with the enlarged emoji
        embed = create_embed(
            title=f"Enlarged Emoji: {emoji_name}",
            color=CONFIG["embed_color"]
        )
        
        embed.set_image(url=emoji_url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Others(bot))
