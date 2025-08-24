#!/usr/bin/env python3
"""
Local test script for Browser-Use Web UI
Test the web interface and browser automation locally before deploying
"""

import asyncio
import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        "browser_use",
        "fastapi", 
        "uvicorn",
        "anthropic",
        "playwright"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing.append(package)
    
    if missing:
        print(f"\n💡 Install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    return True

def check_environment():
    """Check environment variables"""
    print("\n🔧 Environment Check:")
    
    # Check AI API keys
    ai_keys = {
        "ANTHROPIC_API_KEY": "Anthropic Claude (Required)",
        "OPENAI_API_KEY": "OpenAI GPT (Optional)",
        "GROQ_API_KEY": "Groq (Optional)"
    }
    
    has_ai_key = False
    for key, desc in ai_keys.items():
        if os.getenv(key):
            print(f"✅ {key} - {desc}")
            has_ai_key = True
        else:
            required = "Required" if "Required" in desc else "Optional"
            print(f"⚠️  {key} - {desc} - {required}")
    
    if not has_ai_key:
        print("\n❌ No AI API keys found!")
        print("At minimum, set ANTHROPIC_API_KEY:")
        print("export ANTHROPIC_API_KEY=your_key_here")
        return False
    
    return True

async def test_browser():
    """Test browser automation"""
    print("\n🌐 Testing Browser Automation:")
    
    try:
        import playwright.async_api as playwright
        
        playwright_instance = await playwright.async_playwright().start()
        browser = await playwright_instance.chromium.launch(headless=True)
        browser_context = await browser.new_context()
        
        page = await browser_context.new_page()
        await page.goto("https://httpbin.org/json")
        
        title = await page.title()
        print(f"✅ Browser test successful - Page title: {title}")
        
        await page.close()
        await browser_context.close()
        await browser.close()
        await playwright_instance.stop()
        
        return True
        
    except Exception as e:
        print(f"❌ Browser test failed: {e}")
        print("💡 Try: playwright install chromium")
        return False

def test_web_server():
    """Test if web server starts successfully"""
    print("\n🌐 Testing Web Server:")
    
    try:
        import uvicorn
        from app import app
        
        print("✅ FastAPI app imported successfully")
        
        # Test basic app creation
        if hasattr(app, 'routes'):
            route_count = len(app.routes)
            print(f"✅ Found {route_count} API routes")
        
        return True
        
    except Exception as e:
        print(f"❌ Web server test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Browser-Use Web UI - Local Testing")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed!")
        return False
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed!")
        return False
    
    # Test browser
    if not await test_browser():
        print("\n❌ Browser test failed!")
        return False
    
    # Test web server
    if not test_web_server():
        print("\n❌ Web server test failed!")
        return False
    
    print("\n🎉 All tests passed!")
    print("\n🚀 Ready to run:")
    print("python app.py")
    print("\nThen visit: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)