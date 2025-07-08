import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

async def test_mongodb_connection():
    """Test MongoDB connection and basic operations"""
    try:
        # Get MongoDB URI from environment or use default
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        print(f"Testing connection to: {mongo_uri}")
        
        # Create client
        client = AsyncIOMotorClient(mongo_uri)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Test database access
        db = client['inventory_db']
        print("✅ Database 'inventory_db' accessible")
        
        # Test collections
        collections = ['parts', 'customers', 'users', 'invoices', 'sales', 'expenses']
        for collection_name in collections:
            try:
                collection = db[collection_name]
                count = await collection.count_documents({})
                print(f"✅ Collection '{collection_name}': {count} documents")
            except Exception as e:
                print(f"❌ Collection '{collection_name}': Error - {e}")
        
        # Close connection
        client.close()
        print("✅ Database test completed successfully")
        
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure MongoDB is installed and running")
        print("2. Check if MongoDB service is started")
        print("3. Verify the MONGO_URI in your .env file")
        print("4. Try running: mongod --dbpath /path/to/data/directory")

if __name__ == "__main__":
    asyncio.run(test_mongodb_connection()) 