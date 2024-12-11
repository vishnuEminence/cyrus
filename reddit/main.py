import os
import praw
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import re
from datetime import datetime, timedelta
from models import saved_in_db, EventData
import asyncio
import calendar

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")

openai_model = ChatOpenAI(api_key=openai_api_key, model="gpt-4o")

reddit = praw.Reddit(
    client_id=reddit_client_id,
    client_secret=reddit_client_secret,
    user_agent="my-reddit-bot/1.0 (by u/your_reddit_username)"
)

def ingest_reddit_data(subreddit, query, limit):
    posts = []
    subreddit_obj = reddit.subreddit(subreddit)
    for submission in subreddit_obj.search(query, limit=limit):
        posts.append({
            "title": submission.title,
            "content": submission.selftext,
            "url": submission.url
        })
    return posts
   

current_year = datetime.now().year

def extract_future_timeframe(content):
    future_years = re.findall(rf"\b({current_year}|20[2-9][0-9]|21[0-9][0-9])\b", content)
    future_keywords = ["next week", "next month", "upcoming", "scheduled", "in ", "later this year"]
    
    if future_years or any(kw in content.lower() for kw in future_keywords):
        return True
    return False


def filter_future_events(documents):
    current_year = datetime.now().year
    future_events = []
    for doc in documents:
        content = doc["content"].lower()
        # Match events with scheduled or future contexts
        if re.search(rf'\b(upcoming|scheduled|{current_year})\b', content) or \
           re.search(r'\b(on \d{1,2}[a-z]{2}? (january|february|march|april|may|june|july|august|september|october|november|december))\b', content):
            future_events.append(doc)
    return future_events

def validate_future_question(question):
    if re.search(rf"\b({current_year}|20[2-9][0-9]|21[0-9][0-9])\b", question) or "next" in question.lower() or "upcoming" in question.lower():
        return True
    return False



def classify_event(document):
    prompt = PromptTemplate(template="Classify the event of following.\n\nEvent Description and provide only event value not add any discription: {document}")
    message = prompt.format(document=document)
    response = openai_model.invoke(message) 
    return response.content

def analyze_sentiment(document):
    # prompt = PromptTemplate(template="Analyze the sentiment (positive, neutral, or negative) for this event:\n\n{document}")
    prompt = PromptTemplate(template="Provide only the sentiment value (positive, neutral, or negative) for this event:\n\n{document}")
    message = prompt.format(document=document)
    response = openai_model.invoke(message)  
    return response.content



def get_last_day_of_month_or_year(date: datetime):
    # Get last day of the current month
    last_day_of_month = date.replace(day=calendar.monthrange(date.year, date.month)[1])
    
    # Get last day of the year
    last_day_of_year = date.replace(month=12, day=31)
    
    return last_day_of_month, last_day_of_year

