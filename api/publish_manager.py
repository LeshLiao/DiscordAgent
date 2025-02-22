from dataclasses import dataclass
from typing import List, Optional, Dict, Union
from api.wallpaper_api import WallpaperAPI, ImageItem, DownloadItem

@dataclass
class PublishConfig:
    """Configuration for publishing items"""
    default_price: float = 2.8
    default_stars: int = 5
    default_photo_type: str = "static"
    default_free_download: bool = True
    default_preview: str = ""
    id_prefix: str = "10"  # Prefix for generated item IDs

class PublishManager:
    def __init__(self, config: Optional[PublishConfig] = None):
        """
        Initialize PublishManager with optional configuration

        Args:
            config: PublishConfig object with default settings
        """
        self.api = WallpaperAPI()
        self.config = config or PublishConfig()
        self._last_generated_id = 0

    def _create_image_list(self, has_small: bool = True, has_large: bool = True) -> List[ImageItem]:
        """Create default image list"""
        image_list = []
        if has_small:
            image_list.append(ImageItem(type="small", name="small.jpg"))
        if has_large:
            image_list.append(ImageItem(type="large", name="large.jpg"))
        return image_list

    def _create_download_list(self, url: str, resolution: str, ext: str = "jpg") -> List[DownloadItem]:
        """Create download list with given parameters"""
        return [DownloadItem(size=resolution, ext=ext, link=url)]

    async def publish(
        self,
        message,
        thumbnail_url: str,
        upscaled_url: str,
        title: str,
        tags: List[str],
        resolution: str = "1632x2912",
        item_id: Optional[str] = None,
        price: Optional[float] = None,
        stars: Optional[int] = None,
        photo_type: Optional[str] = None,
        free_download: Optional[bool] = None,
        preview: Optional[str] = None,
    ) -> bool:
        """
        Publish a new wallpaper item

        Args:
            message: Discord message object for sending responses
            thumbnail_url: URL of the thumbnail image
            upscaled_url: URL of the full item image
            title: Title of the wallpaper
            tags: List of tags for the wallpaper
            resolution: Image resolution (default: "1632x2912")
            item_id: Optional custom item ID
            price: Optional custom price
            stars: Optional custom star rating
            photo_type: Optional custom photo type
            free_download: Optional custom free download flag
            preview: Optional custom preview image

        Returns:
            bool: True if publication was successful, False otherwise
        """
        try:
            # Use provided values or defaults from config
            final_item_id = ""
            final_price = price or self.config.default_price
            final_stars = stars or self.config.default_stars
            final_photo_type = photo_type or self.config.default_photo_type
            final_free_download = free_download if free_download is not None else self.config.default_free_download
            final_preview = preview or self.config.default_preview

            # Create image and download lists
            image_list = self._create_image_list()
            download_list = self._create_download_list(upscaled_url, resolution)

            # Add wallpaper through API
            result = self.api.add_wallpaper(
                item_id = "",  # If item_id is empty (""), backend will auto-generate a new ID
                name=title,
                price=final_price,
                free_download=final_free_download,
                stars=final_stars,
                photo_type=final_photo_type,
                tags=tags,
                size_options=[resolution],
                thumbnail=thumbnail_url,
                preview=final_preview,
                image_list=image_list,
                download_list=download_list
            )

            # Handle the response
            response_text = str(result)
            if "successful" in response_text and "itemId=" in response_text:
                # Extract itemId from success message
                new_item_id = response_text.split("itemId=")[-1]
                await message.channel.send(f"✅ Item published successfully!\nItem ID: {new_item_id}")
                return True
            else:
                await message.channel.send(f"❌ Failed to add the item: {response_text}")
                return False

        except Exception as e:
            await message.channel.send(f"Error during publication: {str(e)}")
            return False

# Example usage:
"""
# Create a custom configuration
config = PublishConfig(
    default_price=3.0,
    default_stars=4,
    id_prefix="20"
)

# Initialize the manager
publisher = PublishManager(config)

# Publish an item
await publisher.publish(
    message=message,
    thumbnail_url="https://example.com/thumb.jpg",
    upscaled_url="https://example.com/item.jpg",
    title="Beautiful Landscape",
    tags=["Nature", "Landscape"],
    resolution="1920x1080"
)
"""