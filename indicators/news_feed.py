import pandas as pd
from urllib.parse import urlparse
from urllib.parse import quote  # Add this import
import feedparser  # Requires: pip install feedparser

# Function to fetch UKA-related news from Google News RSS feed
def fetch_google_news():
    query = "UK Carbon Allowance OR UKA OR UK ETS OR linking with EU OR linking emissions trading OR ETS link"
    encoded_query = quote(query)  # Encode the query string to make it URL-safe
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("❌ Failed to fetch news from RSS feed.")
        return pd.DataFrame()

    news_data = []
    for entry in feed.entries[:6]:  # Limit to the 10 most recent articles
        title = entry.title
        link = entry.link
        source = entry.source.title if "source" in entry else "Unknown Source"
        published = entry.published if "published" in entry else "Unknown Date"

        # Append the article data
        news_data.append({
            "title": title,
            "source": source,
            "link": link,
            "published": published
        })

    # Convert to DataFrame
    news_df = pd.DataFrame(news_data)

    # Parse the 'published' column into datetime and sort by date
    news_df["published"] = pd.to_datetime(news_df["published"], errors="coerce")
    news_df = news_df.sort_values(by="published", ascending=False)

    return news_df