import requests
from bs4 import BeautifulSoup
import pandas as pd

def fetch_google_news():
    # Define the search query
    query = "UK Carbon Allowance OR UKA OR EU ETS OR UK ETS OR linking with EU OR linking emissions trading OR ETS link"
    url = f"https://news.google.com/search?q={query}&hl=en-US&gl=US&ceid=US%3Aen"

    # Send a GET request to Google News
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Failed to fetch data: {response.status_code}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all article containers
    articles = soup.find_all('article')

    # Placeholder to store the data
    news_data = []

    for article in articles:
        title_tag = article.find('a')
        if title_tag:
            title = title_tag.text
            link = title_tag['href']
            
            # Ensure the link is properly formatted for Google News
            if not link.startswith('http'):
                link = 'https://news.google.com' + link

            # Placeholder for source (if available in another part of the HTML structure)
            source_tag = article.find('span', class_='xQ82C e8fRJf')
            source = source_tag.text if source_tag else 'Unknown Source'

            # Add data to news_data
            news_data.append({
                'title': title,
                'source': source,
                'link': link  # Make sure 'link' is properly set here
            })

    # Return as DataFrame
    return pd.DataFrame(news_data)
