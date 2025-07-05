import os
import json
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Request, Form, Depends, status, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv
from openai import OpenAI  # type: ignore
import pandas as pd
import io
import csv
from passlib.context import CryptContext
from jose import JWTError, jwt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from contextlib import asynccontextmanager

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    pass

app = FastAPI(title="SLN AUTOMOBILES INVENTORY", lifespan=lifespan)

# Get current directory for absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Static and templates
app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(MONGO_URI)
db = client['inventory_db']

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# OpenAI
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Sample data for initialization
SAMPLE_PARTS = [
    {
        "part_number": "BOS-001",
        "part_name": "Oil Filter",
        "brand": "Bosch",
        "vehicle_compatibility": "Honda Civic 2018-2023",
        "category": "Filters",
        "quantity_in_stock": 25,
        "minimum_stock_level": 10,
        "unit_price": 12.50,
        "supplier": "AutoZone",
        "location_in_shop": "Shelf A1",
        "condition": "New",
        "warranty_period": 12,
        "created_at": datetime.now()
    },
    {
        "part_number": "NGK-002",
        "part_name": "Spark Plug",
        "brand": "NGK",
        "vehicle_compatibility": "Toyota Camry 2019-2022",
        "category": "Engine",
        "quantity_in_stock": 50,
        "minimum_stock_level": 20,
        "unit_price": 8.75,
        "supplier": "NAPA",
        "location_in_shop": "Rack B2",
        "condition": "New",
        "warranty_period": 6,
        "created_at": datetime.now()
    }
]

# Initialize database with sample data
async def init_db():
    try:
        # Check if parts collection is empty
        count = await db.parts.count_documents({})
        if count == 0:
            await db.parts.insert_many(SAMPLE_PARTS)
            print("Sample data inserted")
    except Exception as e:
        print(f"Database initialization error: {e}")
        print("Make sure MongoDB is running on localhost:27017")

# Authentication functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# Routes
@app.get('/test-static')
async def test_static():
    return {"message": "Static files should be working", "static_dir": STATIC_DIR}

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    try:
        parts = await db.parts.find().to_list(1000)
        return templates.TemplateResponse('index.html', {'request': request, 'parts': parts})
    except Exception as e:
        print(f"Error loading home page: {e}")
        return templates.TemplateResponse('index.html', {'request': request, 'parts': [], 'error': 'Database connection error'})

@app.get('/add', response_class=HTMLResponse)
async def add_part_page(request: Request):
    return templates.TemplateResponse('add_part.html', {'request': request})

@app.post('/add')
async def add_part(
    part_number: str = Form(...),
    part_name: str = Form(...),
    brand: str = Form(...),
    vehicle_compatibility: str = Form(...),
    category: str = Form(...),
    quantity_in_stock: int = Form(...),
    minimum_stock_level: int = Form(...),
    unit_price: float = Form(...),
    supplier: str = Form(...),
    location_in_shop: str = Form(None),
    condition: str = Form("New"),
    warranty_period: str = Form(None)
):
    try:
        # Convert warranty_period to int if provided, otherwise None
        warranty_int = None
        if warranty_period and warranty_period.strip():
            try:
                warranty_int = int(warranty_period)
            except ValueError:
                warranty_int = None
        
        part_data = {
            "part_number": part_number,
            "part_name": part_name,
            "brand": brand,
            "vehicle_compatibility": vehicle_compatibility,
            "category": category,
            "quantity_in_stock": quantity_in_stock,
            "minimum_stock_level": minimum_stock_level,
            "unit_price": unit_price,
            "supplier": supplier,
            "location_in_shop": location_in_shop,
            "condition": condition,
            "warranty_period": warranty_int,
            "created_at": datetime.now()
        }
        
        await db.parts.insert_one(part_data)
        return RedirectResponse(url='/', status_code=303)
    except Exception as e:
        print(f"Error adding part: {e}")
        return RedirectResponse(url='/add?error=Failed to add part', status_code=303)

@app.get('/edit/{part_id}', response_class=HTMLResponse)
async def edit_part_page(request: Request, part_id: str):
    part = await db.parts.find_one({"_id": ObjectId(part_id)})
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return templates.TemplateResponse('edit_part.html', {'request': request, 'part': part})

