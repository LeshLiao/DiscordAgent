import time
import pyautogui
import aiohttp
import os
from PIL import Image

def click_discord_and_imagine(prompt):
    time.sleep(2)
    # Click on Discord message box
    pyautogui.click(x=1940, y=933)
    # Type the command
    pyautogui.write("/imagine")
    time.sleep(1)
    pyautogui.press('enter')
    time.sleep(1)
    pyautogui.write(prompt)
    time.sleep(1)
    pyautogui.press('enter')

async def download_image(url, filename, prefix):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    # Define folders
                    input_folder = "input"
                    output_folder = "output"

                    # Create directories if they don't exist
                    os.makedirs(output_folder, exist_ok=True)
                    os.makedirs(input_folder, exist_ok=True)

                    # Download and save file
                    input_path = os.path.join(input_folder, filename)
                    with open(input_path, "wb") as f:
                        f.write(await response.read())

                    # Convert PNG to JPG if it's a PNG file
                    if filename.lower().endswith('.png'):
                        with Image.open(input_path) as im:
                            # Convert to RGB mode if necessary
                            if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):
                                bg = Image.new('RGB', im.size, (255, 255, 255))
                                if im.mode == 'RGBA':
                                    bg.paste(im, mask=im.split()[3])
                                else:
                                    bg.paste(im)
                                im = bg

                            # Get image resolution
                            width, height = im.size
                            print(f"width={width} x height={height}")
                            resolution_name = f"{prefix}_{width}x{height}_"

                            # Change extension to jpg
                            jpg_filename = os.path.splitext(filename)[0] + '.jpg'
                            output_path = os.path.join(output_folder, f"{resolution_name}{jpg_filename}")

                            # Save as JPG
                            im.save(output_path, 'JPEG', quality=95)

                            # Remove the original PNG file
                            os.remove(input_path)

                            print(f"Image converted and saved: {resolution_name}{jpg_filename}")
                    else:
                        # Handle non-PNG files
                        with Image.open(input_path) as im:
                            width, height = im.size
                            print(f"width={width} x height={height}")
                            resolution_name = f"{prefix}_{width}x{height}_"

                            output_path = os.path.join(output_folder, f"{resolution_name}{filename}")
                            os.rename(input_path, output_path)
                            print(f"Image saved: {resolution_name}{filename}")
                else:
                    print(f"Failed to download image. Status code: {response.status}")

    except aiohttp.ClientError as e:
        print(f"Network error while downloading image: {e}")
    except Exception as e:
        print(f"Unexpected error in download_image: {e}")