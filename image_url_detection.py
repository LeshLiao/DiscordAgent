import requests
from io import BytesIO
from PIL import Image
from typing import Tuple, Optional

def is_image_url(url: str, timeout: int = 5) -> Tuple[bool, Optional[str]]:
    """
    Verifies if a URL points to a real image by downloading a small portion
    of the content and attempting to open it as an image.

    Args:
        url (str): URL to check
        timeout (int): Request timeout in seconds

    Returns:
        Tuple[bool, Optional[str]]: (is_image, content_type)
            - is_image: True if the URL points to a valid image
            - content_type: The Content-Type header from the response
    """
    if not url or not isinstance(url, str):
        return False, None

    # Use a streaming request with a small chunk size to minimize data transfer
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Range': 'bytes=0-16384'  # Request only the first 16KB
    }

    try:
        # Start a streaming request
        response = requests.get(url, headers=headers, stream=True, timeout=timeout)

        # Get the content type
        content_type = response.headers.get('Content-Type', '')

        # If content type doesn't seem to be an image, return early
        if not content_type.startswith('image/'):
            return False, content_type

        # Read a small chunk of data (up to 16KB)
        chunk = BytesIO()
        for data in response.iter_content(chunk_size=4096):
            chunk.write(data)
            # Only read up to 16KB to check if it's an image
            if chunk.tell() >= 16384:
                break

        # Reset buffer position
        chunk.seek(0)

        # Try to open as an image
        try:
            img = Image.open(chunk)
            # Verify by accessing image properties
            img.verify()
            return True, content_type
        except Exception:
            # Fallback method: try to at least get image size
            try:
                chunk.seek(0)
                img = Image.open(chunk)
                _ = img.size  # Try to access image size
                return True, content_type
            except Exception:
                return False, content_type
        finally:
            # Close the request to free resources
            response.close()

    except requests.RequestException as e:
        print(f"Request error: {e}")
        return False, None
    except Exception as e:
        print(f"Error validating image: {e}")
        return False, None

# Example usage
if __name__ == "__main__":
    # Test URLs - including both real images and non-images
    test_urls = [
        # "https://www.python.org/static/img/python-logo.png",       # Real image
        # "https://www.python.org/static/img/aaapython-logo.png",  # Real image
        "https://plus.unsplash.com/premium_photo-1673448760651-7e1e6fd79e40?q=80&w=2070&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
        # "https://www.google.com",                                   # Not an image
        # "https://example.com/nonexistent.jpg",                      # Non-existent
        # "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_1280.jpg",  # Real image
    ]

    for url in test_urls:
        print(f"Testing URL: {url}")
        is_image, content_type = is_image_url(url)
        print(f"Is valid image: {is_image}")
        print(f"Content type: {content_type}")
        print("-" * 50)