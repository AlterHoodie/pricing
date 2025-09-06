from src.services.rapidapi import get_instagram_page_info, get_instagram_post_info
from src.agents import analyze_asset
from src.utils import create_collage_from_urls
import logging
import asyncio

logging.getLogger().setLevel(logging.INFO)

def classify_pricing(follower_count: int, engagement_rate: float, content_type: str) -> dict:
    """
    Classify pricing based on follower count, engagement rate, and content type.
    
    Args:
        follower_count (int): Number of followers
        engagement_rate (float): Engagement rate as percentage (0-100)
        content_type (str): Either 'premium' or 'mass-meme'
    
    Returns:
        dict: Contains price_range, internal_cost_estimate, pitching_cost_estimate, and classification_details
    """
    
    # Convert engagement rate to decimal if provided as percentage
    if engagement_rate > 10:
        engagement_rate = engagement_rate / 100
    
    # Define pricing structure based on the image and notebook analysis
    if content_type.lower() == 'premium':
        pricing_matrix = {
            # Format: (follower_min, follower_max, engagement_min, engagement_max): (internal_cost, pitching_cost, tier)
            (0, 100000, 0, 1): (700, 1200, "Premium Basic Low Engagement"),
            (0, 100000, 1, 5): (1200, 1500, "Premium Basic Medium Engagement"),
            (0, 100000, 5, 100): (1500, 2000, "Premium Basic High Engagement"),
            
            (100000, 500000, 0, 1): (2000, 2500, "Premium Mid Low Engagement"),
            (100000, 500000, 1, 5): (2500, 3000, "Premium Mid Medium Engagement"),
            (100000, 500000, 5, 100): (3000, 4000, "Premium Mid High Engagement"),
            
            (500000, 1000000, 0, 1): (2500, 3000, "Premium Large Low Engagement"),
            (500000, 1000000, 1, 5): (3000, 5000, "Premium Large Medium Engagement"),
            (500000, 1000000, 5, 100): (5000, 8500, "Premium Large High Engagement"),
            
            (1000000, 2500000, 0, 1): (7000, 15000, "Premium Mega Low Engagement"),
            (1000000, 2500000, 1, 5): (15000, 25000, "Premium Mega Medium Engagement"),
            (1000000, 2500000, 5, 100): (25000, 35000, "Premium Mega High Engagement"),
            
            (2500000, 5000000, 0, 1): (15000, 25000, "Premium Ultra Low Engagement"),
            (2500000, 5000000, 1, 5): (25000, 35000, "Premium Ultra Medium Engagement"),
            (2500000, 5000000, 5, 100): (35000, 75000, "Premium Ultra High Engagement"),
            
            (5000000, float('inf'), 0, 1): (25000, 35000, "Premium Celebrity Low Engagement"),
            (5000000, float('inf'), 1, 5): (35000, 75000, "Premium Celebrity Medium Engagement"),
            (5000000, float('inf'), 5, 100): (75000, 150000, "Premium Celebrity High Engagement"),
        }
    
    else:  # mass-meme or general
        pricing_matrix = {
            # Format: (follower_min, follower_max, engagement_min, engagement_max): (internal_cost, pitching_cost, tier)
            (0, 100000, 0, 1): (150, 200, "General Basic Low Engagement"),
            (0, 100000, 1, 5): (200, 300, "General Basic Medium Engagement"),
            (0, 100000, 5, 100): (300, 400, "General Basic High Engagement"),
            
            (100000, 500000, 0, 1): (400, 600, "General Mid Low Engagement"),
            (100000, 500000, 1, 5): (600, 800, "General Mid Medium Engagement"),
            (100000, 500000, 5, 100): (800, 1200, "General Mid High Engagement"),
            
            (500000, 1000000, 0, 1): (1000, 1500, "General Large Low Engagement"),
            (500000, 1000000, 1, 5): (1500, 2000, "General Large Medium Engagement"),
            (500000, 1000000, 5, 100): (2500, 3500, "General Large High Engagement"),
            
            (1000000, 2500000, 0, 1): (2000, 3000, "General Mega Low Engagement"),
            (1000000, 2500000, 1, 5): (3500, 5000, "General Mega Medium Engagement"),
            (1000000, 2500000, 5, 100): (6000, 8000, "General Mega High Engagement"),
            
            (2500000, 5000000, 0, 1): (5000, 7000, "General Ultra Low Engagement"),
            (2500000, 5000000, 1, 5): (8000, 10000, "General Ultra Medium Engagement"),
            (2500000, 5000000, 5, 100): (12000, 15000, "General Ultra High Engagement"),
            
            (5000000, float('inf'), 0, 1): (10000, 15000, "General Celebrity Low Engagement"),
            (5000000, float('inf'), 1, 5): (15000, 20000, "General Celebrity Medium Engagement"),
            (5000000, float('inf'), 5, 100): (25000, 30000, "General Celebrity High Engagement"),
        }
    
    # Find matching price tier
    for (f_min, f_max, e_min, e_max), (internal_cost, pitching_cost, tier) in pricing_matrix.items():
        if (f_min <= follower_count < f_max and 
            e_min <= engagement_rate < e_max):
            
            return {
                "price_tier": tier,
                "min_cost_estimate": internal_cost,  # Min price
                "max_cost_estimate": pitching_cost,  # Max price
                "follower_range": f"{f_min:,}-{f_max:,}" if f_max != float('inf') else f"{f_min:,}+",
                "engagement_range": f"{e_min}-{e_max}%",
                "content_type": content_type,
            }
    
    # Default case if no match found
    return {
        "price_tier": "Unclassified",
        "min_cost_estimate": 0,
        "max_cost_estimate": 0,
        "follower_range": "Unknown",
        "engagement_range": "Unknown", 
        "content_type": content_type,
        "error": "No matching price tier found for given parameters"
    }


