#!/bin/bash
# Deploy Browser-Use Web UI to Railway

set -e  # Exit on any error

echo "🚀 Deploying Browser-Use Web UI to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    curl -sSL https://railway.app/install.sh | sh
    echo "✅ Railway CLI installed"
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
fi

echo "📋 Setting up Railway project..."

# Initialize Railway project if needed
if [ ! -f "railway.json" ]; then
    echo "❌ railway.json not found in current directory"
    exit 1
fi

# Check if we're already linked to a Railway project
if ! railway status &> /dev/null; then
    echo "🔗 Creating new Railway project..."
    railway init
fi

echo "🔧 Setting required environment variables..."

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not found in environment"
    echo "Please set it manually in Railway dashboard or export it:"
    echo "export ANTHROPIC_API_KEY=your_key_here"
    echo "Or set it now:"
    read -p "ANTHROPIC_API_KEY: " anthropic_key
    if [ -n "$anthropic_key" ]; then
        railway variables set ANTHROPIC_API_KEY="$anthropic_key"
        echo "✅ ANTHROPIC_API_KEY set"
    fi
else
    railway variables set ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
    echo "✅ ANTHROPIC_API_KEY set from environment"
fi

# Set other optional environment variables
if [ -n "$OPENAI_API_KEY" ]; then
    railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
    echo "✅ OPENAI_API_KEY set"
fi

if [ -n "$GROQ_API_KEY" ]; then
    railway variables set GROQ_API_KEY="$GROQ_API_KEY"
    echo "✅ GROQ_API_KEY set"
fi

# Set production-specific variables
railway variables set PYTHONUNBUFFERED="1"
railway variables set LOG_LEVEL="INFO"
railway variables set BROWSER_TYPE="chromium"
railway variables set HEADLESS="true"

echo "📦 Deploying to Railway..."
railway up

echo "🎉 Deployment complete!"

# Get the deployment URL
if railway domain; then
    echo "🌐 Your Browser-Use Web UI is available at:"
    railway domain | head -1
else
    echo "🌐 Deployment successful! Check your Railway dashboard for the URL."
fi

echo ""
echo "📝 Next steps:"
echo "1. Visit your deployment URL"
echo "2. Create a new browser automation session"
echo "3. Watch your AI agent work in real-time!"
echo ""
echo "🔧 To view logs: railway logs"
echo "📊 To check status: railway status"