from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.init_db import init_db
from app.api.routes import auth, profile, products, orders, scans, dashboard

app = FastAPI(title="TreeRasa API", version="1.0.0", description="Agricultural marketplace and plant health platform")
app.add_middleware(CORSMiddleware, allow_origins=settings.allowed_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok", "service": "treerasa-api"}

for router in (auth.router, profile.router, products.router, orders.router, scans.router, dashboard.router):
    app.include_router(router, prefix="/api")