@app.post('/edit/{part_id}')
async def edit_part(
    part_id: str,
    part_number: str = Form(...),
    part_name: str = Form(...),
    brand: str = Form(...),
    vehicle_compatibility: str = Form(...),
    category: str = Form(...),
    quantity_in_stock: int = Form(...),
    minimum_stock_level: int = Form(...),
    unit_price: float = Form(...),
    supplier: str = Form(...),
    location_in_shop: str = Form(None),
    condition: str = Form("New"),
    warranty_period: str = Form(None)
):
    try:
        # Convert warranty_period to int if provided, otherwise None
        warranty_int = None
        if warranty_period and warranty_period.strip():
            try:
                warranty_int = int(warranty_period)
            except ValueError:
                warranty_int = None
        
        part_data = {
            "part_number": part_number,
            "part_name": part_name,
            "brand": brand,
            "vehicle_compatibility": vehicle_compatibility,
            "category": category,
            "quantity_in_stock": quantity_in_stock,
            "minimum_stock_level": minimum_stock_level,
            "unit_price": unit_price,
            "supplier": supplier,
            "location_in_shop": location_in_shop,
            "condition": condition,
            "warranty_period": warranty_int,
            "updated_at": datetime.now()
        }
        
        await db.parts.update_one({"_id": ObjectId(part_id)}, {"$set": part_data})
        return RedirectResponse(url='/', status_code=303)
    except Exception as e:
        print(f"Error editing part: {e}")
        return RedirectResponse(url=f'/edit/{part_id}?error=Failed to update part', status_code=303)

@app.get('/delete/{part_id}')
async def delete_part(part_id: str):
    await db.parts.delete_one({"_id": ObjectId(part_id)})
    return RedirectResponse(url='/', status_code=303)

@app.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})

@app.post('/login')
async def login(
    username: str = Form(...),
    password: str = Form(...)
):
    # For demo purposes, accept any login
    # In production, you should verify against database
    access_token = create_access_token(data={"sub": username})
    response = RedirectResponse(url='/', status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get('/logout')
async def logout():
    response = RedirectResponse(url='/', status_code=303)
    response.delete_cookie(key="access_token")
    return response

@app.get('/chat', response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse('chat.html', {'request': request})

@app.post('/api/chat')
async def chat_api(request: Request):
    try:
        data = await request.json()
        user_message = data.get('message', '')
        language = data.get('language', 'en-US')
        
        # Get inventory data for context
        parts = await db.parts.find().to_list(1000)
        inventory_context = "Inventory data:\n"
        for part in parts:
            inventory_context += f"- {part['part_name']} (Part #: {part['part_number']}, Brand: {part['brand']}, "
            inventory_context += f"Compatibility: {part['vehicle_compatibility']}, Category: {part['category']}, "
            inventory_context += f"Stock: {part['quantity_in_stock']}, Min Stock: {part['minimum_stock_level']}, "
            inventory_context += f"Price: ${part['unit_price']}, Supplier: {part['supplier']})\n"
        
        # Create system message
        system_message = f"""You are an AI assistant for SLN AUTOMOBILES spare parts shop. 
        You have access to the following inventory data. Answer questions about parts, availability, pricing, and compatibility.
        Be helpful and provide accurate information based on the data provided.
        
        {inventory_context}"""
        
        # Get response from OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        return JSONResponse({'response': ai_response})
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/dashboard', response_class=HTMLResponse)
async def dashboard(request: Request):
    # Get statistics
    total_parts = await db.parts.count_documents({})
    low_stock_parts = await db.parts.count_documents({"$expr": {"$lt": ["$quantity_in_stock", "$minimum_stock_level"]}})
    
    # Get total inventory value
    pipeline = [
        {"$project": {"value": {"$multiply": ["$quantity_in_stock", "$unit_price"]}}},
        {"$group": {"_id": None, "total_value": {"$sum": "$value"}}}
    ]
    result = await db.parts.aggregate(pipeline).to_list(1)
    total_value = result[0]['total_value'] if result else 0
    
    # Get category distribution
    category_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    categories = await db.parts.aggregate(category_pipeline).to_list(100)
    
    # Get low stock items
    low_stock_items = await db.parts.find(
        {"$expr": {"$lt": ["$quantity_in_stock", "$minimum_stock_level"]}}
    ).to_list(100)
    
    return templates.TemplateResponse('dashboard.html', {
        'request': request,
        'total_parts': total_parts,
        'low_stock_parts': low_stock_parts,
        'total_value': total_value,
        'categories': categories,
        'low_stock_items': low_stock_items
    })

@app.get('/export')
async def export_inventory():
    parts = await db.parts.find().to_list(1000)
    
    # Convert to DataFrame
    df = pd.DataFrame(parts)
    if not df.empty:
        df['_id'] = df['_id'].astype(str)
        df['created_at'] = df['created_at'].astype(str)
    
    # Create CSV
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventory.csv"}
    )

@app.get('/api/search')
async def search_parts(q: str):
    try:
        if not q or len(q.strip()) < 2:
            return JSONResponse({'parts': []})
        
        parts = await db.parts.find({
            "$or": [
                {"part_name": {"$regex": q.strip(), "$options": "i"}},
                {"part_number": {"$regex": q.strip(), "$options": "i"}},
                {"brand": {"$regex": q.strip(), "$options": "i"}},
                {"vehicle_compatibility": {"$regex": q.strip(), "$options": "i"}}
            ]
        }).to_list(100)
        
        return JSONResponse({'parts': parts})
    except Exception as e:
        print(f"Search error: {e}")
        return JSONResponse({'parts': [], 'error': 'Search failed'})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 