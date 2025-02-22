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
def printImageUrl(api_key):
    query = 'nature'
    per_page = 80 # max 80
    page = 1
    url = f'https://api.pexels.com/v1/search?query={query}&per_page={per_page}&page={page}'

    temp_note = f"search?query={query}&per_page={per_page}&page={page}"

    headers = {
        'Authorization': api_key
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
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
    else:
        print(f'Error: {response.status_code}')


def add_one(source, note, url):
    # Add a new item to the waiting list
    response = api_client.add_waiting_item(
        source=source,
        url=url,
        priority=0,
        note=note,
    )

    # Check the response
    if response["success"]:
        print("Item added successfully.")
    else:
        print(f"Failed to add item: {response['message']}")

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Get api key from environment variable
    api_key = os.getenv('PEXELS_COM_API')
    if not api_key:
        print("Error: PEXELS_COM_API not found in environment variables")
        exit(1)

    # testFunction(api_key)
    printImageUrl(api_key)

    # Initialize the API client
    # api_client = WallpaperAPI()

