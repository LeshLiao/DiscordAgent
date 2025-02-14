import os
from dotenv import load_dotenv
from openai import OpenAI
import base64
import json
from typing import Tuple, Dict

class ImageAnalyzer:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")

        # Initialize the OpenAI client
        self.client = OpenAI(api_key=api_key)

    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string

        Args:
            image_path (str): Path to the image file

        Returns:
            str: Base64 encoded image string
        """
        try:
            with open(image_path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            raise Exception(f"Error encoding image: {str(e)}")

    def _parse_response(self, response_content: str) -> Tuple[str, list]:
        """
        Parse the JSON response from OpenAI

        Args:
            response_content (str): JSON response string from OpenAI

        Returns:
            Tuple[str, list]: Title and list of tags
        """
        try:
            response_data = json.loads(response_content)
            return response_data["name"], response_data["tags"]
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing JSON response: {str(e)}")
        except KeyError as e:
            raise Exception(f"Missing required key in response: {str(e)}")

    def analyze_image(self, image_path: str) -> Tuple[str, list]:
        """
        Analyze an image using OpenAI's API and return title and tags

        Args:
            image_path (str): Path to the image file

        Returns:
            Tuple[str, list]: Title and list of tags
        """
        try:
            # Encode the image
            base64_image = self._encode_image(image_path)

            # Create the API request
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI that generates titles and tags for images. Always format the JSON response exactly as shown in the example."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": 'Please provide a title for the attached image, and give it some image tags. (1) A descriptive title for the image. (2) A list of relevant tags, including general descriptors and the two main colors in hexadecimal format with their respective coverage percentages (from 1% to 100%), appended to the color hex code. please return as a json format, here is a response example: {"name": "Twilight over the Bay Bridge","tags": ["Landscape","Cityscape","Bridge","Skyline","#8B008B%045","#4682B4%020"]}'
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )

            # Parse and return the response
            api_response = response.choices[0].message.content
            print("api_response=")
            print(api_response)
            return self._parse_response(api_response)

        except Exception as e:
            raise Exception(f"Error analyzing image: {str(e)}")

# Usage example:
if __name__ == "__main__":
    try:
        analyzer = ImageAnalyzer()
        title, tags = analyzer.analyze_image("ignoreFolder/test.jpg")
        print(f"Title: {title}")
        print(f"Tags: {tags}")
    except Exception as e:
        print(f"Error: {str(e)}")