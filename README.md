# TreeRasa

Full-stack starter for a three-role agricultural platform:
- Farmer: plant scans/history, farm-produce listings, incoming sales/orders, customer details, vendor supplies, reviews, profile.
- Vendor: supply listings, incoming orders/sales, purchases from other sellers, reviews, profile.
- User: scan plants, browse and buy produce/supplies, order/scan history, reviews, profile.
- PostgreSQL stores users, profiles, products, orders, order items, scans, and reviews.
- React + Vite + Tailwind CSS 3, responsive green UI, light/dark theme.

## Requirements
- Python 3.11+ recommended
- PostgreSQL 14+
- Node.js 18+

## 1. Configure PostgreSQL
Create a database and user (adapt credentials to your installation):
```sql
CREATE USER treerasa WITH PASSWORD 'replace_this_password';
CREATE DATABASE treerasa OWNER treerasa;
```

Copy `.env.example` to `backend/.env` and update `DATABASE_URL` and `JWT_SECRET_KEY`.
Do not commit `.env`.

## 2. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
The first run creates missing tables with SQLAlchemy. For a production deployment, use Alembic migrations before changing schemas. Existing tables are not automatically migrated by `create_all()`.

API docs: http://localhost:8000/docs

Register one of the roles `farmer`, `vendor`, or `user` through the UI. The public API intentionally does not allow self-registration as admin.

## 3. Frontend
In another terminal:
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```
Open http://localhost:5173.

## 4. Plant model integration
No ML model/training code is included or retrained. The scan endpoint saves uploaded image bytes in PostgreSQL and records scan history. It returns a clear `model_not_configured` result until you wire your existing inference code in `backend/app/services/inference.py`. Replace only that service's `predict_plant()` implementation with an adapter to your existing wheat, pomegranate, sugarcane, cotton, and PlantVillage models. Keep the response contract stable.

## Important implementation notes
- This is a starter scaffold and should be tested with your local database before production use.
- Product/order operations are backend-authorized; the frontend is not trusted for role permissions.
- Sellers can only view customer contact details for orders containing their own items.
- Purchases from one's own products are rejected.
- Reviews require a delivered order item and are unique per user/product.
- Multi-seller carts are split into separate seller orders at checkout.
- Image uploads are stored in PostgreSQL as bytea fields to satisfy the requirement that app data is persisted in PostgreSQL. For large production deployments, object storage is often more scalable.
- Never expose `DATABASE_URL` or `JWT_SECRET_KEY` in frontend environment variables.
