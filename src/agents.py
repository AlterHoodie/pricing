from typing import List, Dict, Any
import json
import logging

from src.clients import openai_response
from src.prompts import CATEGORIZE_PROMPT
from src.utils import extract_x

async def categorize(
    images: List[str]
) -> Dict[str, Any]:
    """
    Calls the AI model with images and a specific category schema,
    then parses the JSON response.
    """
    prompt = CATEGORIZE_PROMPT
    response_text = await openai_response(images=images, prompt=prompt, model="gpt-4.1-mini")

    response_json = extract_x(response_text,"json")
    try:
        return json.loads(response_json)
    except json.JSONDecodeError as e:
        logging.error(
            f"Error decoding JSON from AI response for schema starting with: {category_schema[:50]}..."
        )
        logging.error(f"Error: {e}")
        logging.error(f"Received response: {response_json}")
        return {
            "error": "Failed to parse JSON response",
            "raw_response": response_json,
        }