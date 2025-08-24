#!/usr/bin/env python3
"""
Browser-Use Web UI for Reputable Platform
Visual monitoring of browser automation agents with real-time streaming
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import base64

# FastAPI and WebSocket imports
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Browser-use imports
from browser_use import Agent, Controller
from anthropic import Anthropic
import playwright.async_api as playwright

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BrowserSession:
    """Represents an active browser automation session"""
    session_id: str
    agent: Optional[Agent] = None
    controller: Optional[Controller] = None
    browser: Optional[object] = None
    page: Optional[object] = None
    status: str = "idle"  # idle, running, completed, error
    task: str = ""
    created_at: datetime = None
    logs: List[dict] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.logs is None:
            self.logs = []
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "status": self.status,
            "task": self.task,
            "created_at": self.created_at.isoformat(),
            "logs": self.logs[-50:]  # Last 50 log entries
        }

class BrowserUseWebUI:
    def __init__(self):
        self.app = FastAPI(title="Browser-Use Web UI", version="1.0.0")
        self.sessions: Dict[str, BrowserSession] = {}
        self.active_connections: Dict[str, WebSocket] = {}
        
        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Setup static files
        static_path = Path(__file__).parent / "static"
        static_path.mkdir(exist_ok=True)
        self.app.mount("/static", StaticFiles(directory=static_path), name="static")
        
        # Setup routes
        self.setup_routes()
        
        # Initialize playwright instance
        self.playwright_instance = None
        
    def setup_routes(self):
        """Setup all API routes"""
        
        @self.app.get("/")
        async def dashboard():
            """Serve the main dashboard"""
            return HTMLResponse(self.get_dashboard_html())
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for Railway"""
            return {"status": "healthy", "sessions": len(self.sessions)}
        
        @self.app.get("/api/sessions")
        async def list_sessions():
            """List all browser sessions"""
            return {
                "sessions": [session.to_dict() for session in self.sessions.values()],
                "total": len(self.sessions)
            }
        
        @self.app.post("/api/sessions")
        async def create_session(request: dict):
            """Create a new browser session"""
            task = request.get("task", "")
            if not task:
                raise HTTPException(status_code=400, detail="Task is required")
            
            session_id = str(uuid.uuid4())
            session = BrowserSession(
                session_id=session_id,
                task=task
            )
            
            self.sessions[session_id] = session
            logger.info(f"Created session {session_id} for task: {task}")
            
            return {"session_id": session_id, "status": "created"}
        
        @self.app.post("/api/sessions/{session_id}/start")
        async def start_session(session_id: str):
            """Start browser automation for a session"""
            if session_id not in self.sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session = self.sessions[session_id]
            if session.status == "running":
                raise HTTPException(status_code=400, detail="Session already running")
            
            # Start the browser automation in background
            asyncio.create_task(self._run_browser_automation(session_id))
            
            return {"session_id": session_id, "status": "starting"}
        
        @self.app.delete("/api/sessions/{session_id}")
        async def stop_session(session_id: str):
            """Stop and delete a session"""
            if session_id not in self.sessions:
                raise HTTPException(status_code=404, detail="Session not found")
            
            session = self.sessions[session_id]
            
            # Clean up browser resources
            if session.page:
                try:
                    await session.page.close()
                except:
                    pass
            
            if session.browser:
                try:
                    await session.browser.close()
                except:
                    pass
            
            del self.sessions[session_id]
            
            return {"message": "Session stopped and deleted"}
        
        @self.app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            """WebSocket for real-time session updates"""
            await websocket.accept()
            self.active_connections[session_id] = websocket
            
            try:
                while True:
                    # Keep connection alive and send periodic updates
                    if session_id in self.sessions:
                        session = self.sessions[session_id]
                        await websocket.send_json({
                            "type": "status_update",
                            "data": session.to_dict()
                        })
                    
                    await asyncio.sleep(1)  # Send updates every second
                    
            except WebSocketDisconnect:
                if session_id in self.active_connections:
                    del self.active_connections[session_id]
    
    async def _run_browser_automation(self, session_id: str):
        """Run browser automation for a session"""
        session = self.sessions[session_id]
        session.status = "running"
        
        try:
            await self._log_to_session(session_id, "info", "Starting browser automation...")
            
            # Initialize Anthropic client
            anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            
            # Initialize playwright browser directly
            playwright_instance = await playwright.async_playwright().start()
            browser = await playwright_instance.chromium.launch(headless=True)
            browser_context = await browser.new_context()
            session.browser = browser_context
            
            # Create a new page
            session.page = await browser_context.new_page()
            
            await self._log_to_session(session_id, "info", "Browser initialized successfully")
            
            # Create browser-use controller
            controller = Controller()
            session.controller = controller
            
            # Create browser-use agent
            agent = Agent(
                task=session.task,
                llm=anthropic_client
            )
            session.agent = agent
            
            await self._log_to_session(session_id, "info", f"Starting task: {session.task}")
            
            # Set up real-time monitoring
            async def capture_screenshots():
                """Capture screenshots periodically"""
                while session.status == "running":
                    try:
                        if session.page:
                            screenshot = await session.page.screenshot(type="png")
                            screenshot_b64 = base64.b64encode(screenshot).decode()
                            
                            # Send screenshot to connected clients
                            if session_id in self.active_connections:
                                await self.active_connections[session_id].send_json({
                                    "type": "screenshot",
                                    "data": {
                                        "image": screenshot_b64,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                })
                    except Exception as e:
                        logger.error(f"Screenshot capture error: {e}")
                    
                    await asyncio.sleep(2)  # Screenshot every 2 seconds
            
            # Start screenshot capture in background
            asyncio.create_task(capture_screenshots())
            
            # Run the automation
            result = await agent.run()
            
            session.status = "completed"
            await self._log_to_session(session_id, "success", f"Task completed: {result}")
            
        except Exception as e:
            session.status = "error"
            error_msg = f"Error in browser automation: {str(e)}"
            logger.error(error_msg)
            await self._log_to_session(session_id, "error", error_msg)
        
        finally:
            # Clean up
            if session.page:
                try:
                    await session.page.close()
                except:
                    pass
    
    async def _log_to_session(self, session_id: str, level: str, message: str):
        """Add a log entry to a session and broadcast it"""
        if session_id not in self.sessions:
            return
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        
        self.sessions[session_id].logs.append(log_entry)
        
        # Broadcast to connected WebSocket clients
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json({
                    "type": "log",
                    "data": log_entry
                })
            except:
                pass  # Connection might be closed
    
    def get_dashboard_html(self):
        """Generate the dashboard HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Browser-Use Web UI - Reputable Platform</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        [v-cloak] { display: none; }
        .log-entry { font-family: 'Courier New', monospace; }
        .screenshot-container { max-height: 400px; overflow: auto; }
    </style>
</head>
<body class="bg-gray-100">
    <div id="app" v-cloak class="container mx-auto p-4">
        <header class="bg-white rounded-lg shadow-md p-6 mb-6">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold text-gray-800">Browser-Use Web UI</h1>
                    <p class="text-gray-600">Real-time monitoring of browser automation agents</p>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm">
                        {{ sessions.length }} Sessions
                    </div>
                    <button @click="showCreateDialog = true" 
                            class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                        New Session
                    </button>
                </div>
            </div>
        </header>

        <!-- Create Session Dialog -->
        <div v-if="showCreateDialog" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="bg-white rounded-lg p-6 w-full max-w-md">
                <h3 class="text-xl font-bold mb-4">Create New Session</h3>
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">Task Description</label>
                    <textarea v-model="newSessionTask" 
                              class="w-full border border-gray-300 rounded-lg p-3 h-24"
                              placeholder="Describe what you want the browser agent to do..."></textarea>
                </div>
                <div class="flex justify-end space-x-3">
                    <button @click="showCreateDialog = false" 
                            class="px-4 py-2 text-gray-600 hover:text-gray-800">Cancel</button>
                    <button @click="createSession" 
                            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">Create</button>
                </div>
            </div>
        </div>

        <!-- Sessions Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <div v-for="session in sessions" :key="session.session_id" 
                 class="bg-white rounded-lg shadow-md overflow-hidden">
                
                <!-- Session Header -->
                <div class="bg-gray-50 px-4 py-3 border-b">
                    <div class="flex justify-between items-center">
                        <h3 class="font-semibold text-gray-800 truncate">
                            {{ session.task || 'Untitled Session' }}
                        </h3>
                        <span :class="getStatusClass(session.status)" 
                              class="px-2 py-1 rounded-full text-xs font-medium">
                            {{ session.status }}
                        </span>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">
                        {{ formatTime(session.created_at) }}
                    </p>
                </div>

                <!-- Screenshot Display -->
                <div v-if="screenshots[session.session_id]" class="screenshot-container p-4 bg-gray-900">
                    <img :src="'data:image/png;base64,' + screenshots[session.session_id]" 
                         class="w-full h-auto rounded border" 
                         alt="Live Screenshot">
                    <p class="text-xs text-gray-400 mt-2 text-center">Live View</p>
                </div>

                <!-- Session Logs -->
                <div class="p-4">
                    <h4 class="font-medium text-gray-700 mb-2">Recent Logs</h4>
                    <div class="bg-gray-900 text-green-400 rounded p-3 h-32 overflow-y-auto">
                        <div v-for="log in session.logs.slice(-10)" :key="log.timestamp" 
                             class="log-entry text-xs mb-1">
                            <span class="text-gray-500">{{ formatLogTime(log.timestamp) }}</span>
                            <span :class="getLogLevelClass(log.level)" class="font-medium">
                                [{{ log.level.toUpperCase() }}]
                            </span>
                            {{ log.message }}
                        </div>
                        <div v-if="session.logs.length === 0" class="text-gray-500 text-center">
                            No logs yet...
                        </div>
                    </div>
                </div>

                <!-- Session Actions -->
                <div class="px-4 pb-4 flex justify-between">
                    <button v-if="session.status === 'idle'" 
                            @click="startSession(session.session_id)"
                            class="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700">
                        Start
                    </button>
                    <button v-if="session.status === 'running'" 
                            @click="stopSession(session.session_id)"
                            class="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700">
                        Stop
                    </button>
                    <button @click="deleteSession(session.session_id)"
                            class="bg-gray-600 text-white px-3 py-1 rounded text-sm hover:bg-gray-700">
                        Delete
                    </button>
                </div>
            </div>

            <!-- Empty State -->
            <div v-if="sessions.length === 0" class="col-span-full text-center py-12">
                <div class="text-gray-400">
                    <svg class="mx-auto h-12 w-12 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    <h3 class="text-lg font-medium text-gray-500 mb-2">No active sessions</h3>
                    <p class="text-gray-400 mb-4">Create your first browser automation session</p>
                    <button @click="showCreateDialog = true" 
                            class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
                        Create Session
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        const { createApp } = Vue;

        createApp({
            data() {
                return {
                    sessions: [],
                    screenshots: {},
                    websockets: {},
                    showCreateDialog: false,
                    newSessionTask: '',
                    isLoading: false
                }
            },
            mounted() {
                this.loadSessions();
                setInterval(this.loadSessions, 5000); // Refresh every 5 seconds
            },
            methods: {
                async loadSessions() {
                    try {
                        const response = await fetch('/api/sessions');
                        const data = await response.json();
                        this.sessions = data.sessions;
                        
                        // Setup WebSocket connections for active sessions
                        for (const session of this.sessions) {
                            if (!this.websockets[session.session_id] && session.status === 'running') {
                                this.setupWebSocket(session.session_id);
                            }
                        }
                    } catch (error) {
                        console.error('Failed to load sessions:', error);
                    }
                },
                
                async createSession() {
                    if (!this.newSessionTask.trim()) return;
                    
                    this.isLoading = true;
                    try {
                        const response = await fetch('/api/sessions', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ task: this.newSessionTask })
                        });
                        
                        if (response.ok) {
                            this.showCreateDialog = false;
                            this.newSessionTask = '';
                            await this.loadSessions();
                        }
                    } catch (error) {
                        console.error('Failed to create session:', error);
                    } finally {
                        this.isLoading = false;
                    }
                },
                
                async startSession(sessionId) {
                    try {
                        await fetch(`/api/sessions/${sessionId}/start`, { method: 'POST' });
                        await this.loadSessions();
                        this.setupWebSocket(sessionId);
                    } catch (error) {
                        console.error('Failed to start session:', error);
                    }
                },
                
                async stopSession(sessionId) {
                    try {
                        await fetch(`/api/sessions/${sessionId}`, { method: 'DELETE' });
                        await this.loadSessions();
                        if (this.websockets[sessionId]) {
                            this.websockets[sessionId].close();
                            delete this.websockets[sessionId];
                        }
                    } catch (error) {
                        console.error('Failed to stop session:', error);
                    }
                },
                
                async deleteSession(sessionId) {
                    if (!confirm('Are you sure you want to delete this session?')) return;
                    await this.stopSession(sessionId);
                },
                
                setupWebSocket(sessionId) {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/ws/${sessionId}`;
                    
                    const ws = new WebSocket(wsUrl);
                    
                    ws.onmessage = (event) => {
                        const message = JSON.parse(event.data);
                        
                        if (message.type === 'screenshot') {
                            this.screenshots[sessionId] = message.data.image;
                        } else if (message.type === 'log') {
                            // Update session logs in real-time
                            const session = this.sessions.find(s => s.session_id === sessionId);
                            if (session) {
                                session.logs.push(message.data);
                            }
                        } else if (message.type === 'status_update') {
                            // Update session status
                            const sessionIndex = this.sessions.findIndex(s => s.session_id === sessionId);
                            if (sessionIndex !== -1) {
                                this.sessions[sessionIndex] = message.data;
                            }
                        }
                    };
                    
                    ws.onclose = () => {
                        delete this.websockets[sessionId];
                    };
                    
                    this.websockets[sessionId] = ws;
                },
                
                getStatusClass(status) {
                    const classes = {
                        idle: 'bg-gray-100 text-gray-800',
                        running: 'bg-blue-100 text-blue-800',
                        completed: 'bg-green-100 text-green-800',
                        error: 'bg-red-100 text-red-800'
                    };
                    return classes[status] || classes.idle;
                },
                
                getLogLevelClass(level) {
                    const classes = {
                        info: 'text-blue-400',
                        success: 'text-green-400',
                        error: 'text-red-400',
                        warning: 'text-yellow-400'
                    };
                    return classes[level] || classes.info;
                },
                
                formatTime(timestamp) {
                    return new Date(timestamp).toLocaleString();
                },
                
                formatLogTime(timestamp) {
                    return new Date(timestamp).toLocaleTimeString();
                }
            }
        }).mount('#app');
    </script>
</body>
</html>
        """

# Global app instance
web_ui = BrowserUseWebUI()
app = web_ui.app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )