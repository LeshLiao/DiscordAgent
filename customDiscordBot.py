import discord
from discord.ext import commands
import aiohttp
import asyncio
from dotenv import load_dotenv
from PIL import Image
import os
import pyautogui
import time
from datetime import datetime
import argparse
from open_ai import ImageAnalyzer

from utility import type_imagine, download_image, upload_to_firebase_3, initialize_firebase, safe_delete, click_somewhere, is_macos, resize_all_and_upload_to_firebase
from api.wallpaper_api import WallpaperAPI, ImageItem, DownloadItem
from api.publish_manager import PublishManager, PublishConfig
from image_url_detection import is_image_url
from sendMessage import send_message
from pexels_resource import add_one

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = "1338067894780559410"  # channel ID (#upload)

directory = os.getcwd()
print(directory)

# Define reconnect settings
MAX_RETRIES = 3
RETRY_DELAY = 3
POLLING_INTERVAL = 60  # Check waiting list every 60 seconds

class CustomBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="*", intents=intents)
        self.reconnect_attempts = 0
        self.session = None

        self.thumbnail_path = ""
        self.upscaled_path = ""
        self.thumbnail_url = ""
        self.thumbnail_blob = ""
        self.upscaled_url = ""
        self.upscaled_blob = ""
        self.waiting_id = ""
        self.imageList_data = ""
        self.auto_polling_mode = False
        self.task_in_progress = False  # CRITICAL: Prevents multiple tasks running simultaneously
        self.polling_task = None  # Store the polling task reference
        print("CustomBot init")
        initialize_firebase()

    async def cleanup(self):
        """Cleanup method to properly close connections"""
        try:
            # Cancel polling task if running
            if self.polling_task and not self.polling_task.done():
                self.polling_task.cancel()
                try:
                    await self.polling_task
                except asyncio.CancelledError:
                    print("Polling task cancelled")

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

        if client.auto_polling_mode:
            # Start the polling task
            if not self.polling_task or self.polling_task.done():
                self.polling_task = asyncio.create_task(self.start_polling_loop())
                print("Started automatic polling mode")

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

    async def start_polling_loop(self):
        """Background task that continuously polls the waiting list"""
        print("=== Polling loop started ===")
        await self.wait_until_ready()  # Wait for bot to be ready

        while not self.is_closed():
            try:
                await polling_waiting_list()
                # Wait before next poll
                await asyncio.sleep(POLLING_INTERVAL)
            except asyncio.CancelledError:
                print("Polling loop cancelled")
                break
            except Exception as e:
                print(f"Error in polling loop: {e}")
                # Wait a bit before retrying after error
                await asyncio.sleep(POLLING_INTERVAL)

client = CustomBot()

async def handle_upload(message, attach_image_url):
    # click text box, and input prompt with image

    prompt_string = "mobile wallpaper --ar 9:16 --iw 3"
    try:
        if attach_image_url:
            print(f"Processing prompt: {attach_image_url}")
            if is_macos():
                click_somewhere("img/mac/message_upscale_textbox.png",interval_seconds = 2, repeat = 1, retry= 3, retry_interval = 2)
            else:
                click_somewhere("img/linux/message_upscale_textbox.png",interval_seconds = 2, repeat = 1, retry= 3, retry_interval = 2)
            type_imagine(f"{attach_image_url} " + prompt_string)
        else:
            is_image, content_type = is_image_url(message.content)
            if is_image:
                image_url = message.content
                print(f"Processing prompt: {image_url}")
                if is_macos():
                    click_somewhere("img/mac/message_upscale_textbox.png",interval_seconds = 2, repeat = 1, retry= 3, retry_interval = 2)
                else:
                    click_somewhere("img/linux/message_upscale_textbox.png",interval_seconds = 2, repeat = 1, retry= 3, retry_interval = 2)
                type_imagine(f"{image_url} " + prompt_string)

    except Exception as e:
        print(f"Error in handle_upload: {e}")

