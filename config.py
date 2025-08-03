import os

# Default owner ID - this should be replaced with your own Discord user ID
DEFAULT_OWNER_ID = 1234567890  # Replace this with your Discord user ID

CONFIG = {
    'prefix': ',',
    'owner_ids': [int(id) for id in os.getenv("OWNER_IDS", str(DEFAULT_OWNER_ID)).split(",") if id],
    'extra_owners': {},
    'antinuke': {
        'enabled': True,
        'bypass_enabled': False,
        'whitelisted_users': {},
        'nightmode': {},
        'admin_roles': {},
        'mod_roles': {}
    },
    'developer_commands': [
        'extraowner', 'mainrole', 'whitelistreset', 'eval', 'reload', 'shutdown'
    ],
    'embed_color': 0xE74C3C,  # Red color similar to the screenshot
    'success_color': 0x2ECC71,  # Green color for success messages
    'error_color': 0xE74C3C,   # Red color for error messages
    'warning_color': 0xF39C12,  # Orange color for warning messages
    'info_color': 0x3498DB,    # Blue color for info messages
}
