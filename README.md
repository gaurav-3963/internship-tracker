# Internship Tracker v4 — Multi-User

## Setup (local testing)

### 1. Install dependencies
pip install -r requirements.txt

### 2. Create .env file
Copy .env.example to .env and fill in your Supabase DATABASE_URL

### 3. Create your admin account
python setup_admin.py

### 4. Run
streamlit run app.py

## Files
- app.py           → Main application (all 3 pages + admin)
- database.py      → PostgreSQL data layer, all queries
- auth.py          → Login page, session management, user management
- export_utils.py  → CSV export ZIP generator
- setup_admin.py   → One-time admin account creation
- requirements.txt → Dependencies
- .env             → Your database credentials (never share or upload)

## Deploy to Streamlit Cloud
1. Push all files EXCEPT .env to GitHub
2. In Streamlit Cloud → App settings → Secrets → add:
   DATABASE_URL = "your-supabase-url"
3. Redeploy
