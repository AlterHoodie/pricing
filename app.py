import streamlit as st
import asyncio
import json
import logging
from typing import Dict, Any

# Import your existing modules
from src.pricing import classify_pricing, get_pricing_from_instagram
from src.services.rapidapi import get_instagram_page_info, get_instagram_post_info
from src.agents import analyze_asset
from src.utils import create_collage_from_urls

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Instagram Pricing Analyzer",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
    
    .left-column {
        padding-right: 1rem;
    }
    
    .right-column {
        padding-left: 1rem;
    }
    
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        height: 3rem;
        font-weight: 600;
        font-size: 16px;
    }
    
    .metric-container {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e9ecef;
        margin: 0.5rem 0;
    }
    
    .pricing-section {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .pricing-section h3 {
        color: white !important;
        margin-bottom: 1rem;
    }
    
    .pricing-section .metric-container {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    .pricing-section [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 1rem;
    }
    
    .pricing-section [data-testid="metric-container"] label {
        color: rgba(255, 255, 255, 0.8) !important;
    }
    
    .pricing-section [data-testid="metric-container"] [data-testid="metric-value"] {
        color: white !important;
        font-weight: 700;
    }
    
    [data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .results-header {
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #667eea;
    }
    
    .brand-section {
        background: #ffffff;
        border: 1px solid #e1e5e9;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .brand-section h3 {
        margin-top: 0 !important;
        color: #2c3e50 !important;
        border-bottom: 2px solid #ecf0f1;
        padding-bottom: 0.5rem;
    }
    
    .info-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    
    .success-card {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)



def format_number(num: int) -> str:
    """Format large numbers with K, M suffixes"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)


def safe_get(data: dict, *keys, default="N/A"):
    """Safely get nested dictionary values"""
    try:
        result = data
        for key in keys:
            result = result[key]
        return result if result else default
    except (KeyError, TypeError):
        return default


def format_list(items, max_items=5, separator=", "):
    """Format a list of items with optional truncation"""
    if not items:
        return "None"
    
    if isinstance(items, str):
        return items
    
    # Filter out None and empty values
    filtered_items = [item for item in items if item and item != "None"]
    
    if not filtered_items:
        return "None"
    
    # Capitalize and format items
    formatted_items = [str(item).title() for item in filtered_items]
    
    if len(formatted_items) > max_items:
        return separator.join(formatted_items[:max_items]) + f" (+{len(formatted_items) - max_items} more)"
    
    return separator.join(formatted_items)


async def analyze_instagram_profile(url: str, progress_bar, status_text):
    """Analyze Instagram profile and return pricing information"""
    try:
        # Update progress
        progress_bar.progress(10)
        status_text.text("🔍 Fetching profile information...")
        
        # Get basic profile info
        page_info = await get_instagram_page_info(url)
        page_name = page_info["asset_name"]
        if not page_info:
            return {"error": "Could not fetch profile information"}
        
        progress_bar.progress(30)
        status_text.text("📊 Analyzing posts and engagement...")
        
        # Get posts for engagement calculation
        posts, _ = await get_instagram_post_info(
            page_info["platform_specific_info"]["pk"], 
            n_posts=27
        )
        
        if not posts:
            return {"error": "No posts found for analysis"}
        
        progress_bar.progress(50)
        status_text.text("🎨 Creating content collages...")
        
        # Calculate engagement rate
        follower_count = page_info["follower_count"]
        total_engagement = sum([
            post["like_count"] + post["comment_count"] + post.get("view_count", 0) 
            for post in posts
        ])
        engagement_rate = (total_engagement / len(posts) / follower_count) * 100
        
        # Extract image URLs for content analysis
        image_urls = []
        for post in posts[:27]:  # Limit to 27 posts
            if post.get("media_list"):
                for media in post["media_list"]:
                    if media.get('type') in ['thumbnail', 'image'] and media.get('url'):
                        image_urls.append(media.get('url'))
                        break
        
        progress_bar.progress(70)
        status_text.text("🤖 Analyzing content quality...")
        
        # Create collages for AI analysis
        collages = []
        if image_urls:
            for i in range(0, min(len(image_urls), 27), 9):
                try:
                    collage = await create_collage_from_urls(
                        image_urls[i:i+9],
                        width=900,
                        height=900
                    )
                    collages.append(collage)
                except Exception as e:
                    logging.warning(f"Failed to create collage: {e}")
                    continue
        
        progress_bar.progress(85)
        status_text.text("🎯 Determining content category...")
        
        # Categorize content (premium vs general)
        content_category = "general"  # default
        if collages:
            try:
                analysis = await analyze_asset(page_name,collages)
                if "pricing" in analysis:
                    content_category = analysis["pricing"].get("category", "general")
            except Exception as e:
                logging.warning(f"Classification failed: {e}")
        
        progress_bar.progress(95)
        status_text.text("💰 Calculating pricing...")
        
        # Get pricing classification
        pricing = classify_pricing(follower_count, engagement_rate, content_category)
        
        # Compile results
        result = {
            "profile_info": page_info,
            "engagement_rate": engagement_rate,
            "brand_analysis": analysis,
            "pricing": pricing,
            "posts_analyzed": len(posts),
            "images_found": len(image_urls)
        }
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        return result
        
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}

def main():
    # Header with better styling
    st.markdown("# 📊 Instagram Pricing Analyzer")
    st.markdown("Get accurate pricing estimates for Instagram influencers")
    
    st.markdown("---")
    
    # URL input with better spacing
    st.markdown("### Enter Profile URL")
    url = st.text_input(
        "",
        placeholder="https://www.instagram.com/username/",
        label_visibility="collapsed"
    )
    
    # Analyze button with better styling
    st.markdown("")  # Add some space
    if st.button("🚀 Analyze Profile", type="primary"):
        if not url:
            st.error("Please enter an Instagram URL")
        elif "instagram.com" not in url:
            st.error("Please enter a valid Instagram URL")
        else:
            # Create progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Run analysis
            with st.spinner("Analyzing profile..."):
                result = asyncio.run(analyze_instagram_profile(url, progress_bar, status_text))
            
            # Clear progress indicators
            progress_bar.empty()
            status_text.empty()
            
            # Display results
            if "error" in result:
                st.error(f"❌ {result['error']}")
            else:
                st.session_state.analysis_result = result
                st.success("✅ Analysis completed successfully!")
                st.rerun()
    
        # Display results if available
    if hasattr(st.session_state, 'analysis_result') and st.session_state.analysis_result:
        result = st.session_state.analysis_result
        profile_info = result["profile_info"]
        pricing = result["pricing"]
        brand_analysis = result.get("brand_analysis", {})
        
        # Results section with better styling
        st.markdown('<div class="results-header"><h2>📊 Analysis Results</h2></div>', unsafe_allow_html=True)
        
        # Create main two-column layout
        left_col, right_col = st.columns(2)
        
        # LEFT COLUMN - Profile & Pricing Info
        with left_col:
            st.markdown('<div class="left-column">', unsafe_allow_html=True)
            
            # Profile Overview Section
            st.markdown("### 👤 Profile Overview")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("👥 Followers", format_number(profile_info["follower_count"]))
                st.metric("📝 Posts Analyzed", result["posts_analyzed"])
            with col2:
                st.metric("📈 Engagement Rate", f"{result['engagement_rate']:.2f}%")
                content_category = "General"
                if brand_analysis.get("pricing", {}).get("category"):
                    content_category = brand_analysis["pricing"]["category"].title()
                st.metric("🎨 Content Type", content_category)
            
            st.markdown("---")
            
            # Pricing section
            st.markdown("### 💰 Pricing Estimates")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Minimum Price", f"₹{pricing['min_cost_estimate']:,}")
            with col2:
                st.metric("Maximum Price", f"₹{pricing['max_cost_estimate']:,}")
            
            # Language Analysis
            if brand_analysis:
                lang_data = brand_analysis.get("language", {})
                if lang_data and not lang_data.get("error"):
                    st.markdown("---")
                    st.markdown("### 🌐 Language Analysis")
                    primary_lang = safe_get(lang_data, "primary_language", default="Not specified")
                    st.info(f"**Primary Language:** {primary_lang}")
                    secondary_langs = format_list(safe_get(lang_data, "secondary_languages", default=[]))
                    st.info(f"**Secondary Languages:** {secondary_langs}")
                
                # Location Analysis
                loc_data = brand_analysis.get("location", {})
                if loc_data and not loc_data.get("error"):
                    st.markdown("---")
                    st.markdown("### 📍 Location & Audience")
                    geo_focus = safe_get(loc_data, "geographic_focus", default="Not specified")
                    st.info(f"**Geographic Focus:** {geo_focus}")
                    audience_loc = format_list(safe_get(loc_data, "audience_location", default=[]))
                    st.info(f"**Audience Location:** {audience_loc}")
                
                # Demographics Analysis
                demo_data = brand_analysis.get("target_demographics", {})
                if demo_data and not demo_data.get("error"):
                    st.markdown("---")
                    st.markdown("### 👥 Target Demographics")
                    target_audience = format_list(safe_get(demo_data, "primary_target_audience_segment", default=[]))
                    st.info(f"**Target Audience:** {target_audience}")
                    age_group = safe_get(demo_data, "inferred_age_skew_detailed", default="Not specified")
                    st.info(f"**Age Group:** {age_group}")
                    gender_skew = safe_get(demo_data, "inferred_gender_skew", default="Not specified")
                    st.info(f"**Gender Skew:** {gender_skew}")
                
                # Content Quality & Style
                content_data = brand_analysis.get("content_tags", {})
                if content_data and not content_data.get("error"):
                    st.markdown("---")
                    st.markdown("### ✨ Content Quality & Style")
                    quality = safe_get(content_data, "content_quality", default="Not specified")
                    st.info(f"**Quality Level:** {quality}")
                    safety = safe_get(content_data, "brand_safety", default="Not specified")
                    st.info(f"**Brand Safety:** {safety}")
                    styles = format_list(safe_get(content_data, "content_style", default=[]))
                    st.info(f"**Content Style:** {styles}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # RIGHT COLUMN - Brand Analysis Details
        with right_col:
            st.markdown('<div class="right-column">', unsafe_allow_html=True)
            
            if brand_analysis:
                st.markdown("## 🎯 Brand Analysis")
                
                # Content Tags
                cat_data = brand_analysis.get("categorization_tags", {})
                if cat_data and not cat_data.get("error"):
                    st.markdown("### 🏷️ Content Categories")
                    
                    primary_cat = safe_get(cat_data, "category_primary", default="Not specified")
                    if primary_cat != "Not specified":
                        st.success(f"**Primary Category:** {primary_cat.title()}")
                    else:
                        st.info(f"**Primary Category:** {primary_cat}")
                    
                    secondary_cats = format_list(safe_get(cat_data, "category_secondary", default=[]))
                    st.info(f"**Secondary Categories:** {secondary_cats}")
                    
                    topics = format_list(safe_get(cat_data, "topics", default=[]), max_items=4)
                    st.info(f"**Topics:** {topics}")
                    
                    formats = format_list(safe_get(cat_data, "meme_format", default=[]))
                    st.info(f"**Content Formats:** {formats}")
                    
                    paragraph = safe_get(cat_data, "paragraph", default="")
                    if paragraph and paragraph != "Not specified":
                        st.markdown("**Content Description:**")
                        st.write(paragraph)
                
                # Professional Attributes
                prof_data = brand_analysis.get("professional_attributes", {})
                if prof_data and not prof_data.get("error"):
                    st.markdown("---")
                    st.markdown("### 🎬 Professional Attributes")
                    expertise = safe_get(prof_data, "technical_expertise", default="Not specified")
                    st.info(f"**Technical Expertise:** {expertise}")
                    production = safe_get(prof_data, "production_value", default="Not specified")
                    st.info(f"**Production Value:** {production}")
                
                # Brand Elements
                brand_data = brand_analysis.get("brand_elements", {})
                if brand_data and not brand_data.get("error"):
                    st.markdown("---")
                    st.markdown("### 🎨 Brand Elements")
                    voice = format_list(safe_get(brand_data, "brand_voice", default=[]))
                    st.info(f"**Brand Voice:** {voice}")
                    personal_brand = safe_get(brand_data, "personal_branding", default="Not specified")
                    st.info(f"**Personal Branding:** {personal_brand}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Reset button with better styling
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Analyze Another Profile", use_container_width=True):
                if 'analysis_result' in st.session_state:
                    del st.session_state.analysis_result
                st.rerun()

if __name__ == "__main__":
    main()
