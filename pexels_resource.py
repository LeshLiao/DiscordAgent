from pexels_api import API
import asyncio
import os
from dotenv import load_dotenv
import requests
from api.wallpaper_api import WallpaperAPI, ImageItem, DownloadItem

# Initialize the Pexels API with your API key
PEXELS_API_KEY = 'your_api_key_here'
api_client = WallpaperAPI()


def testFunction(api_key):
    api = API(api_key)
    # Search for mobile wallpapers
    query = 'mobile wallpaper'
    api.search(query, per_page=15)  # Adjust 'per_page' as needed
    photos = api.get_entries()

    # Extract and print image URLs
    for photo in photos:
        print(photo.original)  # URL to the original image



# Document: https://www.pexels.com/api/documentation/#photos-search
def printImageUrl(api_key, query_text, current_page):
    query = query_text
    per_page = 80 # max 80
    page = current_page
    url = f'https://api.pexels.com/v1/search?query={query}&per_page={per_page}&page={page}'

    temp_note = f"search?query={query}&per_page={per_page}&page={page}"

    headers = {
        'Authorization': api_key
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        add_one_count = 0
        data = response.json()
        photos = data.get('photos', [])
        for photo in photos:
            height = photo.get('height', 0)
            width = photo.get('width', 0)
            if height > width:
                original_url = photo.get('src', {}).get('original')
                if original_url:
                    print(original_url)
                    add_one("pexels.com API", temp_note, original_url)
                    add_one_count = add_one_count + 1
    else:
        print(f'Error: {response.status_code}')
    print("\n Total added:" + str(add_one_count) + "\n")

def add_one(source, note, url):
    # Add a new item to the waiting list
    response = api_client.add_waiting_item(
        source=source,
        note=note,
        url=url,
        priority=0,
        assign="",
        status="",
        itemId="",
        itemUrl="",
        review=False
    )

    # Check the response
    if response["success"]:
        print("Item added successfully.")
        return True
    else:
        print(f"Failed to add item: {response['message']}")
        return False

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Get api key from environment variable
    api_key = os.getenv('PEXELS_COM_API')
    if not api_key:
        print("Error: PEXELS_COM_API not found in environment variables")
        exit(1)

    # printImageUrl(api_key, 'nature', 1)     # 20250228 added to waiting list (28)
    # printImageUrl(api_key, 'nature', 2)     # 20250228 added to waiting list (26)
    # printImageUrl(api_key, 'nature', 3)     # 20250228 added to waiting list (31)
    # printImageUrl(api_key, 'nature', 4)     # 20250228 added to waiting list (19)
    # printImageUrl(api_key, 'nature', 5)     # 20250228 added to waiting list (34)
    # printImageUrl(api_key, 'nature', 6)     # 20250228 added to waiting list (31)
    # printImageUrl(api_key, 'nature', 7)     # 20250228 added to waiting list (22)
    # printImageUrl(api_key, 'nature', 8)     # 20250228 added to waiting list (22)

    # printImageUrl(api_key, 'space', 1)     # 20250228 added to waiting list (16)
    # printImageUrl(api_key, 'space', 2)     # 20250228 added to waiting list ()
    # printImageUrl(api_key, 'space', 3)     # 20250228 added to waiting list ()
    # printImageUrl(api_key, 'space', 4)     # 20250228 added to waiting list ()
    # printImageUrl(api_key, 'space', 5)     # 20250228 added to waiting list ()

    # printImageUrl(api_key, 'minimalistic wallpaper', 1)     # 20250228 added to waiting list ()
    # printImageUrl(api_key, 'minimalistic wallpaper', 2)     # 20250228 added to waiting list ()

    printImageUrl(api_key, 'nature', 9)     # 20250228 added to waiting list
    printImageUrl(api_key, 'nature', 10)     # 20250228 added to waiting list
    printImageUrl(api_key, 'nature', 11)     # 20250228 added to waiting list
    printImageUrl(api_key, 'nature', 12)     # 20250228 added to waiting list
    printImageUrl(api_key, 'nature', 13)     # 20250228 added to waiting list