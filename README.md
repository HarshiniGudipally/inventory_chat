# SLN AUTOMOBILES Inventory Management System

A comprehensive inventory management system for automobile spare parts shops with AI-powered multilingual voice assistant support.

## Features

- **Inventory Management**: Add, edit, delete, and track auto parts
- **AI Assistant**: Multilingual voice-enabled chat assistant (Telugu, Hindi, English)
- **Dashboard**: Real-time analytics and low stock alerts
- **Search & Filter**: Quick search through inventory
- **Export**: CSV export functionality
- **Responsive Design**: Mobile-friendly interface

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: MongoDB
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **AI**: OpenAI GPT-3.5-turbo
- **Authentication**: JWT tokens
- **Voice**: Web Speech API

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd agentic_ai
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example environment file
   copy env_example.txt .env
   
   # Edit .env with your actual values
   # Required:
   # - MONGO_URI (default: mongodb://localhost:27017)
   # - SECRET_KEY (generate a secure key)
   # - OPENAI_API_KEY (get from OpenAI)
   ```

4. **Start MongoDB**
   ```bash
   # Make sure MongoDB is running on localhost:27017
   # Or update MONGO_URI in .env to point to your MongoDB instance
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the application**
   - Open your browser and go to `http://localhost:8000`
   - The application will automatically create sample data on first run

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Email Configuration (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Usage

### Inventory Management
- **View Inventory**: See all parts with stock levels and pricing
- **Add Parts**: Use the "Add New Part" button to add inventory items
- **Edit Parts**: Click "Edit" on any part to modify details
- **Delete Parts**: Click "Delete" to remove items from inventory
- **Search**: Use the search bar to find specific parts

### AI Assistant
- **Multilingual Support**: Choose between Telugu, Hindi, and English
- **Voice Input**: Click the microphone button to speak your questions
- **Voice Output**: AI responses are automatically spoken back
- **Example Questions**: Use the provided example buttons for quick queries

### Dashboard
- **Statistics**: View total parts, low stock items, and inventory value
- **Category Distribution**: See how parts are distributed across categories
- **Low Stock Alerts**: Get notified of items that need restocking
- **Quick Actions**: Access common functions from the dashboard

### Export
- **CSV Export**: Download your complete inventory as a CSV file
- **Data Backup**: Use exports for backup and analysis

## API Endpoints

- `GET /` - Main inventory page
- `GET /add` - Add new part form
- `POST /add` - Create new part
- `GET /edit/{id}` - Edit part form
- `POST /edit/{id}` - Update part
- `GET /delete/{id}` - Delete part
- `GET /dashboard` - Analytics dashboard
- `GET /chat` - AI assistant interface
- `POST /api/chat` - AI chat API
- `GET /api/search` - Search parts API
- `GET /export` - Export inventory as CSV

## Sample Data

The application comes with sample auto parts data including:
- Oil filters (Bosch)
- Spark plugs (NGK)
- Various categories and suppliers

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running on localhost:27017
   - Check your MONGO_URI in .env file
   - Verify MongoDB service is started

2. **OpenAI API Errors**
   - Verify your OPENAI_API_KEY is correct
   - Check your OpenAI account has sufficient credits
   - Ensure the API key has proper permissions

3. **Static Files Not Loading**
   - Check that the static/ directory exists
   - Verify file permissions
   - Clear browser cache

4. **Port Already in Use**
   - Change the port in main.py (line 340)
   - Kill existing processes using the port
   - Use a different port number

### Error Logs
- Check the terminal/console for error messages
- Look for specific error codes and messages
- Verify all environment variables are set correctly

## Development

### Project Structure
```
agentic_ai/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── env_example.txt      # Environment variables template
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── add_part.html
│   ├── edit_part.html
│   ├── dashboard.html
│   └── chat.html
├── static/              # Static files
│   ├── style.css
│   └── script.js
└── README.md
```

### Adding New Features
1. Create new routes in `main.py`
2. Add corresponding templates in `templates/`
3. Update static files as needed
4. Test thoroughly before deployment

## Security Considerations

- Change the default SECRET_KEY in production
- Use HTTPS in production environments
- Implement proper user authentication
- Validate all user inputs
- Use environment variables for sensitive data

## License

This project is open source and available under the MIT License.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review error logs
3. Verify all dependencies are installed
4. Ensure MongoDB and environment variables are configured correctly 