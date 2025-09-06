CATEGORIZE_PROMPT = """You are an expert social media analyst tasked with classifying Instagram pages as either "premium" or "general" based on their content quality, branding, and overall presentation.

Analyze the provided images/collages from the Instagram page and classify the page based on the following criteria:

**PREMIUM PAGE INDICATORS:**
- **Strong Brand Identity**: Consistent visual theme, color scheme, typography, and design elements across posts
- **Professional Templates**: Uses branded templates, consistent layouts, and high-quality graphic design
- **Community Engagement**: Content that fosters genuine community interaction and discussion
- **Original/Curated Content**: Creates original content or carefully curates high-value content that aligns with their brand
- **Niche Focus**: Specializes in specific topics, industries, or interests rather than generic content
- **High Production Value**: Professional photography, well-designed graphics, thoughtful composition
- **Brand Consistency**: Logo placement, watermarks, or consistent branding elements visible across posts
- **Educational/Valuable Content**: Provides insights, tips, tutorials, or valuable information to their audience

**GENERAL PAGE INDICATORS:**
- **Generic Content**: Primarily reposts memes, viral content, or generic posts without adding unique value
- **Inconsistent Branding**: No clear visual identity, random mix of styles and formats
- **Low Production Value**: Basic image quality, minimal design effort, no consistent aesthetic
- **Meme-focused**: Heavy reliance on trending memes, reaction images, or viral content
- **No Brand Templates**: Posts lack consistent design elements or branded templates
- **Random Content Mix**: Posts about various unrelated topics without a clear niche or focus
- **Minimal Original Creation**: Mostly shares or reposts content from other sources
- **Entertainment-only Focus**: Content designed purely for quick entertainment rather than providing value

**ANALYSIS INSTRUCTIONS:**
1. Examine the visual consistency across the provided images
2. Look for branding elements, templates, and design patterns
3. Assess the content quality and production value
4. Determine if the content serves a specific niche or community
5. Evaluate whether the page demonstrates professional content creation

**IMPORTANT GUIDELINES:**
- Focus on the overall pattern across multiple posts, not individual exceptional posts
- Consider the target audience and content purpose
- A page can have entertaining content and still be premium if it maintains brand consistency and quality
- Look for evidence of intentional content strategy vs. random posting

Based on your analysis, classify the page and provide your response in the following JSON format:

```json
{
"category": "premium" | "general"
}
```

Remember: 
- "premium" = Professional branding, consistent templates, community-focused, high-value content
- "general" = Generic memes, inconsistent branding, random content, low production value

Analyze the provided images carefully and make your classification based on the predominant characteristics you observe."""

BASE_PROMPT_TEMPLATE = """Given the Account's Page give me the following in json format, If Screenshot has no Content put `None` values.
NOTE: The resultant json should be a `*JSON parsable String*`
{}
"""


LANGUAGE_SCHEMA = """{{
"primary_language": <"Hindi", "Hinglish","English", "Tamil", "Telugu", "Bengali", "Marathi", "Punjabi", "Malayalam", "Kannada", "Gujarati", "Urdu", "Odia">,## Select One
"secondary_languages": ["Hindi", "English", "Tamil", "Telugu", "Bengali", "Marathi", "Punjabi", "Malayalam", "Kannada", "Gujarati", "Urdu", "Odia", "Hinglish", "None"] ## Select Many in list
}}"""
## Gives good enough data just with images


LOCATION_SCHEMA = """

NOTE:
  - Pan-India: Content/services primarily target audiences across the entirety of India.
  - Regional Specific: Content/services primarily target a specific Indian state (e.g., Tamil Nadu).
  - Metro Only: Content/services primarily target one or a few specific major Indian metropolitan cities (e.g., Mumbai, Delhi, Bangalore).
  - In audience_location , If Pan-India is selected dont include state/city name 

{{
  "geographic_focus": <"Metro Only", "Regional Specific", "Pan-India">, select only 1 Note: If Metro/Regional selected, specify which city/state in audience_location,
  "audience_location": ["Pan-India", "[State_name]", "[city_name]"] - select 2-3 (give in list format)
}}"""


