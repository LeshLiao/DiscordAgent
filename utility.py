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


# when you use blob.make_public(), the URL will have no expiration
def upload_to_firebase_3(local_file_path, firebase_folder):
    """
    Uploads an image to Firebase Storage and returns a non-signed download URL

    Args:
        local_file_path (str): The local path to the image file
        firebase_folder (str): The folder name in Firebase Storage (e.g., 'thumbnail', 'upscaled')

    Returns:
        str: The Firebase Storage download URL of the uploaded file
    """
    try:
        # Get bucket
        bucket = storage.bucket()

        # Get the base filename from the local path
        filename = os.path.basename(local_file_path)
        file_ext = os.path.splitext(local_file_path)[1]

        # Create unique filename with UTC timestamp and UUID
        time_string = get_utc_time()
        firebase_filename = f"{time_string}{firebase_folder}_{str(uuid.uuid4())}{file_ext}"

        # Create the full path in Firebase Storage
        destination_blob_name = f'images/{firebase_folder}/{firebase_filename}'

        # Upload the file
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(local_file_path)

        # Make the blob publicly accessible
        blob.make_public()

        # Construct the Firebase Storage download URL
        download_url = (
            f"https://firebasestorage.googleapis.com/v0/b/{bucket.name}"
            f"/o/{destination_blob_name.replace('/', '%2F')}?alt=media"
        )

        print(f"File uploaded successfully to Firebase Storage: {destination_blob_name}")
        print(f"Download URL: {download_url}")

        return download_url

    except Exception as e:
        print(f"Error uploading to Firebase: {e}")
        return None


async def download_image(url, filename, prefix):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    # Define folders
                    input_folder = "input"     # from discord
                    output_folder = "output"   # converted file output

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
                            os.rename(input_path, output_path) # the input_path will no longer exist after rename

                    return output_path  # Return the path of the saved file

                else:
                    print(f"Failed to download image. Status code: {response.status}")
                    return None

    except Exception as e:
        print(f"Error in download_image: {e}")
        return None

def click_discord_and_imagine(prompt):
    position_x = 542
    position_y = 658
    # Click on Discord message box
    pyautogui.click(x=position_x, y=position_y)
    time.sleep(1)
    pyautogui.click(x=position_x, y=position_y)
    # Type the command
    pyautogui.write("/imagine")
    time.sleep(1)
    pyautogui.press('space')
    time.sleep(1)
    pyautogui.press('space')
    time.sleep(1)
    pyautogui.write(prompt)
    time.sleep(1)
    pyautogui.press('enter')

def click_specific_button():
    # Locate the image on the screen
    location = pyautogui.locateOnScreen('img/upscale.png', confidence=0.8)
    if location:
        # Get the center of the located image
        center = pyautogui.center(location)
        # Click the center of the image
        pyautogui.click(center)
    else:
        print("Image not found on the screen.")

def safe_delete(file_path):
    # Safely delete the local file
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Successfully deleted local file: {file_path}")
    except Exception as delete_error:
        print(f"Warning: Could not delete local file {file_path}: {delete_error}")
        # Continue execution since upload was successful


# Usage example:
if __name__ == "__main__":

    # Test upload to firebase
    # try:
    #     initialize_firebase()
    #     new_url = upload_to_firebase_3("output/test.jpg", "thumbnail")
    #     print("new_url=")
    #     print(new_url)
    # except Exception as e:
    #     print(f"utility.py Error: {str(e)}")

    # Test click button
    click_specific_button()