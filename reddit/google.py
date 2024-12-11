import os
import requests
from dotenv import load_dotenv
from datetime import datetime
import re

# Load environment variables
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
google_client_id = os.getenv("GOOGLE_CSE_ID")

# Define search queries for each category
search_queries = {
    "sports": "upcoming game OR match OR tournament",
    "nba": "upcoming game OR playoffs OR match",
    "soccer": "upcoming match OR tournament OR championship",
    "tennis": "upcoming match OR tournament OR event",
    "concerts": "upcoming concert OR music festival OR event",
    "festival": "upcoming festival OR event OR celebration",
    "movies": "upcoming movie OR release OR premiere",
    "apple": "upcoming product OR event OR launch",
    "android": "upcoming product OR event OR release",
    "cryptocurrency": "upcoming launch OR event OR ICO",
    "politics": "upcoming election OR event OR debate",
    "worldnews": "upcoming summit OR meeting OR event",
    "science": "upcoming experiment OR discovery OR conference",
    "space": "upcoming mission OR launch OR event"
}

def fetch_google_data(search_query):
    """
    Fetch data from Google Custom Search API based on a search query.
    """
    search_url = f"https://www.googleapis.com/customsearch/v1?q={search_query}&key={google_api_key}&cx={google_client_id}"
    response = requests.get(search_url)
    
    if response.status_code == 200:
        results = response.json().get('items', [])
        return results
    else:
        raise Exception(f"Google API error: {response.status_code} - {response.text}")

def extract_future_timeframe(content):
    """
    Check if content mentions future timeframes or dates.
    """
    current_year = datetime.now().year
    future_years = re.findall(rf"\b({current_year}|20[2-9][0-9]|21[0-9][0-9])\b", content)
    future_keywords = ["next week", "next month", "upcoming", "scheduled", "in ", "later this year"]
    
    if future_years or any(kw in content.lower() for kw in future_keywords):
        return True  
    return False

def filter_future_events(results):
    """
    Filter events that mention future timeframes or are relevant to future events.
    """
    current_year = datetime.now().year
    future_events = []
    for result in results:
        snippet = result.get("snippet", "").lower()
        if extract_future_timeframe(snippet):
            future_events.append({
                "title": result.get("title"),
                "link": result.get("link"),
                "snippet": snippet
            })
    return future_events

def main():
    for category, query in search_queries.items():
        print(f"\nFetching data for category: {category}...")
        try:
            # Fetch Google search results
            results = fetch_google_data(query)
            if not results:
                print(f"No results found for category: {category}")
                continue

            # Filter future events from results
            future_events = filter_future_events(results)
            if not future_events:
                print(f"No future events found for category: {category}")
                continue

            # Display filtered future events
            print(f"\nFuture Events for '{category}':")
            for i, event in enumerate(future_events, start=1):
                print(f"{i}. Title: {event['title']}")
                print(f"   Link: {event['link']}")
                print(f"   Snippet: {event['snippet']}\n")

        except Exception as e:
            print(f"Error fetching data for category {category}: {e}")

if __name__ == "__main__":
    main()