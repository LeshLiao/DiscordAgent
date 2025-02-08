import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv
from PIL import Image
import os

import pyautogui
import time

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

client = commands.Bot(command_prefix="*", intents=discord.Intents.all())

directory = os.getcwd()
print(directory)


my_prompt = "a man is programming in the garden."

def click_discord_and_type():
    # Give you time to switch to the right window
    time.sleep(2)

    # Click on Discord message box  (x=1923, y=935
    pyautogui.click(x=1923, y=935)  # You'll need to adjust these coordinates

    # Type the command
    pyautogui.write("/imagine")
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.write("a man is programming in the garden.")
    time.sleep(1)
    pyautogui.press('enter')


# Add the imagine command
@client.command()
async def imagine(ctx):
    click_discord_and_type()
    await ctx.send("Command triggered!")

    """Format and send the prompt in a way that's easy to copy-paste into Midjourney"""
    #formatted_prompt = f"/imagine prompt: {my_prompt}"
    #await ctx.send("a man is programming in the garden.")
    #await ctx.send(formatted_prompt)


def split_image(image_file):
    with Image.open(image_file) as im:
        # Get the width and height of the original image
        width, height = im.size
        # Calculate the middle points along the horizontal and vertical axes
        mid_x = width // 2
        mid_y = height // 2
        # Split the image into four equal parts
        top_left = im.crop((0, 0, mid_x, mid_y))
        top_right = im.crop((mid_x, 0, width, mid_y))
        bottom_left = im.crop((0, mid_y, mid_x, height))
        bottom_right = im.crop((mid_x, mid_y, width, height))

        return top_left, top_right, bottom_left, bottom_right

async def download_image(url, filename):
    response = requests.get(url)
    if response.status_code == 200:

        # Define the input and output folder paths
        input_folder = "input"
        output_folder = "output"

        # Check if the output folder exists, and create it if necessary
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        # Check if the input folder exists, and create it if necessary
        if not os.path.exists(input_folder):
            os.makedirs(input_folder)

        with open(f"{directory}/{input_folder}/{filename}", "wb") as f:
            f.write(response.content)
        print(f"Image downloaded: {filename}")

        input_file = os.path.join(input_folder, filename)

        if "UPSCALED_" not in filename:
            file_prefix = os.path.splitext(filename)[0]
            # Split the image
            top_left, top_right, bottom_left, bottom_right = split_image(input_file)
            # Save the output images with dynamic names in the output folder
            top_left.save(os.path.join(output_folder, file_prefix + "_top_left.jpg"))
            top_right.save(os.path.join(output_folder, file_prefix + "_top_right.jpg"))
            bottom_left.save(os.path.join(output_folder, file_prefix + "_bottom_left.jpg"))
            bottom_right.save(os.path.join(output_folder, file_prefix + "_bottom_right.jpg"))

        else:
            os.rename(f"{directory}/{input_folder}/{filename}", f"{directory}/{output_folder}/{filename}")
        # Delete the input file
        os.remove(f"{directory}/{input_folder}/{filename}")

@client.event
async def on_ready():
    print("Bot connected")

@client.event
async def on_message(message):
    # Process commands first
    await client.process_commands(message)

    # Then handle attachments
    for attachment in message.attachments:
        if "Upscaled by" in message.content:
            file_prefix = 'UPSCALED_'
        else:
            file_prefix = ''
        if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            await download_image(attachment.url, f"{file_prefix}{attachment.filename}")

client.run(discord_token)