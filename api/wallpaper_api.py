import requests
import json
from typing import List, Dict, Union, Optional
from dataclasses import dataclass

@dataclass
class ImageItem:
    type: str
    name: str

@dataclass
class DownloadItem:
    size: str
    ext: str
    link: str

class WallpaperAPI:
    def __init__(self, base_url: str = "https://online-store-service.onrender.com"):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, data: Optional[dict] = None) -> Dict[str, Union[bool, str]]:
        """
        Make HTTP request to the API

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            data: Request payload (optional)

        Returns:
            Dictionary containing response status and message
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data if data else None
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": response.text
                }
            else:
                return {
                    "success": False,
                    "message": f"Error: {response.text}"
                }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Request failed: {str(e)}"
            }

    def add_wallpaper(
        self,
        item_id: str,
        name: str,
        price: float,
        free_download: bool,
        stars: int,
        photo_type: str,
        tags: List[str],
        size_options: List[str],
        thumbnail: str,
        preview: str,
        image_list: List[ImageItem],
        download_list: List[DownloadItem]
    ) -> Dict[str, Union[bool, str]]:
        """
        Add a new wallpaper item to the database.

        Args:
            item_id: Unique identifier for the wallpaper
            name: Name of the wallpaper
            price: Price of the wallpaper
            free_download: Whether the wallpaper is free to download
            stars: Rating of the wallpaper (1-5)
            photo_type: Type of photo (e.g., "static")
            tags: List of tags describing the wallpaper
            size_options: Available size options
            thumbnail: Thumbnail image filename
            preview: Preview image filename
            image_list: List of image variations with type and filename
            download_list: List of download options with size and link

        Returns:
            Dictionary with status and message
        """
        payload = {
            "itemId": item_id,
            "name": name,
            "price": price,
            "freeDownload": free_download,
            "stars": stars,
            "photoType": photo_type,
            "tags": tags,
            "sizeOptions": size_options,
            "thumbnail": thumbnail,
            "preview": preview,
            "imageList": [{"type": img.type, "name": img.name} for img in image_list],
            "downloadList": [{"size": dl.size, "ext": dl.ext, "link": dl.link} for dl in download_list]
        }

        return self._make_request("POST", "/api/items", payload)

    def get_wallpapers(self) -> Dict[str, Union[bool, str, List[dict]]]:
        """Get all wallpapers"""
        return self._make_request("GET", "/api/items")

    def get_wallpaper(self, item_id: str) -> Dict[str, Union[bool, str, dict]]:
        """Get a specific wallpaper by ID"""
        return self._make_request("GET", f"/api/items/{item_id}")

    def update_wallpaper(self, item_id: str, data: dict) -> Dict[str, Union[bool, str]]:
        """Update a wallpaper"""
        return self._make_request("PUT", f"/api/items/{item_id}", data)

    def delete_wallpaper(self, item_id: str) -> Dict[str, Union[bool, str]]:
        """Delete a wallpaper"""
        return self._make_request("DELETE", f"/api/items/{item_id}")