async def handle_to_waiting_list(message, attach_image_url):
    note = ""
    try:
        temp_url = ""
        result = False
        #if message.content in "Discord Message:":
        #    print("pass")
        #    pass
        if attach_image_url:
            temp_url = attach_image_url
            result = add_one("discord", note, temp_url)
        else:
            is_image, content_type = is_image_url(message.content)
            if is_image:
                image_url = message.content
                temp_url = image_url
                result = add_one("discord", note, temp_url)
        if result:
            await message.channel.send(f"Discord Message: Added url successfully: {temp_url}")

    except Exception as e:
        print(f"Error in handle_upload: {e}")

async def handle_bot(message, attach_image_url, file_name):
    try:
        if file_name.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            if "- Upscaled" in message.content:
                client.upscaled_path = await download_image(attach_image_url)
                if client.upscaled_path:
                    firebase_url, blob_name = upload_to_firebase_3(client.upscaled_path, "upscaled")
                    if firebase_url:
                        client.upscaled_url = firebase_url
                        client.upscaled_blob = blob_name
                        await message.channel.send(f"Upscaled added to firebase successfully!")

                        # Initialize the image analyzer
                        analyzer = ImageAnalyzer()
                        try:
                            # Analyze the thumbnail image
                            title, tags = analyzer.analyze_image(client.thumbnail_path)
                            new_itemId = await publish_item(message, title, tags)
                            safe_delete(client.upscaled_path)
                            safe_delete(client.thumbnail_path)
                            if new_itemId != "":
                                api_client = WallpaperAPI()
                                api_client.complete_waiting_list_item(client.waiting_id, new_itemId, client.thumbnail_url)

                                # Clear the URLs after successful publishing
                                client.thumbnail_url = ""
                                client.thumbnail_blob = ""
                                client.upscaled_url = ""
                                client.upscaled_blob = ""
                                client.waiting_id = ""
                                client.imageList_data = ""

                                # Mark task as completed
                                client.task_in_progress = False
                                print("✓ Task completed, ready for next item")

                                # Immediately check for next item
                                await polling_waiting_list()
                            else:
                                print("Publish item failed! Marking task as not in progress")
                                client.task_in_progress = False

                        except Exception as e:
                            await message.channel.send(f"Error analyzing image: {str(e)}")
                            client.task_in_progress = False
                    else:
                        await message.channel.send("Failed to upload upscaled image to Firebase")
                        client.task_in_progress = False

            elif "- Image #" in message.content:
                client.thumbnail_path = await download_image(attach_image_url)
                if client.thumbnail_path:
                    client.imageList_data = await resize_all_and_upload_to_firebase(client.thumbnail_path, False)
                    if (client.imageList_data):
                        print("Downsize all type and added to firebase successfully!")
                    firebase_url, blob_name = upload_to_firebase_3(client.thumbnail_path, "thumbnail")
                    if firebase_url:
                        client.thumbnail_url = firebase_url
                        client.thumbnail_blob = blob_name
                        # await message.channel.send(f"Thumbnail added to firebase successfully!")
                        print("Thumbnail added to firebase successfully!, click upscale button...")

                        time.sleep(6)
                        if is_macos():
                            click_somewhere("img/mac/upscale_subtle.png",interval_seconds = 0.5, repeat = 2, retry= 30, retry_interval = 5)
                        else:
                            click_somewhere("img/linux/upscale_subtle.png",interval_seconds = 0.5, repeat = 2, retry= 30, retry_interval = 5)
                    else:
                        await message.channel.send("Failed to upload thumbnail to Firebase")
            elif "- <@" in message.content and "discordapp" in attach_image_url:
                print("click U4 option...")

                time.sleep(3)
                if is_macos():
                    # Sometimes, Discord displays a 'poop' image when an image fails to load
                    # therefore, it's necessary to retry.
                    click_somewhere("img/mac/u4_extend.png",interval_seconds = 0.5, repeat = 2, retry = 30, retry_interval = 5)
                else:
                    click_somewhere("img/linux/u4_extend.png",interval_seconds = 0.5, repeat = 2, retry = 30, retry_interval = 5)

        else:
            print(f"Message:")
            print(message.content)

    except Exception as e:
        print(f"Error in handle_bot: {e}")
        client.task_in_progress = False  # Reset flag on error

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
            return ""

        # Publish the item with actual URLs from the bot's state
        new_itemId = await publisher.publish(
            message=message,
            thumbnail_url=client.thumbnail_url,
            thumbnail_blob=client.thumbnail_blob,
            upscaled_url=client.upscaled_url,
            upscaled_blob=client.upscaled_blob,
            title=title,
            tags=tags,
            resolution="1632x2912",
            imagesList = client.imageList_data
        )
        return new_itemId

    except Exception as e:
        print(f"Error in publish_item: {e}")
        await message.channel.send(f"Error during publication: {str(e)}")
        return ""

