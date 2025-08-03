#!/usr/bin/env python3
"""
This file is a dedicated entry point for the Discord bot,
designed to prevent port conflicts with the Flask app.
It directly executes the main.py script where the bot code is located.
"""

import os
import sys
import subprocess

if __name__ == "__main__":
    print("Starting Discord bot in dedicated mode...")
    
    # Set the environment variable for child processes
    os.environ["RUN_DISCORD_ONLY"] = "1"
    
    # Run main.py directly as a subprocess
    subprocess.run(["python", "main.py"])