#!/usr/bin/env python3
"""
Startup script for the Super Admin Agent server.

This script provides an easy way to start the agent server with proper configuration.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi',
        'uvicorn', 
        'openai',
        'supabase',
        'pydantic',
        'python-multipart',
        'python-dotenv',
        'httpx',
        'aiofiles',
        'redis',
        'PyPDF2',
        'python-docx',
        'python-pptx',
        'pillow',
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package}")
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r agents/requirements.txt")
        return False
    
    print("✅ All dependencies are installed!")
    return True


def check_environment():
    """Check if environment variables are configured."""
    print("\n🔧 Checking environment configuration...")
    
    required_env_vars = [
        'OPENAI_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_SERVICE_ROLE_KEY',
        'SUPABASE_ANON_KEY',
        'JWT_SECRET'
    ]
    
    missing_vars = []
    
    for var in required_env_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
            print(f"✗ {var}")
        else:
            # Show partial value for security
            display_value = value[:10] + "..." if len(value) > 10 else value
            print(f"✓ {var} = {display_value}")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Create a .env file in the agents/ directory with required values.")
        print("Use agents/env.example as a template.")
        return False
    
    print("✅ Environment configuration looks good!")
    return True


def check_external_services():
    """Check if external services are accessible."""
    print("\n🌐 Checking external services...")
    
    # Check Redis
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
        r = redis.from_url(redis_url)
        r.ping()
        print("✓ Redis connection successful")
    except Exception as e:
        print(f"⚠ Redis connection failed: {str(e)}")
        print("  Redis is optional but recommended for session management")
    
    # Check OpenAI API
    try:
        import openai
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # This would make a test API call in a real scenario
        print("✓ OpenAI API key configured")
    except Exception as e:
        print(f"⚠ OpenAI configuration issue: {str(e)}")
    
    print("✅ External services check completed!")
    return True


def create_directories():
    """Create necessary directories."""
    print("\n📁 Creating directories...")
    
    directories = [
        'uploads',
        'logs'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created directory: {directory}")
        else:
            print(f"✓ Directory exists: {directory}")
    
    return True


def start_server(host="0.0.0.0", port=8001, reload=True, workers=1):
    """Start the FastAPI server."""
    print(f"\n🚀 Starting Super Admin Agent server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Reload: {reload}")
    print(f"   Workers: {workers}")
    print("=" * 50)
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "agents.main:app",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    if workers > 1:
        cmd.extend(["--workers", str(workers)])
    
    # Add log level
    log_level = "debug" if reload else "info"
    cmd.extend(["--log-level", log_level])
    
    try:
        # Change to project root directory
        os.chdir(Path(__file__).parent.parent)
        
        # Start the server
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Server startup failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Start the Super Admin Agent server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    parser.add_argument("--skip-checks", action="store_true", help="Skip dependency checks")
    
    args = parser.parse_args()
    
    print("🤖 Super Admin Agent Server Startup")
    print("=" * 50)
    
    if not args.skip_checks:
        # Run all checks
        if not check_dependencies():
            return False
        
        if not check_environment():
            return False
        
        check_external_services()
        create_directories()
    
    # Start the server
    reload = not args.no_reload
    return start_server(
        host=args.host,
        port=args.port,
        reload=reload,
        workers=args.workers
    )


if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n✅ Server startup completed!")
    else:
        print("\n❌ Server startup failed!")
        print("\nTroubleshooting:")
        print("1. Check that all dependencies are installed")
        print("2. Verify environment variables are set correctly")
        print("3. Ensure external services (Redis, OpenAI) are accessible")
        print("4. Check the logs for detailed error messages")
        
    sys.exit(0 if success else 1)
