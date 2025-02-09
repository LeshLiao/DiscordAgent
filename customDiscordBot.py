import discord
from discord.ext import commands
import aiohttp
import asyncio
from dotenv import load_dotenv
from PIL import Image
import os
import pyautogui
import time

from utility import click_discord_and_imagine, download_image

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

directory = os.getcwd()
print(directory)

# Define reconnect settings
MAX_RETRIES = 3
RETRY_DELAY = 3

class CustomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="*", intents=intents)
        self.reconnect_attempts = 0
        self.session = None

    async def cleanup(self):
        """Cleanup method to properly close connections"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
            if not self.is_closed():
                await self.close()
        except Exception as e:
            print(f"Error during cleanup: {e}")

    async def on_ready(self):
        print(f"Bot connected as {self.user.name}")
        print(f"Bot ID: {self.user.id}")
        self.reconnect_attempts = 0

    async def on_connect(self):
        print("Bot successfully connected to Discord")

    async def on_disconnect(self):
        print("Bot disconnected from Discord")
        self.reconnect_attempts += 1
        if self.reconnect_attempts <= MAX_RETRIES:
            print(f"Attempting to reconnect... (Attempt {self.reconnect_attempts}/{MAX_RETRIES})")
            await asyncio.sleep(RETRY_DELAY)
        else:
            print("Max reconnection attempts reached. Please check your connection and restart the bot.")

    async def on_resumed(self):
        print("Bot resumed connection")
        self.reconnect_attempts = 0

    async def on_error(self, event_method, *args, **kwargs):
        print(f"Error in {event_method}:")
        import traceback
        traceback.print_exc()

client = CustomBot()

async def handle_upload(message, image_url):
    try:
        if image_url:
            await message.channel.send(f"Processing prompt: {image_url}")
            click_discord_and_imagine(f"{image_url} HDR Coastal Landscape --ar 9:16 --seed 10")
    except Exception as e:
        print(f"Error in handle_upload: {e}")

async def handle_upscale(message, image_url, file_name):
    try:
        if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            if "- Upscaled" in message.content:
                await download_image(image_url, file_name, "upscaled")
            elif "- Image #" in message.content:
                await download_image(image_url, file_name, "thumbnail")
        else:
            print(f"Error: unknown image format!")

    except Exception as e:
        print(f"Error in handle_upscale: {e}")

async def handle_publish():
    pass

@client.event
async def on_message(message):
    try:
        channel_name = message.channel.name
        print(f"\n===== message (channel: {channel_name}) =====\n")
        print(message)
        print("\nmessage.content=")
        print(message.content)
        print("\nmessage.attachments=")
        print(message.attachments)
        print("===============================")

        # filter user
        # if message.author == client.user:
        #     return

        image_url = ""
        file_name = ""
        for attachment in message.attachments:
            image_url = attachment.url
            file_name= attachment.filename
            break

        if channel_name == "upload":
            await handle_upload(message, image_url)
        elif channel_name == "upscale":
            await handle_upscale(message, image_url, file_name)
        elif channel_name == "publish":
            await handle_publish()

    except Exception as e:
        print(f"Error in on_message: {e}")
        await message.channel.send("An error occurred while processing the message.")

async def main():
    try:
        async with aiohttp.ClientSession() as session:
            client.session = session
            await client.start(discord_token)
    except discord.errors.ConnectionClosed:
        print("Connection closed. Attempting to reconnect...")
    except discord.errors.LoginFailure:
        print("Login failed. Please check your token.")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        await client.cleanup()

async def shutdown():
    """Cleanup tasks tied to the service's shutdown."""
    print("Received exit signal, shutting down...")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    print(f"Cancelling {len(tasks)} outstanding tasks...")
    for task in tasks:
        task.cancel()

    print("Waiting for task cancellation...")
    await asyncio.gather(*tasks, return_exceptions=True)

    await client.cleanup()
    print("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received")
        asyncio.run(shutdown())
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("Bot has been shut down.")