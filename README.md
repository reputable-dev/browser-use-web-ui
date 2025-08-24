# Browser-Use Web UI for Reputable Platform

A web-based interface for monitoring and controlling browser automation agents using browser-use library with real-time visual feedback.

## 🌟 Features

### Real-Time Visual Monitoring
- **Live Screenshots**: See exactly what the browser agent is doing
- **Real-time Logs**: Stream of automation actions and decisions
- **WebSocket Updates**: Instant status changes and progress updates
- **Session Management**: Create, start, stop, and monitor multiple automation sessions

### Professional Web Interface
- **Responsive Dashboard**: Works on desktop, tablet, and mobile
- **Session Grid**: Visual overview of all active automation sessions
- **Log Viewer**: Terminal-style log display with color coding
- **Task Management**: Create sessions with custom task descriptions

### Production Ready
- **Railway Deployment**: One-click deployment to Railway
- **Docker Support**: Containerized for consistent deployment
- **Health Checks**: Built-in monitoring and health endpoints
- **Error Handling**: Graceful failure recovery and user feedback

## 🚀 Quick Deployment on Railway

### 1. Deploy to Railway (Recommended)

**Method 1: GitHub Integration**
1. Fork/Clone: `git clone https://github.com/reputable-dev/browser-use-web-ui`
2. Visit [Railway.app](https://railway.app) and create a new project
3. Connect your GitHub repository
4. Railway will automatically detect and deploy the application

**Method 2: Manual Deploy**

```bash
# Clone to your repository
git clone https://your-repo/browser-use-web-ui
cd browser-use-web-ui

# Deploy to Railway
railway login
railway link
railway up
```

### 2. Environment Configuration

Set these environment variables in Railway dashboard:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key
```

### 3. Access Your Deployment

Railway will provide you with a URL like: `https://your-app.railway.app`

## 🏠 Local Development

### Prerequisites
- Python 3.11+
- pip package manager

### Installation

```bash
# Clone the repository
cd browser-use-web-ui

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
python app.py
```

Open http://localhost:8000 in your browser.

## 📖 Usage Guide

### Creating a New Session

1. Click **"New Session"** button
2. Enter a task description:
   ```
   "Visit bunnings.com and search for garden tools, then take a screenshot of the search results"
   ```
3. Click **"Create"**

### Starting Automation

1. Find your session in the dashboard
2. Click **"Start"** button
3. Watch real-time screenshots and logs
4. See the agent make decisions and perform actions

### Example Tasks

**Website Analysis:**
```
"Visit reputable.dev and analyze the main navigation structure, taking notes on the key sections and features highlighted"
```

**Competitive Research:**
```
"Go to trustpilot.com, search for 'Bunnings Warehouse', and analyze the first 10 reviews for sentiment and key themes"
```

**Social Media Monitoring:**
```
"Visit twitter.com, search for #bunnings, and analyze the sentiment of the first 20 tweets"
```

**E-commerce Scraping:**
```
"Visit bunnings.com.au, search for 'outdoor furniture', and collect product names, prices, and ratings from the first page"
```

## 🔧 Integration with Reputable Platform

### Adding Browser-Use to Existing Scrapers

```python
# Add to lib/scrapers/browser-use-scraper.ts
import requests

class BrowserUseIntegration:
    def __init__(self, web_ui_url="https://your-railway-app.railway.app"):
        self.base_url = web_ui_url
    
    async def run_automation_task(self, task_description):
        # Create session
        response = requests.post(f"{self.base_url}/api/sessions", 
                               json={"task": task_description})
        session_id = response.json()["session_id"]
        
        # Start automation
        requests.post(f"{self.base_url}/api/sessions/{session_id}/start")
        
        # Monitor progress via WebSocket or polling
        return session_id
```

### Webhook Integration

Set up webhooks to notify your main application when automation completes:

```python
# Add webhook endpoint to app.py
@app.post("/webhook/completion")
async def automation_complete(session_id: str, result: dict):
    # Send results back to Reputable Platform
    # Store in Convex, trigger next steps, etc.
    pass
```

## 🏗️ Architecture

### Components
- **FastAPI Backend**: REST API and WebSocket server
- **Vue.js Frontend**: Reactive dashboard interface  
- **Browser-Use Agent**: AI-powered browser automation
- **Playwright Browser**: Headless Chrome automation
- **WebSocket Streaming**: Real-time updates

### Data Flow
```
User Creates Task → FastAPI Session → Browser-Use Agent → Playwright Browser
                                          ↓
WebSocket Stream ← Screenshots & Logs ← Real-time Monitoring
```

### Session Lifecycle
1. **Create**: User defines automation task
2. **Initialize**: Browser and AI agent setup
3. **Execute**: Agent performs browser actions
4. **Monitor**: Live screenshots and decision logs
5. **Complete**: Results captured and session closed

## 📊 Monitoring & Health

### Health Check Endpoint
```
GET /health
```
Returns server status and active session count.

### Metrics Tracking
- Active sessions count
- Success/failure rates
- Average task completion time
- Browser resource usage

### Logs and Debugging
- Real-time log streaming via WebSocket
- Session-specific log history
- Browser console output capture
- Screenshot timeline for debugging

## 🔒 Security & Production

### Security Features
- CORS configuration for allowed origins
- Input validation on all endpoints
- Resource cleanup on session termination
- Non-root user execution in Docker

### Production Considerations
- Set `ALLOWED_ORIGINS` for security
- Monitor resource usage (CPU/Memory)
- Implement rate limiting for session creation
- Set up log aggregation for monitoring
- Configure auto-scaling based on session load

### Resource Limits
- Max concurrent sessions: 10 (configurable)
- Session timeout: 30 minutes
- Browser memory limit: 1GB per session
- Screenshot retention: 24 hours

## 🚀 Advanced Configuration

### Custom Browser Settings
```python
# In app.py, modify browser initialization
browser_context = await browser_service.get_browser(
    "chrome",
    headless=True,
    viewport_size=(1920, 1080),
    user_agent="Custom User Agent"
)
```

### AI Model Configuration
```python
# Switch between AI providers
if os.getenv("USE_OPENAI"):
    from openai import OpenAI
    ai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
else:
    from anthropic import Anthropic
    ai_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details.

---

## 🎯 Next Steps

1. **Deploy to Railway**: Use the deploy button above
2. **Set API Keys**: Configure Anthropic API key in Railway
3. **Test Automation**: Create your first browser session
4. **Integrate**: Connect to your Reputable Platform scrapers
5. **Monitor**: Use the real-time dashboard to monitor progress

**Ready to deploy! 🚀**