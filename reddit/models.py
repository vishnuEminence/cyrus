from pydantic import BaseModel,Field
from typing import Dict
from connection import get_event_collection
from datetime import datetime,timedelta
from motor.motor_asyncio import AsyncIOMotorCollection



# Define the data models
class EventData(BaseModel):
    category: str
    event_type:str
    sentiment: str
    title: str
    event_description:str
    probability_of_yes: str
    probability_of_no: str
    created_date:datetime
class EventDataResponseModel(BaseModel):
    category: str
    event_type:str
    sentiment: str
    title: str
    event_description:str
    probability_of_yes: str
    probability_of_no: str
    created_date:datetime
    
# Save to database
async def saved_in_db(event_data: EventDataResponseModel):
    try:
        collection = await get_event_collection()
        if collection is None:
            raise RuntimeError("Database connection failed")
        delete_result = await delete_data_before_give_date()
        
        result = await collection.insert_one(event_data.dict())
        return {"status": "success", "inserted_id": str(result.inserted_id)}

    except Exception as e:
        raise RuntimeError(f"Failed to save event data: {e}")



async def delete_data_before_give_date():
    try:
        # Calculate the cutoff date (21 days ago)
        current_date = datetime.now()
        cutoff_date = current_date - timedelta(days=21)

        # Get the MongoDB collection
        collection = await get_event_collection()
        if collection is None:
            raise RuntimeError("Database connection failed")

        result = await collection.delete_many({"created_date": {"$lt": cutoff_date}})
        
        if result.deleted_count > 0:
            return {"status": "success", "deleted_count": result.deleted_count}
        else:
            return {"status": "success", "message": "No old data to delete"}
    
    except Exception as e:
        raise RuntimeError(f"Failed to delete old event data: {e}")



# Fetch data older than 21 days
async def fetch_data_based_on_date():
    try:
        # Calculate the cutoff date
        current_date = datetime.now()
        cutoff_date = current_date - timedelta(days=21)

        # Get the MongoDB collection
        collection = await get_event_collection()
        if collection is None:
            raise RuntimeError("Database connection failed")

        # Query for records older than the cutoff date
        cursor = collection.find({"created_date": {"$lt": cutoff_date}})
        records = await cursor.to_list(length=None)  # Fetch all matching documents

        return {"status": "success", "data": records}
    except Exception as e:
        raise RuntimeError(f"Failed to fetch old event data: {e}")
