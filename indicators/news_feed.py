import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urlparse
import google.generativeai as genai  # Requires: pip install google-generativeai

# Function to fetch UKA-related news from Google News
def fetch_google_news():
    query = "UK Carbon Allowance OR UKA OR EU ETS OR UK ETS OR linking with EU OR linking emissions trading OR ETS link"
    url = f"https://news.google.com/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, "html.parser")
    articles = soup.find_all("article")

    news_data = []

    for article in articles:
        anchor = article.find("a", href=True)
        title = anchor.text.strip() if anchor else "No Title"
        link = "https://news.google.com" + anchor["href"][1:] if anchor and anchor["href"].startswith("./") else ""

        source = "Unknown Source"

        # Try to extract domain from full redirect link
        if "google.com" in link:
            parsed = urlparse(link)
            parts = parsed.path.split('/')
            for part in parts:
                if part.startswith("http"):
                    try:
                        domain = urlparse(part).netloc
                        if domain:
                            source = domain.replace("www.", "")
                            break
                    except:
                        pass

        if title != "No Title" and link:
            news_data.append({
                "title": title,
                "source": source,
                "link": link
            })

    return pd.DataFrame(news_data)

# Function to summarize news headlines using Gemini API
def summarize_news_with_gemini(df):
    genai.configure(api_key="YOUR_GEMINI_API_KEY")

    if df.empty:
        return "No news to summarize."

    prompt = "Here are recent UKA-related news headlines:\n"
    for _, row in df.iterrows():
        prompt += f"- {row['title']} ({row['source']})\n"

    prompt += "\nSummarize the key trends or events in 2–3 sentences."

    model = genai.GenerativeModel(model_name="gemini-pro")

    try:
        response = model.generate_content(prompt)
        
        # ✅ Move print statements up
        print("📤 Prompt sent to Gemini:\n", prompt)
        print("📥 Response from Gemini:\n", response.text)

        return response.text.strip() if response.text else "No summary returned."
    except Exception as e:
        return f"❌ Gemini error: {e}"