# Function to generate the betting question and check the date validity
def generate_question(event_description, event_type, sentiment):
    current_date = datetime.now().date()
    last_day_of_month, last_day_of_year = get_last_day_of_month_or_year(current_date)
    
    # Calculate the future date (current date + 21 days)
    future_date = current_date + timedelta(days=21)
    
    # Convert dates to string
    current_date_str = current_date.strftime('%Y-%m-%d')
    future_date_str = future_date.strftime('%Y-%m-%d')
    last_day_of_month_str = last_day_of_month.strftime('%Y-%m-%d')
    last_day_of_year_str = last_day_of_year.strftime('%Y-%m-%d')
    
    prompt = PromptTemplate(template=f"""
        Create a betting question based on the following event description. The question should:
        - Be specific, fact-based, and tied to measurable outcomes.
        - Avoid vague predictions or generalizations.
        - Be formatted for a Yes/No answer with probabilities, where the sum of the probabilities is 100%.
        - Ensure the question is future-oriented by estimating the event date and validating it against the current date. If the event is in the past, generate a related future-oriented question that reflects the potential outcome or next steps.

        Inputs:
        - Event Description: {event_description}
        - Event Type: {event_type}
        - Sentiment: {sentiment}
        - Current Date: {current_date_str}

        Output:
        - Generated Question: [A realistic, future-oriented, fact-based betting question relevant to the input.]
        - Probability: [Yes %, No %].
    """)

    
    # Format the prompt with the provided data
    message = prompt.format(event_description=event_description, event_type=event_type, sentiment=sentiment, current_date=current_date_str)
    response = openai_model.invoke(message)  # Assuming openai_model.invoke() sends the request and gets the response
    
    data = response.content
    if 'Generated Question:' in data:
        start_index = data.find('Generated Question:') + len('Generated Question:')
        end_index = data.find('Probability:') if 'Probability:' in data else len(data)
        generated_question = data[start_index:end_index].strip()
        
        # Extract probabilities from the response
        match_yes = re.search(r'Yes (\d+%)', data)
        yes_probability = match_yes.group(1) if match_yes else None

        match_no = re.search(r'No (\d+%)', data)
        no_probability = match_no.group(1) if match_no else None

        # Check if the generated question mentions the end of the month or year
        prompt = PromptTemplate(template=f"""
        Given the generated question: '{generated_question}', 
        check if the date, time, or year mentioned in the question falls within the current date ({current_date_str}) 
        and the next 21 days (until {future_date_str}).
        
        Additionally:
        - If the question mentions the end of the month, consider the last day of the current month ({last_day_of_month_str}).
        - If the question mentions the end of the year, consider the last day of the current year ({last_day_of_year_str}).
        
        If the condition is satisfied, return the question; otherwise, return 'No'.
        """)
        
        message = prompt.format(generated_question=generated_question)
        
        # Get the final validation response
        response = openai_model.invoke(message)
        
        if "No" in response.content:
            return "No", None, None,None  
        else:
            return generated_question, yes_probability, no_probability,event_description


async def main():
    subreddits = [
        "sports", "nba", "soccer", "tennis", "concerts", "festival", "movies",
        "apple", "Android", "cryptocurrency", "politics", "worldnews", "science", "space"
    ]
    query = "upcoming OR scheduled OR next week"

    for subreddit in subreddits:
        print(f"\nIngesting data from /r/{subreddit}...")
        try:
            # Step 1: Fetch Reddit documents
            reddit_documents = ingest_reddit_data(subreddit, query, limit=50)
            # print(type(reddit_documents))
            # print(len(reddit_documents))
            # print(f"Document {subreddit} Ends")

            # print()
            
            # print(reddit_documents[1])

            # break

            # Step 2: Filter future events
            future_events = filter_future_events(reddit_documents)
            if not future_events:
                print(f"No future events found in /r/{subreddit}")
                continue

            for doc in future_events:
                try:
                    # Step 3: Process pipeline for event data
                    event_type = classify_event(doc["content"])
                    sentiment = analyze_sentiment(doc["content"])
                    batting_question, yes_probability, no_probability,event_description= generate_question(doc["content"], event_type, sentiment)
                    # Skip if the generated batting question is "No"
                    if batting_question and batting_question != "No":
                        print(batting_question)
                        print(yes_probability)
                        print(no_probability)
                        # print(event_description)
                        # print("Discarded Question: No (Not valid, skipping event)")
                        # continue
                    
                    event_data = EventData(
                        category=subreddit,
                        event_type=event_type,
                        sentiment=sentiment,
                        title=batting_question,
                        event_description=event_description,
                        probability_of_yes=f"{yes_probability}",  
                        probability_of_no=f"{no_probability}",
                        created_date=datetime.now()
                    )
                    
                    save_response = await saved_in_db(event_data)
                    
                    if save_response["status"] == "success":
                        print(f"Event data saved successfully with ID: {save_response['inserted_id']}")

                        if validate_future_question(batting_question):
                            print(f"\nSubreddit: {subreddit}")
                            print(f"Event Type: {event_type}")
                            print(f"Sentiment: {sentiment}")
                            print(f"Generated Betting Question: {batting_question}")
                        else:
                            print(f"Discarded Question: {batting_question} (Not Future-Oriented)")
                    else:
                        print("Failed to save event data")

                except Exception as e:
                    print(f"Error processing event document: {e}")
        
        except Exception as e:
            print(f"Error ingesting data from /r/{subreddit}: {e}")



if __name__ == "__main__":
    asyncio.run(main())