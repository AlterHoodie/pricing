import re
import logging
from PIL import Image
from typing import List, Tuple
import asyncio

from src.clients import download_image

def extract_x(response: str, code_type: str) -> str:
    pattern = rf"```{code_type}\s*(.*?)```"
    match = re.search(pattern, response, re.DOTALL)
    return match.group(1).strip() if match else response

async def create_collage_from_urls(image_urls:List[str], width:int=800, height:int=1000, layout:Tuple=None)-> Image:
    """
    Creates a collage from a list of image URLs.
    
    Parameters:
    - image_urls: List of URLs to the images
    - output_path: Path where the collage will be saved
    - width: Width of the output collage
    - height: Height of the output collage
    - layout: Tuple indicating (rows, columns). If None, it will be calculated automatically.
    """
    # Download all images
    images = []
    # Download images in parallel using asyncio.gather
    downloaded_images = await asyncio.gather(*[download_image(url) for url in image_urls])
    images = [img for img in downloaded_images if img is not None]
    
    if not images:
        logging.error("No images could be downloaded. Check your URLs and internet connection.")
        raise Exception("No images could be downloaded. Check your URLs and internet connection.")
    
    # Calculate layout if not provided
    if layout is None:
        n = len(images)
        if n <= 2:
            rows, cols = 1, n
        elif n <= 4:
            rows, cols = 2, 2
        elif n <= 6:
            rows, cols = 2, 3
        elif n <= 9:
            rows, cols = 3, 3
        else:
            # Calculate approximately square layout
            import math
            cols = math.ceil(math.sqrt(n))
            rows = math.ceil(n / cols)
    else:
        rows, cols = layout
    
    # Calculate dimensions for each image in the collage
    img_width = width // cols
    img_height = height // rows
    
    # Create a new blank image for the collage
    collage = Image.new('RGB', (width, height), (255, 255, 255))
    
    # Place each image in the collage
    for i, img in enumerate(images):
        if i >= rows * cols:
            break  # Don't try to place more images than our layout allows
            
        # Resize image maintaining aspect ratio
        img_aspect = img.width / img.height
        cell_aspect = img_width / img_height
        
        if img_aspect > cell_aspect:
            # Image is wider than cell
            new_width = img_width
            new_height = int(new_width / img_aspect)
            offset_x = 0
            offset_y = (img_height - new_height) // 2
        else:
            # Image is taller than cell
            new_height = img_height
            new_width = int(new_height * img_aspect)
            offset_x = (img_width - new_width) // 2
            offset_y = 0
            
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate position
        row = i // cols
        col = i % cols
        x = col * img_width + offset_x
        y = row * img_height + offset_y
        
        # Paste the image into the collage
        collage.paste(img_resized, (x, y))
    
    return collage