@client.event
async def on_message(message):
    try:
        channel_name = message.channel.name
        print(f"\n===== message (channel: {channel_name}) =====")
        print(" - message.content:")
        print(message.content)

        attach_image_url = ""
        file_name = ""
        for attachment in message.attachments:
            attach_image_url = attachment.url
            file_name= attachment.filename
            break

        if channel_name == "upload":            # message from smart phone
            await handle_upload(message, attach_image_url)
        elif channel_name == "bot":         # message from Discord Bot
            await handle_bot(message, attach_image_url, file_name)
        elif channel_name == "to_waiting_list": # message from smart phone
            await handle_to_waiting_list(message, attach_image_url)

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

async def get_next_url_from_waiting_list():
    """Get the next URL from waiting list and send it to Discord channel"""
    api_client = WallpaperAPI()
    response = api_client.get_one_from_waiting_list(assign="midjourney")

    # Check if the request was successful
    if response["success"]:
        # Access the extracted data
        _id = response["data"]["_id"]
        url = response["data"]["url"]
        client.waiting_id = _id

        print(f"✓ GET one item from waiting list!")
        print(f"  _id: {_id}")
        print(f"  url: {url}")

        # Get the channel and send the message directly
        try:
            channel = client.get_channel(int(CHANNEL_ID))
            if channel:
                await channel.send(url)
                print(f"✓ URL sent to #upload channel")
            else:
                print(f"✗ Error: Channel with ID {CHANNEL_ID} not found")
                client.task_in_progress = False
        except Exception as e:
            print(f"✗ Error sending message: {e}")
            client.task_in_progress = False
    else:
        # Handle error case
        print(f"✗ Error: {response['message']}")
        client.task_in_progress = False
        if "No waiting items found." in response.get('message', ''):
            print("\n========== No waiting items found. ==========\n")

async def polling_waiting_list():
    """
    Check the waiting list count and process the next item if available.
    Includes protection against running multiple tasks simultaneously.
    """
    # CRITICAL: Check if a task is already in progress
    if client.task_in_progress:
        print("⚠ Task in progress...")
        return

    # Get current UTC time and local time
    utc_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    local_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== Polling waiting list ===")
    print(f"UTC:   {utc_time}")
    print(f"Local: {local_time}")

    api_client = WallpaperAPI()
    count = api_client.get_count_from_waiting_list()

    print(f"Waiting list count: {count}")

    if count > 0:
        # Set flag to prevent concurrent tasks
        client.task_in_progress = True
        print("✓ Items available, starting task...")

        try:
            await get_next_url_from_waiting_list()
        except Exception as e:
            print(f"✗ Error in get_next_url_from_waiting_list: {e}")
            client.task_in_progress = False
    else:
        print("○ No items in waiting list")

if __name__ == "__main__":
    # Hint
    print("=== Please Check you python venv first ===")
    print("COMMAND: source venv/bin/activate")
    print("COMMAND: deactivate")
    print("COMMAND: python3 customDiscordBot.py -auto")

    # Set up argument parser
    parser = argparse.ArgumentParser(description='Discord Bot Runner')
    parser.add_argument('-auto', '--automatic', action='store_true',
                        help='Run the bot in automatic mode')
    args = parser.parse_args()

    if args.automatic:
        print("🤖 Auto mode enabled!")
        client.auto_polling_mode = True
    else:
        print("👤 Normal mode!")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received")
        asyncio.run(shutdown())
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("Bot has been shut down.")