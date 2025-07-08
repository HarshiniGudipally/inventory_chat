#!/usr/bin/env python3
"""
Startup script for Auto Parts Inventory System
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('motor', 'motor'),
        ('jinja2', 'jinja2'),
        ('python-dotenv', 'dotenv'),
        ('openai', 'openai'),
        ('pandas', 'pandas'),
        ('python-multipart', 'multipart'),
        ('passlib', 'passlib'),
        ('python-jose', 'jose')
    ]
    
    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install missing packages with:")
        print("   pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are installed")
    return True

def check_env_file():
    """Check if .env file exists"""
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("📝 Creating .env file from template...")
        
        env_example = Path('env_example.txt')
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("✅ .env file created from template")
            print("⚠️  Please edit .env file with your actual values:")
            print("   - MONGO_URI (default: mongodb://localhost:27017)")
            print("   - SECRET_KEY (generate a secure key)")
            print("   - OPENAI_API_KEY (get from OpenAI)")
            return False
        else:
            print("❌ env_example.txt not found")
            return False
    
    print("✅ .env file found")
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        'static/images/parts',
        'static/images/customers'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created/verified")

def check_mongodb():
    """Check if MongoDB is accessible"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import asyncio
        
        async def test_connection():
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            try:
                await client.admin.command('ping')
                return True
            except Exception:
                return False
            finally:
                client.close()
        
        result = asyncio.run(test_connection())
        if result:
            print("✅ MongoDB connection successful")
            return True
        else:
            print("❌ MongoDB connection failed")
            print("💡 Make sure MongoDB is running on localhost:27017")
            return False
    except Exception as e:
        print(f"❌ Error checking MongoDB: {e}")
        return False

def main():
    """Main startup function"""
    print("🚗 SLN AUTOMOBILES INVENTORY")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check environment file
    if not check_env_file():
        print("\n💡 After editing .env file, run this script again")
        sys.exit(1)
    
    # Check MongoDB
    if not check_mongodb():
        print("\n💡 Start MongoDB and run this script again")
        sys.exit(1)
    
    # Create necessary directories
    create_directories()
    
    print("\n🚀 Starting the application...")
    print("📱 Open your browser and go to: http://localhost:8000")
    print("📱 Open your browser and go to: http://localhost:8000/dashboard")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 40)
    
    # Start the application
    try:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 