import logging
import re
from typing import List, Dict, Any
from datetime import datetime
import os

from dotenv import load_dotenv
from src.clients import call_rapid_api

load_dotenv(override=True)

api_key = os.getenv("RAPID_API_KEY")


def extract_instagram_post_data(posts_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extracts specific information from a list of Instagram post data dictionaries
    from the RapidAPI structure.

    Args:
        posts_data: A list of dictionaries, where each dictionary represents
                    an Instagram post's data (like the provided example).

    Returns:
        A list of dictionaries, where each dictionary contains the
        extracted information for a single post. Returns an empty list
        if the input is empty or invalid.
    """
    extracted_posts = []
    if not isinstance(posts_data, list):
        print("Error: Input must be a list of post dictionaries.")
        return []

    # If a single post dictionary is passed instead of a list, wrap it in a list
    if posts_data and not isinstance(posts_data[0], dict):
        posts_data = [posts_data]

    for post in posts_data:
        if not isinstance(post, dict):
            print(f"Warning: Skipping invalid item in list: {post}")
            continue

        post_info = {}
        post_info["code"] = post.get("code")
        # Convert ISO timestamp to Unix timestamp
        taken_at_iso = post.get("taken_at")
        if taken_at_iso:
            post_info["taken_at"] = int(datetime.fromisoformat(taken_at_iso.replace('Z', '+00:00')).timestamp())
        else:
            post_info["taken_at"] = None

        # Extract user info, including the profile picture URL
        user_info = post.get("user", {})
        post_info["username"] = user_info.get("username")
        post_info["user_full_name"] = user_info.get("full_name")

        # 1. Type of post
        media_type = post.get("media_type")
        if media_type == 1:
            post_info["type"] = "image"
        elif media_type == 2:
            post_info["type"] = "video"
        elif media_type == 8:
            post_info["type"] = "carousel"
        else:
            post_info["type"] = post.get("product_type", "unknown")

        # 2. Counts
        post_info["like_count"] = post.get("like_count", 0)
        post_info["share_count"] = post.get("share_count", 0)
        post_info["comment_count"] = post.get("comment_count", 0)
        post_info["sponsor_tags"] = post.get("sponsor_tags", [])

        # 3. Played count (for videos) or View count
        if post_info["type"] == "video":
            post_info["played_count"] = post.get("play_count") or post.get("view_count", 0)
        else:
            post_info["played_count"] = 0

        # 4. Caption, Hashtags, and Mentions
        caption_text = post.get("caption_text", "") or ""
        post_info["caption"] = caption_text
        post_info["hashtags"] = re.findall(r"#(\w+)", caption_text)
        post_info["mentions"] = re.findall(r"@(\w+)", caption_text)

        # 5. Is paid partnership
        post_info["is_paid_partnership"] = post.get("is_paid_partnership", False)

        # 6. Media list (URLs and types)
        media_list = []
        resources = []

        if post_info["type"] == "carousel":
            resources = post.get("resources", [])
        else:
            resources = [post]

        for item in resources:
            item_media_type = item.get("media_type")
            if item_media_type == 1:  # Image
                image_versions = item.get("image_versions", [])
                if image_versions and isinstance(image_versions, list) and len(image_versions) > 0:
                    media_list.append({
                        "url": image_versions[0].get("url"),
                        "type": "image"
                    })
            elif item_media_type == 2:  # Video
                image_versions = item.get("image_versions", [])
                if image_versions and isinstance(image_versions, list) and len(image_versions) > 0:
                    media_list.append({
                        "url": image_versions[0].get("url"),
                        "type": "thumbnail"
                    })
                video_versions = item.get("video_versions", [])
                if video_versions and isinstance(video_versions, list) and len(video_versions) > 0:
                    media_list.append({
                        "url": video_versions[0].get("url"),
                        "type": "video"
                    })

        post_info["media_list"] = [media for media in media_list if media.get("url")]

        extracted_posts.append(post_info)

    return extracted_posts


async def get_instagram_post_info(
    page_id: str, n_posts: int = 500
) -> tuple:

    pagination_token = None
    post_array = []
    raw_post_array = []
    should_continue = True

    query_string = {"user_id": page_id}
    url = "https://instagram-premium-api-2023.p.rapidapi.com/v1/user/medias/chunk"
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "instagram-premium-api-2023.p.rapidapi.com"}

    while should_continue:
        if pagination_token:
            query_string["end_cursor"] = pagination_token

        data = await call_rapid_api(url=url, params=query_string, headers=headers)
        if not data:
            return [], []

        posts = data[0]
        pagination_token = data[1]

        if posts:
            posts_info = extract_instagram_post_data(posts)
            post_array.extend(posts_info)
            raw_post_array.extend(posts)

        # Stop conditions:
        # 1. If we have enough posts (n_posts limit reached)
        # 2. If no more pagination token available
        if len(post_array) >= n_posts:
            should_continue = False
        elif not pagination_token:
            should_continue = False

    return post_array, raw_post_array

def extract_instagram_page_info(page_data: dict) -> dict:
    page_info = {
        "asset_name": page_data.get("username", ""),
        "description": page_data.get("biography", ""),
        "follower_count": page_data.get("follower_count", 0),
        "is_verified": page_data.get("is_verified", False),
        "platform_specific_info": {},
    }
    page_info_schema = [
        "pk",
        "full_name",
        "is_private",
        "profile_pic_url",
        "profile_pic_url_hd",
        "media_count",
        "following_count",
        "is_business",
        "public_email",
        "contact_phone_number",
        "public_phone_country_code",
        "public_phone_number",
        "category"
    ]

    for key in page_info_schema:
        page_info["platform_specific_info"][key] = page_data.get(key)
    return page_info


async def get_instagram_page_info(page_url: str) -> dict:
    try:
        query_string = {"url": page_url}
        url = "https://instagram-premium-api-2023.p.rapidapi.com/v1/user/by/url"
        headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "instagram-premium-api-2023.p.rapidapi.com"}

        data = await call_rapid_api(url, params=query_string, headers=headers)
        if data.get("exc_type"):
            raise Exception(f"{data.get('exc_type')}")
        if data:
            return extract_instagram_page_info(data)

        raise Exception(f"RapidAPI: Page Data Empty")
    except Exception as e:
        logging.error(f"RapidAPI: Unknown error:{e}")
        return {}

if __name__ == "__main__":
    import asyncio
    post_array, raw_post_array = asyncio.run(get_instagram_post_info(page_url="https://www.instagram.com/pubity", n_posts=10))
    print(post_array)
    print(raw_post_array)