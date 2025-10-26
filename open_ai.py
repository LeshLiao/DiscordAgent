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

    def parse_analyze_image_response(self, response_content: str) -> Tuple[str, list]:
        """
        Parse the JSON response from OpenAI, handling both direct JSON and code block formats

        Args:
            response_content (str): Response string from OpenAI which might be either:
                - Direct JSON: {"name": "Title", "tags": [...]}
                - Code block: ```json\n{"name": "Title", "tags": [...]}\n```

        Returns:
            Tuple[str, list]: Title and list of tags
        """
        try:
            # First, try to clean up the response if it's in a code block
            cleaned_content = response_content.strip()
            if cleaned_content.startswith('```json'):
                # Remove ```json from start and ``` from end
                cleaned_content = cleaned_content.replace('```json', '', 1).strip()
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3].strip()

            # Parse the JSON
            response_data = json.loads(cleaned_content)

            # Validate required fields
            if 'name' not in response_data or 'tags' not in response_data:
                raise KeyError("Response missing required 'name' or 'tags' fields")

            if not isinstance(response_data['name'], str):
                raise ValueError("'name' field must be a string")

            if not isinstance(response_data['tags'], list):
                raise ValueError("'tags' field must be a list")

            return response_data["name"], response_data["tags"]

        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing JSON response: {str(e)}\nResponse content: {response_content}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Invalid response format: {str(e)}\nResponse content: {response_content}")
        except Exception as e:
            raise Exception(f"Unexpected error parsing response: {str(e)}\nResponse content: {response_content}")

    def parse_describe_image_response(self, response_content: str) -> str:
        """
        Parse the JSON response from OpenAI for image description

        Args:
            response_content (str): Response string from OpenAI which might be either:
                - Direct JSON: {"prompt": "description text"}
                - Code block: ```json\n{"prompt": "description text"}\n```

        Returns:
            str: The description/prompt string
        """
        try:
            # First, try to clean up the response if it's in a code block
            cleaned_content = response_content.strip()
            if cleaned_content.startswith('```json'):
                # Remove ```json from start and ``` from end
                cleaned_content = cleaned_content.replace('```json', '', 1).strip()
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3].strip()

            # Parse the JSON
            response_data = json.loads(cleaned_content)

            # Validate required field
            if 'prompt' not in response_data:
                raise KeyError("Response missing required 'prompt' field")

            if not isinstance(response_data['prompt'], str):
                raise ValueError("'prompt' field must be a string")

            return response_data["prompt"]

        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing JSON response: {str(e)}\nResponse content: {response_content}")
        except (KeyError, ValueError) as e:
            raise Exception(f"Invalid response format: {str(e)}\nResponse content: {response_content}")
        except Exception as e:
            raise Exception(f"Unexpected error parsing response: {str(e)}\nResponse content: {response_content}")

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
                                "text": 'Please provide a title for the attached image, and give it some image tags. (1) A descriptive title for the image. (2) please incorporate the following popular tags when relevant: "landscape", "nature" "minimalistic" "anime" and "space", those five tags only will shown at once for a image, including general descriptors and the two main colors in hexadecimal format with their respective coverage percentages (from 1% to 100%), appended to the color hex code. please return as a json format, here is a response example: {"name": "Twilight over the Bay Bridge","tags": ["nature","bridge","skyline","#8B008B%045","#4682B4%020"]}'
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
            print("analyze_image api_response=")
            print(api_response)
            return self.parse_analyze_image_response(api_response)

        except Exception as e:
            raise Exception(f"Error analyzing image: {str(e)}")


    def describe_image(self, image_path: str) -> str:
        """
        Analyze an image using OpenAI's API and return a prompt string
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
                        "content": "Please describe the image in as much detail as possible for use with an AI image tool. Always format the JSON response exactly as shown in the example."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": 'Please describe the image in as much detail as possible for use with an AI image tool. please return as a json format, here is a response example: {"prompt": "bright sunlight shining through dense cumulus clouds, vivid blue sky and horizon curvature of the Earth, dramatic lighting"}'
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
            print("describe_image api_response=")
            print(api_response)
            return self.parse_describe_image_response(api_response)

        except Exception as e:
            raise Exception(f"Error analyzing image: {str(e)}")


# Usage example:
if __name__ == "__main__":
    try:
        analyzer = ImageAnalyzer()
        title, tags = analyzer.analyze_image("output/thumbnail_816x1456_dlnx38_minimalist_a801c4d6-82d1-4232-b22e-eb0e4a467193.jpg")
        print(f"Title: {title}")
        print(f"Tags: {tags}")
    except Exception as e:
        print(f"Error: {str(e)}")