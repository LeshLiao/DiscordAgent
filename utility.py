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
import platform

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

        return download_url, destination_blob_name

    except Exception as e:
        print(f"Error upload_to_firebase_3(): {e}")
        return None, None  # Return both values as None instead of just None


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

def type_imagine(prompt):
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

def safe_delete(file_path):
    # Safely delete the local file
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Successfully deleted local file: {file_path}")
    except Exception as delete_error:
        print(f"Warning: Could not delete local file {file_path}: {delete_error}")
        # Continue execution since upload was successful

def click_somewhere(image_file, interval_seconds=1, repeat=1, retry=2, retry_interval=1):
    """
    Locate an image on screen and click on it, with proper handling for MacOS Retina displays.
    Will retry finding the image if not found on first attempt.

    Args:
        image_file (str): Path to the image file to locate on screen
        interval_seconds (float): Time to wait between clicks in seconds
        repeat (int): Number of times to click the image
        retry (int): Number of times to retry finding the image if not found
        retry_interval (float): Time to wait between retries in seconds

    Returns:
        bool: True if image was found and clicked, False otherwise
    """
    print(f"click_somewhere( {image_file}, interval={interval_seconds}s, repeat={repeat}x, retry={retry}x )")

    # Retry loop
    for attempt in range(retry + 1):  # +1 because first attempt is not a retry
        try:
            if attempt > 0:
                print(f"Retry attempt {attempt}/{retry} for finding image: {image_file}")
                time.sleep(retry_interval)  # Wait before retrying

            # Locate the image on the screen
            location = pyautogui.locateOnScreen(image_file, confidence=0.8)

            if location:
                print(f"Image found on attempt {attempt + 1}!")
                # Get the center of the located image
                center = pyautogui.center(location)

                # Check if running on MacOS (for Retina display adjustment)
                if is_macos():
                    # Adjust for Retina display by dividing coordinates by 2
                    click_x, click_y = center[0] / 2, center[1] / 2
                    print(f"MacOS detected - Using adjusted coordinates: ({click_x}, {click_y})")
                else:
                    # Use original coordinates on non-MacOS systems
                    click_x, click_y = center[0], center[1]
                    print(f"Using original coordinates: ({click_x}, {click_y})")

                # Perform the specified number of clicks
                for i in range(repeat):
                    if i > 0:  # Don't wait before the first click
                        time.sleep(interval_seconds)
                    # Click the center of the image
                    pyautogui.click(x=click_x, y=click_y)
                    print(f"Click {i+1}/{repeat} completed")

                return True

            print(f"Image not found on attempt {attempt + 1}")
            # Continue to next retry attempt if image not found

        except Exception as e:
            print(f"Error in click_somewhere (attempt {attempt + 1}): {str(e)}")
            import traceback
            traceback.print_exc()

    # If we've tried all attempts and still haven't found the image
    print(f"Image not found after {retry + 1} attempts: {image_file}")
    return False

def is_macos():
    """
    Detects if the current operating system is MacOS.

    Returns:
        bool: True if the current OS is MacOS, False otherwise
    """
    system = platform.system()
    return system == "Darwin"  # MacOS reports as "Darwin" in platform.system()

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
    # click_somewhere("img/Message_upscale_textbox.png")

    click_somewhere("img/mongodb.png",interval_seconds = 2, repeat = 1, retry= 3, retry_interval = 2)



    # Detection current OS
    # if is_macos():
    #     print("Running on MacOS")
    # else:
    #     print(f"Not running on MacOS. Current OS: {platform.system()}")

