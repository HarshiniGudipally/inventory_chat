import os
import json
from datetime import datetime, timedelta, date
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
import uuid

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

# Collections
parts_collection = db.parts
sales_collection = db.sales
invoices_collection = db.invoices
expenses_collection = db.expenses
customers_collection = db.customers
users_collection = db.users
chat_sessions_collection = db.chat_sessions

# Security
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# OpenAI
openai_api_key = os.getenv('OPENAI_API_KEY')
openai_client = None
if openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key)
    except Exception as e:
        print(f"Warning: Could not initialize OpenAI client: {e}")
        openai_client = None

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

# Sample customers for initialization
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



# Initialize database with sample data
async def init_db():
    try:
        print("Initializing database...")
        print(f"MongoDB URI: {MONGO_URI}")
        
        # Test database connection
        await client.admin.command('ping')
        print("Database connection successful")
        
        # Check if parts collection is empty
        count = await parts_collection.count_documents({})
        print(f"Parts collection count: {count}")
        if count == 0:
            await parts_collection.insert_many(SAMPLE_PARTS)
            print("Sample parts data inserted")
        
        # Check if customers collection is empty
        customer_count = await customers_collection.count_documents({})
        print(f"Customers collection count: {customer_count}")
        if customer_count == 0:
            await customers_collection.insert_many(SAMPLE_CUSTOMERS)
            print("Sample customers data inserted")
        
        # Check if users collection is empty
        user_count = await users_collection.count_documents({})
        print(f"Users collection count: {user_count}")
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
            print("Sample users data inserted")
        
        # Check invoices collection
        invoice_count = await invoices_collection.count_documents({})
        print(f"Invoices collection count: {invoice_count}")
            
    except Exception as e:
        print(f"Database initialization error: {e}")
        print("Make sure MongoDB is running on localhost:27017")
        print("You may need to install MongoDB or start the MongoDB service")

# Authentication functions
def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def get_password_hash(password):
    try:
        return pwd_context.hash(password)
    except Exception as e:
        print(f"Password hashing error: {e}")
        # Fallback to a simple hash if bcrypt fails
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Sample users for initialization (will be created in init_db)
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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = await users_collection.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

async def get_current_admin_user(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Routes
@app.get('/test-static')
async def test_static():
    return {"message": "Static files should be working", "static_dir": STATIC_DIR}

@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    try:
        parts = await parts_collection.find().to_list(1000)
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
    warranty_period: str = Form(None),
    part_image: UploadFile = File(None)
):
    try:
        # Convert warranty_period to int if provided, otherwise None
        warranty_int = None
        if warranty_period and warranty_period.strip():
            try:
                warranty_int = int(warranty_period)
            except ValueError:
                warranty_int = None
        
        # Handle image upload
        image_filename = None
        if part_image:
            # Create images directory if it doesn't exist
            images_dir = os.path.join(BASE_DIR, "static", "images", "parts")
            os.makedirs(images_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(part_image.filename or "")[1]
            image_filename = f"{part_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            image_path = os.path.join(images_dir, image_filename)
            
            # Save the image
            with open(image_path, "wb") as buffer:
                content = await part_image.read()
                buffer.write(content)
        
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
            "image_filename": image_filename,
            "created_at": datetime.now()
        }
        
        await parts_collection.insert_one(part_data)
        return RedirectResponse(url='/', status_code=303)
    except Exception as e:
        print(f"Error adding part: {e}")
        return RedirectResponse(url='/add?error=Failed to add part', status_code=303)

@app.get('/edit/{part_id}', response_class=HTMLResponse)
async def edit_part_page(request: Request, part_id: str):
    part = await parts_collection.find_one({"_id": ObjectId(part_id)})
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
    warranty_period: str = Form(None),
    part_image: UploadFile = File(None)
):
    try:
        # Convert warranty_period to int if provided, otherwise None
        warranty_int = None
        if warranty_period and warranty_period.strip():
            try:
                warranty_int = int(warranty_period)
            except ValueError:
                warranty_int = None
        
        # Handle image upload
        image_filename = None
        if part_image:
            # Create images directory if it doesn't exist
            images_dir = os.path.join(BASE_DIR, "static", "images", "parts")
            os.makedirs(images_dir, exist_ok=True)
            
            # Generate unique filename
            file_extension = os.path.splitext(part_image.filename or "")[1]
            image_filename = f"{part_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
            image_path = os.path.join(images_dir, image_filename)
            
            # Save the image
            with open(image_path, "wb") as buffer:
                content = await part_image.read()
                buffer.write(content)
        
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
        
        # Only update image if new one is provided
        if image_filename:
            part_data["image_filename"] = image_filename
        
        await parts_collection.update_one({"_id": ObjectId(part_id)}, {"$set": part_data})
        return RedirectResponse(url='/', status_code=303)
    except Exception as e:
        print(f"Error editing part: {e}")
        return RedirectResponse(url=f'/edit/{part_id}?error=Failed to update part', status_code=303)

