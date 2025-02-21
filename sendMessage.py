"""
Discord Message Sender Module
This module provides functionality to send messages to Discord channels using a bot token.
"""

import discord
import asyncio
import os
from dotenv import load_dotenv
from typing import Optional, Union

class DiscordMessenger:
    def __init__(self, token: Optional[str] = None):
        """
        Initialize the Discord messenger.

        Args:
            token (Optional[str]): Discord bot token. If not provided, will try to load from environment variable.
        """
        self.token = token or os.getenv('DISCORD_TOKEN')
        if not self.token:
            raise ValueError("Discord token not provided and DISCORD_TOKEN not found in environment")

        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)

    async def send_message(self, channel_id: Union[int, str], message: str) -> bool:
        """
        Send a message to a specific Discord channel.

        Args:
            channel_id (Union[int, str]): The ID of the channel to send the message to
            message (str): The message content to send

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        try:
            # Convert channel_id to int if it's a string
            channel_id = int(channel_id)

            async with self.client as client:
                await client.login(self.token)

                # Get the channel
                channel = client.get_channel(channel_id)
                if not channel:
                    channel = await client.fetch_channel(channel_id)

                if channel:
                    await channel.send(message)
                    return True
                else:
                    print(f"Could not find channel with ID: {channel_id}")
                    return False

        except Exception as e:
            print(f"Error sending message: {e}")
            return False

def send_message(token: str, channel_id: Union[int, str], message: str) -> bool:
    """
    Synchronous wrapper for sending a Discord message.

    Args:
        token (str): Discord bot token
        channel_id (Union[int, str]): Channel ID to send the message to
        message (str): Message content to send

    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    messenger = DiscordMessenger(token)
    return asyncio.run(messenger.send_message(channel_id, message))

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Get token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: DISCORD_TOKEN not found in environment variables")
        exit(1)

    # Channel ID and message
    CHANNEL_ID = "1338067894780559410"  # Replace with your channel ID
    MESSAGE = "Hello from Discord Messenger!"

    # Send the message
    success = send_message(token, CHANNEL_ID, MESSAGE)
    print(f"Message sent: {success}")