async def get_pricing_from_instagram(page_url: str, page_name: str) -> dict:
    page_info = await get_instagram_page_info(page_url)
    if not page_info:
        logging.warning(f"No page info found for {page_url}")
        return {"error": "No page info found", "page_url": page_url}

    post_array, raw_post_array = await get_instagram_post_info(page_info["platform_specific_info"]["pk"], n_posts=27)
    follower_count = page_info["follower_count"]

    engagement_rate = sum([post["like_count"] + post["comment_count"] + post.get("view_count", 0) for post in post_array]) / follower_count
    logging.info(f"Engagement rate: {engagement_rate}")

    if not post_array:
        logging.warning(f"No posts found for {page_url}")
        return {"error": "No posts found", "page_url": page_url}

    # Extract image URLs from posts
    image_urls = []
    for post in post_array:
        if post.get("media_list"):
            for media in post["media_list"]:
                if media.get('type') in ['thumbnail', 'image'] and media.get('url'):
                    image_urls.append(media.get('url'))
                    break

    if not image_urls:
        logging.warning(f"No images found for {page_url}")
        return {"error": "No images found", "page_url": page_url}
    
    collages = []
    if image_urls:
        tasks = []
        for i in range(0, min(len(image_urls), 27), 9):
            tasks.append(create_collage_from_urls(
                image_urls[i:i+9],
                width=900,
                height=900
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logging.warning(f"Failed to create collage: {result}")
            else:
                collages.append(result)
    
    # Max 3 collages * 9 images
    if collages:
        try:
            analysis = await analyze_asset(page_name,collages)
            if "pricing" in analysis:
                content_category = analysis["pricing"].get("category", "general")
            else:
                logging.warning(f"No pricing analysis found for {page_url}")
                content_category = "general"
        except Exception as e:
            logging.warning(f"Classification failed: {e}")

    logging.info(f"Collages created: {len(collages)}")

    logging.info(f"Analysis: {analysis}")

    return classify_pricing(follower_count, engagement_rate, content_category) | {"brand_analysis": analysis}

if __name__ == "__main__":
    import asyncio
    import json
    with open("./data/general_sample_profiles.json", "r") as f:
        general_sample_profiles = json.load(f)
    with open("./data/premium_sample_profiles.json", "r") as f:
        premium_sample_profiles = json.load(f)
    
    for page in premium_sample_profiles[1:2]:
        print(page["profile_link"], page["Username"])
        pricing = asyncio.run(get_pricing_from_instagram(page["profile_link"], page["Username"]))
        page["pricing"] = pricing
        print(pricing)
        print("-"*100)
    with open("./data/test.json", "w") as f:
        json.dump(premium_sample_profiles, f)