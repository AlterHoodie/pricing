from typing import List, Dict, Any
import json
import logging
import asyncio

from src.clients import openai_response
from src.prompts import CATEGORIZE_PROMPT, BASE_PROMPT_TEMPLATE, LANGUAGE_SCHEMA, LOCATION_SCHEMA, TARGET_DEMOGRAPHICS_SCHEMA, CATEGORIZATION_TAGS_SCHEMA, CONTENT_TAGS_SCHEMA,PROFESSIONAL_ATTRIBUTES_SCHEMA, BRAND_ELEMENTS_SCHEMA
from src.utils import extract_x

async def categorize(
    images: List[str], category_schema: str
) -> Dict[str, Any]:
    """
    Calls the AI model with images and a specific category schema,
    then parses the JSON response.
    """
    prompt = BASE_PROMPT_TEMPLATE.format(category_schema)
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

async def analyze_asset(
    asset_name: str, 
    images: List[str], 
) -> Dict[str, Any]:
    """
    Analyzes various aspects of a brand using AI based on provided images, with async gather.
    
    Args:
        asset_name: Name of the asset being analyzed
        images: List of image URLs or base64 encoded images
    
    Returns:
        Dictionary of analysis results
    """
    
    categories_to_analyze = {
        "pricing": CATEGORIZE_PROMPT,
        "language": LANGUAGE_SCHEMA,
        "location": LOCATION_SCHEMA,
        "target_demographics": TARGET_DEMOGRAPHICS_SCHEMA,
        "categorization_tags": CATEGORIZATION_TAGS_SCHEMA,
        "content_tags": CONTENT_TAGS_SCHEMA,
        "professional_attributes": PROFESSIONAL_ATTRIBUTES_SCHEMA,
        "brand_elements": BRAND_ELEMENTS_SCHEMA,
    }

    brand_analysis_results = {}
    
    # Create tasks for each category
    tasks = []
    for key, schema in categories_to_analyze.items():
        tasks.append((key, categorize(images, schema)))

    # Gather results
    try:
        results = await asyncio.gather(*[task[1] for task in tasks])
        for (key, _), result in zip(tasks, results):
            brand_analysis_results[key] = result
    except Exception as e:
        logging.error(f"Error during async analysis for asset {asset_name}: {e}")
        for key, _ in tasks:
            brand_analysis_results[key] = {
                "error": str(e),
                "details": "Analysis failed for this category.",
            }

    return brand_analysis_results