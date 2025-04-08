import pandas as pd
from urllib.parse import urlparse, quote
import feedparser  # Requires: pip install feedparser
from datetime import datetime, timedelta

def fetch_google_news():
    query = "UK Carbon Allowance OR UKA OR UK ETS OR linking with EU OR linking emissions trading OR ETS link"
    encoded_query = quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("❌ Failed to fetch news from RSS feed.")
        return pd.DataFrame()

    news_data = []
    for entry in feed.entries[:6]:
        title = entry.title
        link = entry.link
        source = entry.source.title if "source" in entry else "Unknown Source"
        published = entry.published if "published" in entry else "Unknown Date"
        description = entry.summary if "summary" in entry else ""

        news_data.append({
            "title": title,
            "source": source,
            "link": link,
            "published": published,
            "description": description
        })

    news_df = pd.DataFrame(news_data)
    news_df["published"] = pd.to_datetime(news_df["published"], errors="coerce")

    # ✅ Filter for past 30 days
    one_month_ago = datetime.now() - timedelta(days=30)
    news_df = news_df[news_df["published"] >= one_month_ago]

    news_df = news_df.sort_values(by="published", ascending=False)
    return news_df

def fetch_uka_players_news():
    # 🎯 Keywords focused on top UKA players and high-emitting industries
    query = (
        "Tata Steel OR British Steel OR Phillips 66 "
        "OR UK oil refining OR UK cement production OR UK combustion of fuels "
    )

    encoded_query = quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    feed = feedparser.parse(rss_url)

    if not feed.entries:
        print("❌ No player-specific news found.")
        return pd.DataFrame()

    news_data = []
    for entry in feed.entries[:8]:  # Fetch top 8 stories
        news_data.append({
            "title": entry.title,
            "link": entry.link,
            "source": entry.source.title if "source" in entry else "Unknown Source",
            "published": entry.published if "published" in entry else "Unknown Date",
            "description": entry.summary if "summary" in entry else ""
        })

    df = pd.DataFrame(news_data)
    df["published"] = pd.to_datetime(df["published"], errors="coerce")
    one_month_ago = datetime.now() - timedelta(days=30)
    df = df[df["published"] >= one_month_ago]
    return df.sort_values("published", ascending=False)