@app.get('/delete/{part_id}')
async def delete_part(part_id: str):
    await parts_collection.delete_one({"_id": ObjectId(part_id)})
    return RedirectResponse(url='/', status_code=303)

@app.get('/login', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})

@app.post('/login')
async def login(
    username: str = Form(...),
    password: str = Form(...)
):
    # Verify user credentials
    user = await users_collection.find_one({"username": username})
    if not user or not verify_password(password, user["hashed_password"]):
        return RedirectResponse(url='/login?error=Invalid credentials', status_code=303)
    
    if not user.get("is_active", True):
        return RedirectResponse(url='/login?error=Account is disabled', status_code=303)
    
    access_token = create_access_token(data={"sub": username, "role": user["role"]})
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
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Get or create chat session
        session = await chat_sessions_collection.find_one({"session_id": session_id})
        if not session:
            session = {
                "session_id": session_id,
                "messages": [],
                "created_at": datetime.now(),
                "last_updated": datetime.now()
            }
            await chat_sessions_collection.insert_one(session)
        
        # Get inventory data for context
        parts = await parts_collection.find().to_list(1000)
        inventory_context = "Inventory data:\n"
        for part in parts:
            inventory_context += f"- {part['part_name']} (Part #: {part['part_number']}, Brand: {part['brand']}, "
            inventory_context += f"Compatibility: {part['vehicle_compatibility']}, Category: {part['category']}, "
            inventory_context += f"Stock: {part['quantity_in_stock']}, Min Stock: {part['minimum_stock_level']}, "
            inventory_context += f"Price: ${part['unit_price']}, Supplier: {part['supplier']})\n"
        
        # Check if OpenAI client is available
        if not openai_client:
            return JSONResponse({
                'response': f"AI Assistant is currently unavailable. However, I can see you have {len(parts)} parts in your inventory. Please contact support to enable AI features.",
                'session_id': session_id
            })
        
        # Create system message
        system_message = f"""You are an AI assistant for SLN AUTOMOBILES spare parts shop. 
        You have access to the following inventory data. Answer questions about parts, availability, pricing, and compatibility.
        Be helpful and provide accurate information based on the data provided.
        
        {inventory_context}"""
        
        # Build conversation history
        messages = [{"role": "system", "content": system_message}]
        
        # Add previous messages (limit to last 10 for context)
        for msg in session.get("messages", [])[-10:]:
            if "role" in msg and "content" in msg:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Convert to proper format for OpenAI
        openai_messages = []
        for msg in messages:
            if msg["role"] == "system":
                openai_messages.append({"role": "system", "content": msg["content"]})
            elif msg["role"] == "user":
                openai_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                openai_messages.append({"role": "assistant", "content": msg["content"]})
        
        # Get response from OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,  # type: ignore
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        
        # Save messages to session
        session_messages = session.get("messages", [])
        session_messages.append({"role": "user", "content": user_message, "timestamp": datetime.now()})
        session_messages.append({"role": "assistant", "content": ai_response, "timestamp": datetime.now()})
        
        # Keep only last 100 messages
        if len(session_messages) > 100:
            session_messages = session_messages[-100:]
        
        # Update session
        await chat_sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "messages": session_messages,
                    "last_updated": datetime.now()
                }
            }
        )
        
        return JSONResponse({
            'response': ai_response,
            'session_id': session_id
        })
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/dashboard', response_class=HTMLResponse)
async def dashboard(request: Request):
    # Get statistics
    total_parts = await parts_collection.count_documents({})
    low_stock_parts = await parts_collection.count_documents({"$expr": {"$lt": ["$quantity_in_stock", "$minimum_stock_level"]}})
    
    # Get total inventory value
    pipeline = [
        {"$project": {"value": {"$multiply": ["$quantity_in_stock", "$unit_price"]}}},
        {"$group": {"_id": None, "total_value": {"$sum": "$value"}}}
    ]
    result = await parts_collection.aggregate(pipeline).to_list(1)
    total_value = result[0]['total_value'] if result else 0
    
    # Get category distribution
    category_pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    categories = await parts_collection.aggregate(category_pipeline).to_list(100)
    
    # Get low stock items
    low_stock_items = await parts_collection.find(
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
    parts = await parts_collection.find().to_list(1000)
    
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
        
        parts = await parts_collection.find({
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

# ==================== SALES & INVOICE MANAGEMENT ====================

@app.get('/sales', response_class=HTMLResponse)
async def sales_page(request: Request):
    """Sales page for creating new sales/invoices"""
    customers = await customers_collection.find().to_list(100)
    return templates.TemplateResponse('sales.html', {'request': request, 'customers': customers})

@app.get('/api/search-part')
async def search_part_by_barcode(part_number: str, customer_type: str = "regular"):
    """Search part by barcode/part number for sales with dynamic pricing"""
    try:
        part = await parts_collection.find_one({"part_number": part_number})
        if part:
            # Calculate dynamic pricing based on customer type
            base_price = part['unit_price']
            if customer_type == "wholesale":
                final_price = base_price * 0.85  # 15% discount for wholesale
            elif customer_type == "vip":
                final_price = base_price * 0.90  # 10% discount for VIP
            else:
                final_price = base_price  # Regular price
            
            return JSONResponse({
                'found': True,
                'part': {
                    'id': str(part['_id']),
                    'part_number': part['part_number'],
                    'part_name': part['part_name'],
                    'brand': part['brand'],
                    'unit_price': part['unit_price'],
                    'final_price': round(final_price, 2),
                    'quantity_in_stock': part['quantity_in_stock'],
                    'customer_type': customer_type
                }
            })
        else:
            return JSONResponse({'found': False, 'message': 'Part not found'})
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post('/api/create-sale')
async def create_sale(request: Request):
    """Create a new sale/invoice"""
    try:
        data = await request.json()
        customer_id = data.get('customer_id')
        items = data.get('items', [])
        payment_method = data.get('payment_method', 'cash')
        notes = data.get('notes', '')
        
        if not items:
            return JSONResponse({'error': 'No items in sale'}, status_code=400)
        
        # Calculate totals
        subtotal = sum(item['quantity'] * item['unit_price'] for item in items)
        tax_rate = 0.08  # 8% tax rate
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Create invoice
        invoice_data = {
            "invoice_number": invoice_number,
            "customer_id": customer_id,
            "items": items,
            "subtotal": subtotal,
            "tax_rate": tax_rate,
            "tax_amount": tax_amount,
            "total": total,
            "payment_method": payment_method,
            "notes": notes,
            "status": "completed",
            "created_at": datetime.now()
        }
        
        invoice_result = await invoices_collection.insert_one(invoice_data)
        invoice_id = str(invoice_result.inserted_id)
        
        # Update inventory and create sales records
        for item in items:
            part_id = ObjectId(item['part_id'])
            quantity_sold = item['quantity']
            
            # Update inventory
            await parts_collection.update_one(
                {"_id": part_id},
                {"$inc": {"quantity_in_stock": -quantity_sold}}
            )
            
            # Create sales record
            sale_data = {
                "invoice_id": invoice_id,
                "part_id": part_id,
                "part_number": item['part_number'],
                "part_name": item['part_name'],
                "quantity_sold": quantity_sold,
                "unit_price": item['unit_price'],
                "total_price": item['quantity'] * item['unit_price'],
                "sold_at": datetime.now()
            }
            await sales_collection.insert_one(sale_data)
        
        return JSONResponse({
            'success': True,
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'total': total
        })
        
    except Exception as e:
        print(f"Error creating sale: {e}")
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/invoices', response_class=HTMLResponse)
async def invoices_page(request: Request):
    """View all invoices"""
    try:
        invoices = await invoices_collection.find().sort("created_at", -1).to_list(100)
        
        # Get customer details for each invoice
        for invoice in invoices:
            if invoice.get('customer_id'):
                try:
                    customer = await customers_collection.find_one({"customer_id": invoice['customer_id']})
                    invoice['customer_name'] = customer['name'] if customer else 'Unknown'
                except Exception as e:
                    print(f"Error fetching customer for invoice {invoice.get('_id')}: {e}")
                    invoice['customer_name'] = 'Unknown'
        
        return templates.TemplateResponse('invoices.html', {'request': request, 'invoices': invoices})
    except Exception as e:
        print(f"Error loading invoices page: {e}")
        return templates.TemplateResponse('invoices.html', {
            'request': request, 
            'invoices': [], 
            'error': 'Failed to load invoices. Please check database connection.'
        })

@app.get('/invoice/{invoice_id}', response_class=HTMLResponse)
async def view_invoice(request: Request, invoice_id: str):
    """View specific invoice details"""
    try:
        invoice = await invoices_collection.find_one({"_id": ObjectId(invoice_id)})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Get customer details
        customer = None
        if invoice.get('customer_id'):
            try:
                customer = await customers_collection.find_one({"customer_id": invoice['customer_id']})
            except Exception as e:
                print(f"Error fetching customer for invoice {invoice_id}: {e}")
                customer = None
        
        return templates.TemplateResponse('invoice_detail.html', {
            'request': request, 
            'invoice': invoice, 
            'customer': customer
        })
    except Exception as e:
        print(f"Error viewing invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# ==================== EXPENSE MANAGEMENT ====================

@app.get('/expenses', response_class=HTMLResponse)
async def expenses_page(request: Request):
    """Expenses management page"""
    try:
        # Get date filters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Build query
        query = {}
        if start_date and end_date:
            try:
                query["date"] = {
                    "$gte": datetime.strptime(start_date, "%Y-%m-%d"),
                    "$lte": datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
                }
            except ValueError as e:
                print(f"Error parsing date filters: {e}")
                # If date parsing fails, show all expenses
                query = {}
        
        expenses = await expenses_collection.find(query).sort("date", -1).to_list(100)
        
        # Calculate totals with error handling
        total_expenses = 0
        for expense in expenses:
            try:
                total_expenses += expense.get('amount', 0)
            except (TypeError, ValueError) as e:
                print(f"Error calculating expense amount: {e}")
                continue
        
        return templates.TemplateResponse('expenses.html', {
            'request': request, 
            'expenses': expenses,
            'total_expenses': total_expenses,
            'start_date': start_date,
            'end_date': end_date,
            'now': datetime.now(),
            'timedelta': timedelta
        })
    except Exception as e:
        print(f"Error loading expenses page: {e}")
        return templates.TemplateResponse('expenses.html', {
            'request': request, 
            'expenses': [],
            'total_expenses': 0,
            'start_date': None,
            'end_date': None,
            'now': datetime.now(),
            'timedelta': timedelta,
            'error': 'Failed to load expenses. Please check database connection.'
        })

@app.post('/expenses/add')
async def add_expense(
    description: str = Form(...),
    amount: float = Form(...),
    category: str = Form(...),
    date: str = Form(...),
    payment_method: str = Form(...),
    notes: str = Form(None)
):
    """Add new expense"""
    try:
        expense_data = {
            "description": description,
            "amount": amount,
            "category": category,
            "date": datetime.strptime(date, "%Y-%m-%d"),
            "payment_method": payment_method,
            "notes": notes,
            "created_at": datetime.now()
        }
        
        await expenses_collection.insert_one(expense_data)
        return RedirectResponse(url='/expenses', status_code=303)
    except Exception as e:
        print(f"Error adding expense: {e}")
        return RedirectResponse(url='/expenses?error=Failed to add expense', status_code=303)

@app.get('/expenses/delete/{expense_id}')
async def delete_expense(expense_id: str):
    """Delete expense"""
    await expenses_collection.delete_one({"_id": ObjectId(expense_id)})
    return RedirectResponse(url='/expenses', status_code=303)

# ==================== CUSTOMER MANAGEMENT ====================

@app.get('/customers', response_class=HTMLResponse)
async def customers_page(request: Request):
    """Customer management page"""
    customers = await customers_collection.find().sort("created_at", -1).to_list(100)
    return templates.TemplateResponse('customers.html', {'request': request, 'customers': customers})

@app.post('/customers/add')
async def add_customer(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    address: str = Form(...)
):
    """Add new customer"""
    try:
        # Generate customer ID
        customer_id = f"CUST{str(uuid.uuid4())[:6].upper()}"
        
        customer_data = {
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "created_at": datetime.now()
        }
        
        await customers_collection.insert_one(customer_data)
        return RedirectResponse(url='/customers', status_code=303)
    except Exception as e:
        print(f"Error adding customer: {e}")
        return RedirectResponse(url='/customers?error=Failed to add customer', status_code=303)

# ==================== ENHANCED DASHBOARD ====================

@app.get('/api/dashboard-stats')
async def get_dashboard_stats():
    """Get enhanced dashboard statistics"""
    try:
        # Today's date
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        
        # This week
        start_of_week = start_of_day - timedelta(days=today.weekday())
        end_of_week = end_of_day + timedelta(days=6-today.weekday())
        
        # This month
        start_of_month = datetime(today.year, today.month, 1)
        end_of_month = datetime(today.year, today.month + 1, 1) - timedelta(seconds=1)
        
        # Sales statistics
        today_sales = await invoices_collection.find({
            "created_at": {"$gte": start_of_day, "$lte": end_of_day}
        }).to_list(1000)
        
        week_sales = await invoices_collection.find({
            "created_at": {"$gte": start_of_week, "$lte": end_of_week}
        }).to_list(1000)
        
        month_sales = await invoices_collection.find({
            "created_at": {"$gte": start_of_month, "$lte": end_of_month}
        }).to_list(1000)
        
        # Calculate totals
        today_total = sum(sale['total'] for sale in today_sales)
        week_total = sum(sale['total'] for sale in week_sales)
        month_total = sum(sale['total'] for sale in month_sales)
        
        # Expense statistics
        today_expenses = await expenses_collection.find({
            "date": {"$gte": start_of_day, "$lte": end_of_day}
        }).to_list(1000)
        
        week_expenses = await expenses_collection.find({
            "date": {"$gte": start_of_week, "$lte": end_of_week}
        }).to_list(1000)
        
        month_expenses = await expenses_collection.find({
            "date": {"$gte": start_of_month, "$lte": end_of_month}
        }).to_list(1000)
        
        # Calculate expense totals with error handling
        today_expense_total = 0
        week_expense_total = 0
        month_expense_total = 0
        
        for expense in today_expenses:
            try:
                today_expense_total += expense.get('amount', 0)
            except (TypeError, ValueError):
                continue
                
        for expense in week_expenses:
            try:
                week_expense_total += expense.get('amount', 0)
            except (TypeError, ValueError):
                continue
                
        for expense in month_expenses:
            try:
                month_expense_total += expense.get('amount', 0)
            except (TypeError, ValueError):
                continue
        
        return JSONResponse({
            'today_sales': today_total,
            'week_sales': week_total,
            'month_sales': month_total,
            'today_expenses': today_expense_total,
            'week_expenses': week_expense_total,
            'month_expenses': month_expense_total,
            'today_profit': today_total - today_expense_total,
            'week_profit': week_total - week_expense_total,
            'month_profit': month_total - month_expense_total
        })
        
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/api/export-chat/{session_id}')
async def export_chat_to_pdf(session_id: str):
    """Export chat session to PDF"""
    try:
        session = await chat_sessions_collection.find_one({"session_id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Create PDF content
        pdf_content = f"""
        SLN AUTOMOBILES - Chat Session Export
        Session ID: {session_id}
        Created: {session['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
        Last Updated: {session['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}
        
        Chat History:
        """
        
        for i, msg in enumerate(session.get("messages", []), 1):
            timestamp = msg.get("timestamp", session["created_at"]).strftime('%H:%M:%S')
            role = msg.get("role", "unknown").title()
            content = msg.get("content", "")
            pdf_content += f"\n{i}. [{timestamp}] {role}: {content}\n"
        
        # For now, return as text file (PDF generation would require additional libraries)
        return StreamingResponse(
            io.BytesIO(pdf_content.encode()),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename=chat_session_{session_id}.txt"}
        )
        
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 