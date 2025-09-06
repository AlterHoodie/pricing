import streamlit as st
import asyncio
import json
import logging
from typing import Dict, Any

# Import your existing modules
from src.pricing import classify_pricing, get_pricing_from_instagram
from src.services.rapidapi import get_instagram_page_info, get_instagram_post_info
from src.agents import categorize
from src.utils import create_collage_from_urls

# Configure logging
logging.basicConfig(level=logging.INFO)

# Page configuration
st.set_page_config(
    page_title="Instagram Pricing Analyzer",
    page_icon="📊",
    layout="centered"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        max-width: 800px;
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


async def analyze_instagram_profile(url: str, progress_bar, status_text):
    """Analyze Instagram profile and return pricing information"""
    try:
        # Update progress
        progress_bar.progress(10)
        status_text.text("🔍 Fetching profile information...")
        
        # Get basic profile info
        page_info = await get_instagram_page_info(url)
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
                classification = await categorize(collages)
                content_category = classification.get("category", "general")
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
            "content_category": content_category,
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
        
        # Results section with better styling
        st.markdown('<div class="results-header"><h2>📊 Analysis Results</h2></div>', unsafe_allow_html=True)
        
        # Profile metrics in cards
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("👥 Followers", format_number(profile_info["follower_count"]))
            st.metric("🎨 Content Type", result["content_category"].title())
        
        with col2:
            st.metric("📈 Engagement Rate", f"{result['engagement_rate']:.2f}%")
            st.metric("📝 Posts Analyzed", result["posts_analyzed"])
        
        # Pricing section with gradient background
        st.markdown("### 💰 Pricing Estimates")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Minimum Price", f"₹{pricing['min_cost_estimate']:,}")
        with col2:
            st.metric("Maximum Price", f"₹{pricing['max_cost_estimate']:,}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Reset button with better styling
        st.markdown("")  # Add space
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Analyze Another Profile", use_container_width=True):
                if 'analysis_result' in st.session_state:
                    del st.session_state.analysis_result
                st.rerun()

if __name__ == "__main__":
    main()
