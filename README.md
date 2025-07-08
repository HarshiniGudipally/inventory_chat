# SLN AUTOMOBILES - Auto Parts Inventory Management System

A comprehensive inventory management system for automotive spare parts shop built with FastAPI, MongoDB, and OpenAI integration.

## Features

### Core Inventory Management
- ✅ Add, edit, delete auto parts
- ✅ Search and filter inventory
- ✅ Stock level monitoring with alerts
- ✅ CSV export functionality
- ✅ **Image upload support for parts (optional)**
- ✅ **Hover preview for part images**

### Sales & Invoice Management
- ✅ Create sales by scanning barcodes or entering part numbers
- ✅ Automatic inventory updates on sales
- ✅ Invoice generation with tax calculation
- ✅ Invoice management and viewing
- ✅ Dynamic pricing based on customer type (Regular, VIP, Wholesale)

### Expense Management
- ✅ Add and track expenses
- ✅ Categorize expenses
- ✅ Filter expenses by date range
- ✅ Daily/weekly/monthly expense tracking

### Customer Management
- ✅ Add and manage customers
- ✅ Customer information storage

### AI Assistant
- ✅ OpenAI-powered chat assistant
- ✅ Voice input and output support
- ✅ Persistent chat sessions
- ✅ Chat history export
- ✅ Multi-language support

### User Management
- ✅ Role-based access control (Admin/Worker)
- ✅ Secure authentication
- ✅ Session management

### Dashboard & Analytics
- ✅ Real-time inventory statistics
- ✅ Sales and expense analytics
- ✅ Profit tracking
- ✅ Low stock alerts

## Image Storage

**Images are stored in:** `static/images/parts/` directory
- File naming: `{part_number}_{timestamp}.{extension}`
- Supported formats: JPG, PNG, GIF
- Images are optional - parts can be added without images
- Hover over images in the inventory list to see larger previews
- Click images to open full-size modal view

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd inventory_chat
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Fix bcrypt issues (if needed)**
   If you encounter bcrypt version compatibility issues, run:
   ```bash
   python fix_dependencies.py
   ```

4. **Set up environment variables**
   - Copy `env_example.txt` to `.env`
   - Edit `.env` with your actual values:
     - `MONGO_URI`: MongoDB connection string
     - `SECRET_KEY`: Secure random key for JWT
     - `OPENAI_API_KEY`: Your OpenAI API key

5. **Start MongoDB**
   - Ensure MongoDB is running on localhost:27017

6. **Run the application**
   ```bash
   python start.py
   ```

7. **Access the application**
   - Main application: http://localhost:8000
   - Dashboard: http://localhost:8000/dashboard

## Default Users

### Admin User
- Username: `admin`
- Password: `admin123`
- Full access to all features

### Worker User
- Username: `worker`
- Password: `worker123`
- Limited access (no user management, no expense deletion)

## Usage

### Adding Parts
1. Click "Add New Part" from the main page
2. Fill in required information
3. **Optionally upload an image** (JPG, PNG, GIF)
4. Click "Add Part"

### Editing Parts
1. Click "Edit" on any part in the inventory
2. Modify the information as needed
3. **Optionally update the image** - leave empty to keep current image
4. Click "Update Part"

### Image Features
- **Hover Preview**: Hover over any part image to see a larger preview
- **Modal View**: Click on any image to open full-size view
- **Optional Upload**: Images are completely optional for all parts
- **Easy Replacement**: When editing, you can replace images or keep existing ones

### Sales Process
1. Go to Sales page
2. Scan barcode or enter part number
3. Select customer type for pricing
4. Enter quantity
5. Complete sale (automatically updates inventory)

### AI Assistant
1. Go to Chat page
2. Ask questions about inventory, parts, or get recommendations
3. Use voice input/output for hands-free operation
4. Export chat history when needed

## File Structure

```
inventory_chat/
├── main.py                 # Main FastAPI application
├── start.py               # Startup script with dependency checks
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create from env_example.txt)
├── static/
│   ├── images/
│   │   └── parts/         # Part images storage
│   ├── style.css          # Stylesheets
│   └── script.js          # JavaScript functionality
├── templates/             # HTML templates
│   ├── base.html          # Base template
│   ├── index.html         # Inventory listing
│   ├── add_part.html      # Add part form
│   ├── edit_part.html     # Edit part form
│   ├── sales.html         # Sales page
│   ├── chat.html          # AI chat interface
│   └── ...                # Other templates
└── README.md              # This file
```

## API Endpoints

### Inventory Management
- `GET /` - Main inventory page
- `GET /add` - Add part form
- `POST /add` - Add new part
- `GET /edit/{part_id}` - Edit part form
- `POST /edit/{part_id}` - Update part
- `GET /delete/{part_id}` - Delete part
- `GET /export` - Export inventory to CSV

### Sales & Invoices
- `GET /sales` - Sales page
- `POST /api/create-sale` - Create new sale
- `GET /invoices` - List invoices
- `GET /invoice/{invoice_id}` - View invoice

### Expenses
- `GET /expenses` - Expenses page
- `POST /expenses/add` - Add expense
- `GET /expenses/delete/{expense_id}` - Delete expense

### AI Assistant
- `GET /chat` - Chat interface
- `POST /api/chat` - Chat API
- `GET /api/export-chat/{session_id}` - Export chat

### Authentication
- `GET /login` - Login page
- `POST /login` - Login
- `GET /logout` - Logout

## Technologies Used

- **Backend**: FastAPI, Python 3.8+
- **Database**: MongoDB with Motor (async driver)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI**: OpenAI GPT API
- **Authentication**: JWT tokens
- **File Upload**: FastAPI File uploads
- **Voice**: Web Speech API

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License. 