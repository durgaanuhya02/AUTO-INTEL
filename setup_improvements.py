#!/usr/bin/env python3
"""
Setup script for enterprise system improvements
"""
import os
import subprocess
import sys

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error running command: {command}")
            print(f"Error output: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Exception running command {command}: {e}")
        return False

def main():
    print("🚀 Setting up Enterprise System Improvements...")
    
    # Check if we're in the right directory
    if not os.path.exists('frontend') or not os.path.exists('backend'):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Install backend dependencies
    print("\n📦 Installing backend dependencies...")
    if not run_command("pip install -r requirements.txt", cwd="backend"):
        print("❌ Failed to install backend dependencies")
        sys.exit(1)
    
    # Install frontend dependencies
    print("\n📦 Installing frontend dependencies...")
    if not run_command("npm install", cwd="frontend"):
        print("❌ Failed to install frontend dependencies")
        sys.exit(1)
    
    # Create necessary directories
    print("\n📁 Creating necessary directories...")
    directories = [
        "backend/uploads",
        "backend/models",
        "backend/logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Set up environment files
    print("\n🔧 Setting up environment files...")
    
    # Copy .env.example to .env if it doesn't exist
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            run_command("copy .env.example .env" if os.name == 'nt' else "cp .env.example .env")
            print("✅ Created .env file from .env.example")
        else:
            print("⚠️  No .env.example file found")
    
    if not os.path.exists('backend/.env'):
        if os.path.exists('backend/.env.example'):
            run_command("copy backend\\.env.example backend\\.env" if os.name == 'nt' else "cp backend/.env.example backend/.env")
            print("✅ Created backend/.env file")
        else:
            print("⚠️  No backend/.env.example file found")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Update your .env files with appropriate values")
    print("2. Start Redis server (if using Redis)")
    print("3. Start the backend: cd backend && python main.py")
    print("4. Start the frontend: cd frontend && npm run dev")
    print("5. Access the application at http://localhost:3000")
    
    print("\n🔍 New Features Available:")
    print("• Advanced Analytics Dashboard with ML forecasting")
    print("• Real-time Performance Monitoring")
    print("• Enhanced Error Handling and Notifications")
    print("• Advanced Data Visualization")
    print("• CSV Upload and ML Model Training")
    print("• Enterprise Security Features")
    print("• System Health Monitoring")
    
    print("\n📚 Documentation:")
    print("• See IMPROVEMENTS_SUMMARY.md for detailed feature overview")
    print("• See ENTERPRISE_FIXES.md for technical implementation details")

if __name__ == "__main__":
    main()