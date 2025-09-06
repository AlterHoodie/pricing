import os 
from dotenv import load_dotenv
import aiohttp
from PIL import Image
from io import BytesIO
from typing import List, Tuple
import base64
import logging

import openai

load_dotenv(override=True)

openai_client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def download_image(url):
    """
    Download an image from a URL and return as a PIL Image object
    """
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                response.raise_for_status()
                content = await response.read()
                return Image.open(BytesIO(content))
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

async def openai_response(
    images: List[str], prompt, model: str = "gpt-4.1", use_web_search: bool = False
) -> Tuple[dict, dict]:

    media_type = "image/png"
    messages = []

    for image in images:
        if isinstance(image, str):
            # Handle file path
            with open(image, "rb") as f:
                encoded_image = base64.standard_b64encode(f.read()).decode("utf-8")
        elif isinstance(image, Image.Image):
            # Handle PIL Image object
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            encoded_image = base64.standard_b64encode(buffered.getvalue()).decode("utf-8")
        else:
            raise TypeError(f"Unsupported image type: {type(image)}. Expected str (file path) or PIL.Image.Image")

        messages.append(
            {
                "type": "input_image",
                "image_url": f"data:{media_type};base64,{encoded_image}",
            }
        )

    messages.append({"type": "input_text", "text": prompt})
    if use_web_search:
        response = await openai_client.responses.create(
            model=model, input=[{"role": "user", "content": messages}],
            tools=[{"type": "web_search_preview", "search_context_size": "low"}]
        )
        return response.output_text
    else:
        response = await openai_client.responses.create(
            model=model, input=[{"role": "user", "content": messages}]
        )

    return response.output_text

async def call_rapid_api(url: str, params: dict, headers: dict) -> dict:
    tries = 3
    async with aiohttp.ClientSession() as session:
        while tries > 0:
            logging.info(f"API call, {tries} tries left")
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 404:
                    raise Exception(f"Page Not Found: {response.status}")
                else:
                    content = await response.text()
                    logging.error(f"status_code:{response.status}:{content}")
                    tries -= 1
                    continue
        if tries == 0:
            raise Exception(f"Failed 3 Attempts : {response.status}")