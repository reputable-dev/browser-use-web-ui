# Browser-Use Web UI Deployment Guide

## 🚀 Quick Deployment to Railway

### Option 1: One-Click Deploy (Recommended)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/browser-use-web-ui)

### Option 2: Manual Deployment

1. **Clone the repository**
   ```bash
   git clone <your-repo>
   cd browser-use-web-ui
   ```

2. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   # or
   curl -sSL https://railway.app/install.sh | sh
   ```

3. **Login to Railway**
   ```bash
   railway login
   ```

4. **Create and deploy the project**
   ```bash
   railway init
   railway up
   ```

5. **Set environment variables**
   ```bash
   railway variables set ANTHROPIC_API_KEY="your_anthropic_key"
   railway variables set OPENAI_API_KEY="your_openai_key"  # optional
   railway variables set GROQ_API_KEY="your_groq_key"     # optional
   ```

6. **Get your deployment URL**
   ```bash
   railway domain
   ```

## 🌐 Alternative Deployment Options

### Vercel (Static + API Routes)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

### Docker (Any Container Platform)

```bash
# Build the image
docker build -t browser-use-web-ui .

# Run locally
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY="your_key" \
  browser-use-web-ui

# Deploy to any container platform (Render, Fly.io, DigitalOcean, etc.)
```

### Heroku

```bash
# Install Heroku CLI
# Create Heroku app
heroku create browser-use-web-ui

# Add Python buildpack
heroku buildpacks:set heroku/python

# Set environment variables
heroku config:set ANTHROPIC_API_KEY="your_key"

# Deploy
git push heroku main
```

## 🔧 Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Your Anthropic API key for Claude

Optional:
- `OPENAI_API_KEY` - OpenAI API key for GPT models
- `GROQ_API_KEY` - Groq API key for fast inference
- `PORT` - Port to run on (default: 8000)
- `LOG_LEVEL` - Logging level (default: INFO)

## ✅ Deployment Verification

After deployment, verify the application is working:

1. Visit your deployment URL
2. Check health endpoint: `https://your-app.com/health`
3. Create a test session with a simple task
4. Verify real-time screenshots and logs are working

## 🔒 Security Considerations

For production deployment:

1. **Set proper CORS origins**:
   ```python
   ALLOWED_ORIGINS = ["https://your-domain.com"]
   ```

2. **Enable HTTPS**: Most platforms handle this automatically

3. **Rate limiting**: Consider adding rate limiting for session creation

4. **Authentication**: Add authentication for production use

5. **Resource limits**: Set memory and CPU limits to prevent abuse

## 📊 Monitoring

- Health check endpoint: `/health`
- Logs are available through your platform's logging system
- Real-time session monitoring through the web UI
- WebSocket connections for live updates

## 🛠️ Troubleshooting

**Playwright browser issues**:
```bash
# Ensure browsers are installed
playwright install chromium
```

**Memory issues**:
- Increase memory allocation in platform settings
- Limit concurrent sessions
- Implement session cleanup

**WebSocket connection problems**:
- Check CORS settings
- Verify WebSocket support in your deployment platform
- Use WSS for HTTPS deployments

## 🔄 Updates and Maintenance

To update your deployment:

1. Pull latest changes
2. Test locally
3. Deploy using your chosen method
4. Verify functionality

```bash
# For Railway
git push origin main
railway up

# For Vercel  
vercel --prod

# For Docker
docker build -t browser-use-web-ui .
# Push to your container registry
```

---

**✅ Your Browser-Use Web UI is now ready for deployment!**

The application provides:
- Real-time browser automation monitoring
- Live screenshots and logs
- WebSocket streaming for instant updates
- Session management for multiple tasks
- Production-ready containerization