import os
from dotenv import load_dotenv
from openai import OpenAI
import base64

# Load environment variables from .env file
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Path to your image file
image_path = 'ignoreFolder/test.jpg'

# Create a chat completion with the image
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are an AI that generates titles and tags for images, Always format the JSON response exactly as shown in the example."
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
                        "url": f"data:image/jpeg;base64,{base64.b64encode(open(image_path, 'rb').read()).decode('utf-8')}"
                    }
                }
            ]
        }
    ],
    max_tokens=300
)

# Extract and print the generated response
print("Generated Response:", response.choices[0].message.content)