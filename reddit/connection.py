from motor.motor_asyncio import AsyncIOMotorClient


async def dbconnection():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017/?readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false')
        client.list_database_names()  # Test the connection
        return client
    except Exception as e:
        raise ConnectionAbortedError(f"Connection failed: {e}")


async def get_event_collection():
    """
    Get the MongoDB collection for event data.

    Returns:
        AsyncIOMotorClient.Collection: The event data collection.
    """
    client = await dbconnection()
    db = client["testdb"]
    collection = db["testcollection"]
    return collection