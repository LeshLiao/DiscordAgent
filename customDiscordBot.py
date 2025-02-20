import discord
from discord.ext import commands
import aiohttp
import asyncio
from dotenv import load_dotenv
from PIL import Image
import os
import pyautogui
import time
from open_ai import ImageAnalyzer

from utility import click_discord_and_imagine, download_image, upload_to_firebase_3, initialize_firebase, safe_delete, click_somewhere
from api.wallpaper_api import WallpaperAPI, ImageItem, DownloadItem
from api.publish_manager import PublishManager, PublishConfig  # Add this line
from image_url_detection import is_image_url

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

        self.thumbnail_path = ""
        self.upscaled_path = ""
        self.thumbnail_url = ""
        self.upscaled_url = ""
        initialize_firebase()

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

async def handle_upload(message, attach_image_url):
    prompt_string = "mobile wallpaper --ar 9:16 --iw 3"
    try:
        if attach_image_url:
            await message.channel.send(f"Processing prompt: {attach_image_url}")
            click_discord_and_imagine(f"{attach_image_url} " + prompt_string)
        else:
            print("message=============================")
            print(message.content)
            is_image, content_type = is_image_url(message.content)
            print(is_image)
            if is_image:
                image_url = message.content
                await message.channel.send(f"Processing prompt: {image_url}")
                click_discord_and_imagine(f"{image_url} " + prompt_string)

    except Exception as e:
        print(f"Error in handle_upload: {e}")

async def handle_upscale(message, attach_image_url, file_name):
    try:
        if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            if "- Upscaled" in message.content:
                client.upscaled_path = await download_image(attach_image_url, file_name, "upscaled")
                if client.upscaled_path:
                    firebase_url = upload_to_firebase_3(client.upscaled_path, "upscaled")
                    if firebase_url:
                        client.upscaled_url = firebase_url
                        await message.channel.send(f"Upscaled added to firebase successfully!")

                        # Initialize the image analyzer
                        analyzer = ImageAnalyzer()
                        try:
                            # Analyze the thumbnail image
                            title, tags = analyzer.analyze_image(client.thumbnail_path)
                            await publish_item(message, title, tags)
                            safe_delete(client.upscaled_path)
                            safe_delete(client.thumbnail_path)
                        except Exception as e:
                            await message.channel.send(f"Error analyzing image: {str(e)}")
                    else:
                        await message.channel.send("Failed to upload upscaled image to Firebase")

            elif "- Image #" in message.content:
                client.thumbnail_path = await download_image(attach_image_url, file_name, "thumbnail")
                if client.thumbnail_path:
                    firebase_url = upload_to_firebase_3(client.thumbnail_path, "thumbnail")
                    if firebase_url:
                        client.thumbnail_url = firebase_url
                        await message.channel.send(f"Thumbnail added to firebase successfully!")
                        print("click upscale button...")
                        click_somewhere("img/upscale.png",interval_seconds = 2, repeat = 1, retry= 3, retry_interval = 2)
                    else:
                        await message.channel.send("Failed to upload thumbnail to Firebase")
            elif "- <@" in message.content and "discordapp" in attach_image_url:
                print("click U4 option...")
                click_somewhere("img/u4.png",interval_seconds = 2, repeat = 1, retry= 3, retry_interval = 2)

        else:
            print(f"Message:")
            print(message.content)

    except Exception as e:
        print(f"Error in handle_upscale: {e}")

async def publish_item(message, title, tags):
    try:
        # Create a custom configuration
        config = PublishConfig(
            default_price=3.0,
            default_stars=4,
            id_prefix="20"
        )

        # Initialize the manager
        publisher = PublishManager(config)

        # Get the URLs from the bot's state
        if not client.thumbnail_url or not client.upscaled_url:
            await message.channel.send("Error: Missing thumbnail or upscaled image URLs")
            return

        # Publish the item with actual URLs from the bot's state
        await publisher.publish(
            message=message,
            thumbnail_url=client.thumbnail_url,
            upscaled_url=client.upscaled_url,
            title=title,  # You might want to make this configurable
            tags=tags,
            resolution="1632x2912"  # This matches your original aspect ratio of 9:16
        )

        # Clear the URLs after successful publishing
        client.thumbnail_url = ""
        client.upscaled_url = ""


    except Exception as e:
        print(f"Error in publish_item: {e}")
        await message.channel.send(f"Error during publication: {str(e)}")

@client.event
async def on_message(message):
    try:
        channel_name = message.channel.name
        print(f"\n===== message (channel: {channel_name}) =====")
        #print(" - message:")
        #print(message)
        print(" - message.content:")
        print(message.content)
        print(" - message.attachments:")
        print(message.attachments)
        print("\n")

        # filter user
        # if message.author == client.user:
        #     return

        attach_image_url = ""
        file_name = ""
        for attachment in message.attachments:
            attach_image_url = attachment.url
            file_name= attachment.filename
            break

        if channel_name == "upload":
            await handle_upload(message, attach_image_url)
        elif channel_name == "upscale":
            await handle_upscale(message, attach_image_url, file_name)
        # elif channel_name == "publish":
        #     await handle_publish(message)

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