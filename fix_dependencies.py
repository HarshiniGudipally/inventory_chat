#!/usr/bin/env python3
"""
Fix dependency issues for SLN AUTOMOBILES Inventory System
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def main():
    print("🔧 Fixing SLN AUTOMOBILES Inventory System Dependencies")
    print("=" * 50)
    
    # Step 1: Uninstall problematic packages
    print("\n1. Uninstalling problematic packages...")
    packages_to_remove = ["bcrypt", "passlib"]
    for package in packages_to_remove:
        success, output = run_command(f"pip uninstall {package} -y")
        if success:
            print(f"✅ Uninstalled {package}")
        else:
            print(f"⚠️  Could not uninstall {package}: {output}")
    
    # Step 2: Install correct versions
    print("\n2. Installing correct package versions...")
    install_commands = [
        "pip install bcrypt==4.0.1",
        "pip install passlib[bcrypt]==1.7.4"
    ]
    
    for command in install_commands:
        success, output = run_command(command)
        if success:
            print(f"✅ {command}")
        else:
            print(f"❌ {command}: {output}")
    
    # Step 3: Install all requirements
    print("\n3. Installing all requirements...")
    success, output = run_command("pip install -r requirements.txt")
    if success:
        print("✅ All requirements installed successfully")
    else:
        print(f"❌ Error installing requirements: {output}")
    
    # Step 4: Test bcrypt
    print("\n4. Testing bcrypt functionality...")
    test_script = """
import bcrypt
import passlib.context
print("✅ bcrypt import successful")
pwd_context = passlib.context.CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash("test123")
print("✅ Password hashing successful")
verified = pwd_context.verify("test123", hashed)
print("✅ Password verification successful")
"""
    
    success, output = run_command(f'python -c "{test_script}"')
    if success:
        print("✅ bcrypt functionality test passed")
    else:
        print(f"❌ bcrypt test failed: {output}")
    
    print("\n🎉 Dependency fix completed!")
    print("You can now run: python start.py")

if __name__ == "__main__":
    main() 