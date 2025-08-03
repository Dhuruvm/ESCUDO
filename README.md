# ESCUDO Discord Bot

A comprehensive Discord moderation and utility bot built with py-cord featuring antinuke protection, moderation tools, and server management capabilities.

## Features

### Main Categories
- **🔰 Antinuke**: Protect your server from raids, mass bans, and other malicious activities
- **🔨 Moderation**: Full suite of moderation commands (ban, kick, mute, warn, etc.)
- **🛠️ Utils**: Utility commands for server management
- **🔊 Voice**: Voice channel management and controls
- **😈 Other**: Fun and miscellaneous commands
- **➕ Join To Create**: Dynamic voice channel creation system
- **👥 SelfRoles**: Self-assignable role system with reaction roles

## Getting Started

1. **Invite the bot** to your server using the invite link
2. **Set up permissions**: Make sure the bot has proper permissions to function
3. **Configure settings**: Use the setup commands to customize the bot for your server

## Command Prefix

The default command prefix is `,` (e.g., `,help`). You can also mention the bot as a prefix.

## Usage Examples

### Antinuke Protection
```
,antinuke on  # Enable antinuke protection
,whitelist @user  # Whitelist a user from antinuke system
```

### Moderation
```
,ban @user Breaking rules  # Ban a user with reason
,mute @user 1h Spamming  # Mute a user for 1 hour
,warn @user Please follow the rules  # Warn a user
```

### Join To Create
```
,setup #voice-category  # Set up the Join to Create system
,limit 5  # Set user limit for your voice channel
```

### Self Roles
```
,addselfrole @role  # Add a role to self-assignable roles
,reactionrole #roles-channel  # Create a reaction role message
```

## Support and Updates

- Use `,help` to see all available commands
- Use `,help [command]` to get detailed information about a specific command

## Installation for Self-Hosting

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your Discord bot token as environment variable DISCORD_TOKEN
4. Optionally configure owner IDs in the config.py file
5. Run the bot: `python main.py`

## Project Structure

- **main.py**: The main entry point containing the Discord bot implementation
- **cogs/**: Directory containing all bot commands organized by category
- **data/**: JSON files for persistent data storage
- **utils/**: Helper modules and utility functions

## License

This project is licensed under the MIT License - see the LICENSE file for details.