"""FastAPI entry point. Feature routes and business logic are kept in separate files."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401 - importing registers model tables
from app.api.routes import auth, plants, marketplace, care, dashboard, workspace, orders, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Convenient for the student MVP. Use Alembic migrations for a production release.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="TreeRasa API", version="0.1.0", description="Plant health and sustainable care platform API", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["https://tree-rasa.vercel.app"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])
for router in (auth.router, plants.router, marketplace.router, care.router, dashboard.router, workspace.router, orders.router, admin.router):
    app.include_router(router, prefix="/api")

@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "service": "treerasa-api"}
