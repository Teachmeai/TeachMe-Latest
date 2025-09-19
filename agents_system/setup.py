#!/usr/bin/env python3
"""
Complete setup script for Super Admin Agent system.

This script handles:
1. Environment setup
2. Dependency installation  
3. Database schema creation
4. Configuration validation
5. Server startup
"""

import os
import sys
import subprocess
import asyncio
import shutil
from pathlib import Path

def print_header():
    """Print setup header."""
    print("""
🤖 SUPER ADMIN AGENT SYSTEM SETUP
================================

This script will set up the complete Super Admin Agent system for TeachMe AI.

Features:
- Platform management via natural language
- Course assistant creation and management
- File upload and vector processing
- Chat sessions with persistence
- Role-based access control

Let's get started!
""")

def check_python_version():
    """Check Python version."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing dependencies...")
    
    requirements_file = Path("agents/requirements.txt")
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        # Upgrade pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)], 
                              check=True, capture_output=True, text=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Dependency installation failed: {e}")
        print(f"   Error output: {e.stderr}")
        return False

def setup_environment():
    """Set up environment file."""
    print("\n🔧 Setting up environment...")
    
    env_example = Path("agents/env.example")
    env_file = Path("agents/.env")
    
    if not env_example.exists():
        print("❌ env.example file not found")
        return False
    
    if env_file.exists():
        overwrite = input("⚠️  .env file already exists. Overwrite? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("✅ Using existing .env file")
            return True
    
    # Copy example to .env
    shutil.copy2(env_example, env_file)
    print("✅ Created .env file from template")
    
    print("\n📝 Please edit agents/.env with your actual configuration:")
    print("   - OPENAI_API_KEY: Your OpenAI API key")
    print("   - SUPABASE_URL: Your Supabase project URL")  
    print("   - SUPABASE_SERVICE_ROLE_KEY: Your Supabase service role key")
    print("   - SUPABASE_ANON_KEY: Your Supabase anon key")
    print("   - JWT_SECRET: Your JWT secret from the main backend")
    
    edit_now = input("\nWould you like to edit the .env file now? (y/N): ").lower().strip()
    if edit_now == 'y':
        # Try to open with default editor
        try:
            if sys.platform == "win32":
                os.startfile(str(env_file))
            elif sys.platform == "darwin":
                subprocess.run(["open", str(env_file)])
            else:
                subprocess.run(["xdg-open", str(env_file)])
                
            input("Press Enter when you've finished editing the .env file...")
        except Exception:
            print(f"Please manually edit: {env_file}")
            input("Press Enter when done...")
    
    return True

def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        "agents/uploads",
        "agents/logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    return True

def validate_configuration():
    """Validate the configuration."""
    print("\n✅ Validating configuration...")
    
    # Check if .env file exists and has required variables
    env_file = Path("agents/.env")
    if not env_file.exists():
        print("❌ .env file not found")
        return False
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv(env_file)
    
    required_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL', 
        'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_ANON_KEY',
        'JWT_SECRET'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("   Please edit agents/.env and add these variables")
        return False
    
    print("✅ Configuration validation passed")
    return True

async def setup_database():
    """Set up the database schema."""
    print("\n🗄️  Setting up database schema...")
    
    try:
        # Import and run database setup
        sys.path.append("agents")
        from setup_database import setup_database
        
        success = await setup_database()
        if success:
            print("✅ Database schema created successfully")
        else:
            print("❌ Database setup failed")
        
        return success
        
    except Exception as e:
        print(f"❌ Database setup error: {str(e)}")
        return False

def create_startup_scripts():
    """Create convenient startup scripts."""
    print("\n📜 Creating startup scripts...")
    
    # Windows batch file
    bat_content = """@echo off
echo Starting Super Admin Agent Server...
cd /d "%~dp0"
python agents/start_agent_server.py
pause
"""
    
    with open("start_agent_server.bat", "w") as f:
        f.write(bat_content)
    
    # Unix shell script
    sh_content = """#!/bin/bash
echo "Starting Super Admin Agent Server..."
cd "$(dirname "$0")"
python3 agents/start_agent_server.py
"""
    
    with open("start_agent_server.sh", "w") as f:
        f.write(sh_content)
    
    # Make shell script executable
    try:
        os.chmod("start_agent_server.sh", 0o755)
    except:
        pass
    
    print("✅ Created startup scripts")
    return True

def run_tests():
    """Run basic system tests."""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test imports
        sys.path.append("agents")
        
        print("   Testing imports...")
        from config.settings import settings
        from utils.openai_client import openai_client
        from utils.supabase_client import supabase_client
        
        print("✅ All imports successful")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def print_completion_info():
    """Print completion information."""
    print("""
🎉 SETUP COMPLETED SUCCESSFULLY!

Your Super Admin Agent system is ready to use.

📋 QUICK START:

1. Start the server:
   Windows: double-click start_agent_server.bat
   Unix/Mac: ./start_agent_server.sh
   Manual: python agents/start_agent_server.py

2. Access the API documentation:
   http://localhost:8001/docs

3. Test the APIs:
   cd agents/tests
   ./test_apis.sh

📁 IMPORTANT FILES:

- agents/.env               - Configuration file
- agents/main.py           - Main application
- agents/tests/            - Test scripts
- agents/uploads/          - File upload directory

🔧 TESTING:

1. Basic API tests:
   bash agents/tests/test_apis.sh

2. File upload tests:
   bash agents/tests/test_file_upload.sh

3. Workflow tests:
   bash agents/tests/test_super_admin_workflows.sh

📚 DOCUMENTATION:

- API docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc
- README: agents/README.md

🚀 NEXT STEPS:

1. Get a JWT token from your main TeachMe backend
2. Add it to the test scripts
3. Start creating course assistants via natural language!

Happy coding! 🎯
""")

async def main():
    """Main setup function."""
    print_header()
    
    # Step 1: Check Python version
    if not check_python_version():
        return False
    
    # Step 2: Install dependencies
    if not install_dependencies():
        return False
    
    # Step 3: Set up environment
    if not setup_environment():
        return False
    
    # Step 4: Create directories
    if not create_directories():
        return False
    
    # Step 5: Validate configuration
    if not validate_configuration():
        return False
    
    # Step 6: Set up database
    setup_db = input("\nWould you like to set up the database schema now? (y/N): ").lower().strip()
    if setup_db == 'y':
        if not await setup_database():
            print("⚠️  Database setup failed, but you can run it later with:")
            print("   python agents/setup_database.py")
    
    # Step 7: Create startup scripts
    if not create_startup_scripts():
        return False
    
    # Step 8: Run tests
    if not run_tests():
        return False
    
    # Step 9: Print completion info
    print_completion_info()
    
    # Step 10: Offer to start server
    start_now = input("Would you like to start the server now? (y/N): ").lower().strip()
    if start_now == 'y':
        print("\n🚀 Starting server...")
        try:
            subprocess.run([sys.executable, "agents/start_agent_server.py"], check=True)
        except KeyboardInterrupt:
            print("\n✅ Server stopped")
        except Exception as e:
            print(f"\n❌ Server error: {e}")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed with error: {e}")
        sys.exit(1)
