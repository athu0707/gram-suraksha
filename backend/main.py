"""
Gram Suraksha App - Main FastAPI Application
Entry point for the backend server
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

from database import engine, Base
from routers import auth, complaints, admin, users

# Create all database tables on startup
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Gram Suraksha API",
    description="Village Issue Reporting System",
    version="1.0.0"
)

# Allow cross-origin requests (needed for frontend-backend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images as static files
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "static")
os.makedirs(frontend_path, exist_ok=True)
# Only mount if directory exists
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
# Register API routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(complaints.router, prefix="/api/complaints", tags=["Complaints"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])


@app.get("/")
async def serve_frontend():
    """Serve the main HTML frontend"""
    return FileResponse(
        os.path.join(os.path.dirname(__file__), "..", "frontend", "templates", "index.html")
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Gram Suraksha is running!"}
