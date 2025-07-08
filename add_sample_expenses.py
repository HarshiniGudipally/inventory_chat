import asyncio
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Sample expense data
SAMPLE_EXPENSES = [
    {
        "description": "Office Rent",
        "amount": 1500.00,
        "category": "rent",
        "date": datetime.now() - timedelta(days=5),
        "payment_method": "bank_transfer",
        "notes": "Monthly office rent payment",
        "created_at": datetime.now() - timedelta(days=5)
    },
    {
        "description": "Electricity Bill",
        "amount": 250.00,
        "category": "utilities",
        "date": datetime.now() - timedelta(days=3),
        "payment_method": "card",
        "notes": "Monthly electricity bill",
        "created_at": datetime.now() - timedelta(days=3)
    },
    {
        "description": "Inventory Purchase - Oil Filters",
        "amount": 500.00,
        "category": "inventory",
        "date": datetime.now() - timedelta(days=1),
        "payment_method": "cash",
        "notes": "Bulk purchase of oil filters from supplier",
        "created_at": datetime.now() - timedelta(days=1)
    },
    {
        "description": "Employee Salary",
        "amount": 2000.00,
        "category": "salary",
        "date": datetime.now(),
        "payment_method": "bank_transfer",
        "notes": "Monthly salary payment for technician",
        "created_at": datetime.now()
    },
    {
        "description": "Vehicle Maintenance",
        "amount": 300.00,
        "category": "maintenance",
        "date": datetime.now() - timedelta(days=10),
        "payment_method": "card",
        "notes": "Service van maintenance and repairs",
        "created_at": datetime.now() - timedelta(days=10)
    }
]

async def add_sample_expenses():
    """Add sample expense data for testing"""
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
        expenses_collection = db.expenses
        
        # Check current expense count
        current_count = await expenses_collection.count_documents({})
        print(f"Current expenses count: {current_count}")
        
        if current_count == 0:
            # Add sample expenses
            await expenses_collection.insert_many(SAMPLE_EXPENSES)
            print("✅ Sample expenses data inserted")
        else:
            print("✅ Expenses collection already has data")
        
        # Show all expenses
        all_expenses = await expenses_collection.find().sort("date", -1).to_list(100)
        print(f"\nTotal expenses in database: {len(all_expenses)}")
        
        for expense in all_expenses:
            print(f"- {expense['date'].strftime('%Y-%m-%d')}: {expense['description']} - ${expense['amount']:.2f}")
        
        # Close connection
        client.close()
        print("\n✅ Sample expenses added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding sample expenses: {e}")

if __name__ == "__main__":
    asyncio.run(add_sample_expenses()) 