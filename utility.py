import time
import pyautogui
import aiohttp
import os
from PIL import Image
import firebase_admin
from firebase_admin import credentials, storage
from datetime import datetime
from dotenv import load_dotenv
import uuid
import pytz

# Load environment variables
load_dotenv()

def get_utc_time():
    """Get current UTC time in the specified format"""
    utc_now = datetime.now(pytz.UTC)
    return utc_now.strftime('%Y%m%d_%H%M%S_')

def initialize_firebase():
    """Initialize Firebase with the provided configuration"""
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": "palettex-37930",
        "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
        "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
        "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
        "client_id": os.getenv('FIREBASE_CLIENT_ID'),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_CERT_URL')
    })

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {
            'storageBucket': 'palettex-37930.appspot.com'
        })

def upload_to_firebase(local_file_path, firebase_folder):
    """
    Uploads an image to Firebase Storage and returns the public URL

    Args:
        local_file_path (str): The local path to the image file
        firebase_folder (str): The folder name in Firebase Storage (e.g., 'thumbnail', 'upscaled')

    Returns:
        str: The public URL of the uploaded file
    """
    try:
        # Get bucket
        bucket = storage.bucket()

        # Get the base filename from the local path
        filename = os.path.basename(local_file_path)
        file_ext = os.path.splitext(local_file_path)[1]

        # Create unique filename with UTC timestamp and UUID
        time_string = get_utc_time()  # Format: 20250213_101530_
        firebase_filename = f"{time_string}{firebase_folder}_{str(uuid.uuid4())}{file_ext}"

        # Create the full path in Firebase Storage
        destination_blob_name = f'images/{firebase_folder}/{firebase_filename}'

        # Upload the file
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_file_path)

        # Make the file publicly accessible
        blob.make_public()

        # Get the public URL
        public_url = blob.public_url

        print(f"File uploaded successfully to Firebase Storage: {destination_blob_name}")

        # Clean up local file after successful upload
        # try:
        #     os.remove(local_file_path)
        #     print(f"Local file deleted: {local_file_path}")
        # except Exception as e:
        #     print(f"Warning: Could not delete local file: {e}")

        return public_url

    except Exception as e:
        print(f"Error uploading to Firebase: {e}")
        return None


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

                    output_path = None

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

                            width, height = im.size
                            resolution_name = f"{prefix}_{width}x{height}_"

                            # Change extension to jpg
                            jpg_filename = os.path.splitext(filename)[0] + '.jpg'
                            output_path = os.path.join(output_folder, f"{resolution_name}{jpg_filename}")

                            # Save as JPG
                            im.save(output_path, 'JPEG', quality=95)
                            os.remove(input_path)
                    else:
                        # Handle non-PNG files
                        with Image.open(input_path) as im:
                            width, height = im.size
                            resolution_name = f"{prefix}_{width}x{height}_"
                            output_path = os.path.join(output_folder, f"{resolution_name}{filename}")
                            os.rename(input_path, output_path)

                    return output_path  # Return the path of the saved file

                else:
                    print(f"Failed to download image. Status code: {response.status}")
                    return None

    except Exception as e:
        print(f"Error in download_image: {e}")
        return None

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
