import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import uuid

load_dotenv()

# Sample data
SAMPLE_CUSTOMERS = [
    {
        "customer_id": "CUST001",
        "name": "John Doe",
        "email": "john.doe@email.com",
        "phone": "+1234567890",
        "address": "123 Main St, City, State 12345",
        "created_at": datetime.now()
    },
    {
        "customer_id": "CUST002", 
        "name": "Jane Smith",
        "email": "jane.smith@email.com",
        "phone": "+1987654321",
        "address": "456 Oak Ave, City, State 12345",
        "created_at": datetime.now()
    }
]

SAMPLE_USERS_DATA = [
    {
        "username": "admin",
        "email": "admin@slnautomobiles.com",
        "password": "admin123",
        "role": "admin",
        "full_name": "System Administrator",
        "is_active": True
    },
    {
        "username": "worker1",
        "email": "worker1@slnautomobiles.com",
        "password": "worker123",
        "role": "worker",
        "full_name": "John Worker",
        "is_active": True
    }
]

def get_password_hash(password):
    """Simple password hashing for initialization"""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

async def init_collections():
    """Initialize missing collections and sample data"""
    try:
        # Get MongoDB URI from environment or use default
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
        print(f"Connecting to: {mongo_uri}")
        
        # Create client
        client = AsyncIOMotorClient(mongo_uri)
        
        # Test connection
        await client.admin.command('ping')
        print("✅ MongoDB connection successful!")
        
        # Get database
        db = client['inventory_db']
        print("✅ Database 'inventory_db' accessible")
        
        # Initialize customers collection
        customers_collection = db.customers
        customer_count = await customers_collection.count_documents({})
        print(f"Customers collection: {customer_count} documents")
        
        if customer_count == 0:
            await customers_collection.insert_many(SAMPLE_CUSTOMERS)
            print("✅ Sample customers data inserted")
        else:
            print("✅ Customers collection already has data")
        
        # Initialize users collection
        users_collection = db.users
        user_count = await users_collection.count_documents({})
        print(f"Users collection: {user_count} documents")
        
        if user_count == 0:
            # Create sample users with proper password hashing
            sample_users = []
            for user_data in SAMPLE_USERS_DATA:
                user = {
                    "username": user_data["username"],
                    "email": user_data["email"],
                    "hashed_password": get_password_hash(user_data["password"]),
                    "role": user_data["role"],
                    "full_name": user_data["full_name"],
                    "is_active": user_data["is_active"],
                    "created_at": datetime.now()
                }
                sample_users.append(user)
            
            await users_collection.insert_many(sample_users)
            print("✅ Sample users data inserted")
        else:
            print("✅ Users collection already has data")
        
        # Initialize invoices collection (empty)
        invoices_collection = db.invoices
        invoice_count = await invoices_collection.count_documents({})
        print(f"Invoices collection: {invoice_count} documents")
        print("✅ Invoices collection ready")
        
        # Initialize sales collection (empty)
        sales_collection = db.sales
        sales_count = await sales_collection.count_documents({})
        print(f"Sales collection: {sales_count} documents")
        print("✅ Sales collection ready")
        
        # Initialize chat_sessions collection (empty)
        chat_sessions_collection = db.chat_sessions
        chat_count = await chat_sessions_collection.count_documents({})
        print(f"Chat sessions collection: {chat_count} documents")
        print("✅ Chat sessions collection ready")
        
        # Close connection
        client.close()
        print("✅ All collections initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing collections: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure MongoDB is running")
        print("2. Check if you have write permissions to the database")
        print("3. Verify the MONGO_URI in your .env file")

if __name__ == "__main__":
    asyncio.run(init_collections()) 