TARGET_DEMOGRAPHICS_SCHEMA = """
{{
"primary_target_audience_segment": "[select from: Gen Z, Young Millennials , Mature Millennials , Gen X , Baby Boomers , Professionals (e.g., B2B), Parents/Families, Students, Hobbyists, General Public]", // Select one or two most prominent (give in list)

"inferred_age_skew_detailed": < // Select ONLY ONE that best describe the perceived age concentration
    "Teens" // (e.g., 13-17),
    "Young-Adults", // (e.g., 18-35) College age, early career
    "Mid-Career Adults" //((e.g., 35-55)),
    "Seniors" // (e.g., 55+),
    "All Ages",
>,

"inferred_gender_skew": "<Primarily Male, Primarily Female, Balanced>" //select only one Based on content themes, interests often associated with genders
}}
"""
## Gives good enough data just with images
## Doesnt work well with twitter

CATEGORIZATION_TAGS_SCHEMA = """
NOTE: category_primary: The single most specific and dominant topic from your list that describes the core subject of the Page in one word.
      category_secondary: 2-3 broader, related, or contextual topics from your list that add more dimension to the Page. 
      topics: You can add new topics if given topic list is inadequate, make sure to add unique topics (i.e dont add topics which are similar to each other)
{{
"topics": ['fan_pages', 'automotive', 'comedy', 'quotes', 'bollywood','art_design', 'technology', 'music', 'regional_cinema','fashion', 'motivation', 'marketing', 'finance', 'football','lifestyle', 'beauty', 'hollywood', 'entertainment', 'news','business', 'relationships', 'ott', 'gaming', 'photography','cricket', 'family', 'education', 'food', 'travel', 'politics','podcasts', 'sports', 'spirituality' ] 5-6 topics,
"category_primary": 1 primary category from above topics,
"category_secondary": [] 2-3 secondary category from above topics,
"meme_format": ["Image Macros", "Video Memes", "Screenshot Memes", "Multi-panel Comics", "Text-only", "Movie Reference"] 2-3
"paragraph": <2-3 lines describing the qualitative charecteristics of the page in detail>
}}"""

CONTENT_TAGS_SCHEMA = """
Here is the page name : {}, Determine the brand_safety using the page_name and its content, ex: fuddusperm - Edgy, politicalsatires - Controversial etc
{{
"content_style": ["Satirical", "Wholesome", "Edgy/Controversial", "Informative", "Inspirational", "Emotional","Nostalgic", "Dramatic", "Educational", "Aesthetic", "Traditional"] 3-4 topics,
"content_quality": <"Professional Studio", "High-End Creator", "Semi-Pro", "Amateur" select one only>,
"brand_safety": <"Completely Safe", "Generally Safe", "Edgy","Controversial", "Adults Only" select only one>
}}"""

PROFESSIONAL_ATTRIBUTES_SCHEMA = """{{
"technical_expertise": <"Industry Expert", "Certified Professional", "Self-Taught Expert", "Enthusiast", "Beginner", "Not Applicable" select one>,
"production_value": <"Professional Team", "Semi-Pro Setup", "High-End Solo Creator", "Smartphone Only" select one>,
"monetization": "<select from: Sponsored Only, Multiple Streams, Products/Merch, Courses/Education, Consulting/Services>",
"brand_association": "<select from: Exclusive Deals, Multiple Brands, Selective Brands, No Brands, Own Brand Only>"
}}"""
## Professional attributes little tough to get for twitter.

BRAND_ELEMENTS_SCHEMA = """{{
"brand_voice": ["Professional", "Casual", "Educational", "Entertaining", "Inspirational", "Authoritative", "Friendly", "Quirky", "Sarcastic", "Wholesome" ] select 2 - 3 in list,
"personal_branding": <"Strong Personal Brand", "Business/Product Focus", "Community First", "Cause/Mission Driven", "Celebrity/Influencer", "Expert/Authority", "Lifestyle Brand", "Minimal Branding", "Meme Brand" select 1>
}}"""