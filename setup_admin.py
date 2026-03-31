"""
Run this ONCE to create your admin account.
python setup_admin.py
"""
from database import init_db, create_user

print("Internship Tracker — Admin Setup")
print("=" * 40)

init_db()
print("Database tables created.")

name     = input("Your full name: ").strip()
email    = input("Your email: ").strip().lower()
password = input("Choose password (min 8 chars): ").strip()
firm     = input("Your firm/company: ").strip()

if len(password) < 8:
    print("Password too short. Must be at least 8 characters.")
    exit(1)

uid, error = create_user(name, email, password, firm, role="admin")
if uid:
    print(f"\nAdmin account created successfully!")
    print(f"Name:  {name}")
    print(f"Email: {email}")
    print(f"Role:  admin")
    print(f"\nYou can now run: streamlit run app.py")
else:
    print(f"\nError: {error}")
