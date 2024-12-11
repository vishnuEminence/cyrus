import os
import tweepy
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

# Define search queries for each category
search_queries = {
    "apple": "upcoming product OR event OR launch",
    "Android": "upcoming product OR event OR release",
    "cryptocurrency": "upcoming launch OR event OR ICO",
    "politics": "upcoming election OR event OR debate",
    "worldnews": "upcoming summit OR meeting OR event",
    "science": "upcoming experiment OR discovery OR conference",
    "space": "upcoming mission OR launch OR event"
}

def check_twitter_api():
    try:
        # Set up Twitter authentication using Bearer Token
        client = tweepy.Client(bearer_token=twitter_bearer_token)

        # Loop through the search queries and fetch tweets for each category
        for category, query in search_queries.items():
            print(f"\nSearching for '{category}' tweets...\n")
            try:
                tweets = client.search_recent_tweets(query=query, max_results=10, tweet_fields=["created_at"])

                if tweets.data:
                    # Limit the output to 10 tweets per category
                    for i, tweet in enumerate(tweets.data):
                        print(f"{i+1}. Tweet: {tweet.text}\n   Created At: {tweet.created_at}\n   URL: https://twitter.com/user/status/{tweet.id}\n")
                else:
                    print(f"No tweets found for '{category}'.")
            except tweepy.TooManyRequests as e:
                print("Rate limit exceeded. Waiting for 15 minutes...")
                time.sleep(15 * 1)  # Wait for 15 minutes
                print("Retrying...")
                continue  # Retry the current search after the wait

    except Exception as e:
        print(f"Error with Twitter API: {e}")

# Main function to search using the queries
def main():
    check_twitter_api()

# Run the program
if __name__ == "__main__":
    main()