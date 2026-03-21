"""
Creates a demo SQLite database with realistic sample data.
Run this once: python setup_demo_db.py
"""
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "demo.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# --- Users ---
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    plan TEXT NOT NULL,
    signup_date DATE NOT NULL,
    last_active DATE,
    churned INTEGER DEFAULT 0,
    churn_date DATE
)
""")

# --- Orders ---
cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    order_date DATE NOT NULL
)
""")

# --- Products ---
cur.execute("""
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
)
""")

# --- Page Views ---
cur.execute("""
CREATE TABLE IF NOT EXISTS page_views (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    page TEXT NOT NULL,
    view_date DATE NOT NULL,
    duration_seconds INTEGER
)
""")

# --- Support Tickets ---
cur.execute("""
CREATE TABLE IF NOT EXISTS support_tickets (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    subject TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL,
    created_date DATE NOT NULL,
    resolved_date DATE
)
""")

# Generate data
random.seed(42)
first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", "Ivy", "Jack",
               "Karen", "Leo", "Mia", "Nathan", "Olivia", "Paul", "Quinn", "Rita", "Sam", "Tina",
               "Uma", "Victor", "Wendy", "Xander", "Yara", "Zane", "Aria", "Blake", "Cleo", "Derek",
               "Elena", "Felix", "Gina", "Hugo", "Iris", "Joel", "Kara", "Liam", "Nora", "Oscar",
               "Piper", "Reed", "Sara", "Troy", "Vera", "Wade", "Xena", "Yuri", "Zara", "Amber"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
              "Martinez", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Harris",
              "Clark", "Lewis", "Walker", "Hall", "Allen", "Young", "King"]
plans = ["free", "basic", "pro", "enterprise"]
plan_weights = [0.4, 0.3, 0.2, 0.1]
categories = ["Electronics", "Clothing", "Books", "Food", "Home", "Sports", "Toys", "Health"]
pages = ["/home", "/products", "/pricing", "/about", "/docs", "/blog", "/settings", "/dashboard", "/checkout", "/support"]
ticket_subjects = ["Login issue", "Billing question", "Feature request", "Bug report", "Account setup",
                   "Performance problem", "Data export help", "Integration support", "Upgrade inquiry", "Cancellation"]
priorities = ["low", "medium", "high", "critical"]
statuses_ticket = ["open", "in_progress", "resolved", "closed"]

base_date = datetime(2025, 1, 1)
now = datetime(2026, 3, 15)

# Users
users = []
for i in range(1, 501):
    fname = random.choice(first_names)
    lname = random.choice(last_names)
    name = f"{fname} {lname}"
    email = f"{fname.lower()}.{lname.lower()}{i}@example.com"
    plan = random.choices(plans, weights=plan_weights, k=1)[0]
    signup = base_date + timedelta(days=random.randint(0, 430))
    last_active = signup + timedelta(days=random.randint(1, (now - signup).days)) if signup < now else signup

    churned = 0
    churn_date = None
    # ~20% churn rate
    if random.random() < 0.20 and (now - signup).days > 30:
        churned = 1
        churn_date = signup + timedelta(days=random.randint(30, min(200, (now - signup).days)))
        last_active = churn_date

    users.append((i, name, email, plan, signup.strftime("%Y-%m-%d"),
                  last_active.strftime("%Y-%m-%d"), churned,
                  churn_date.strftime("%Y-%m-%d") if churn_date else None))

cur.executemany("INSERT OR IGNORE INTO users VALUES (?,?,?,?,?,?,?,?)", users)

# Products
products = []
product_names = {
    "Electronics": ["Wireless Earbuds", "USB-C Hub", "Mechanical Keyboard", "Webcam HD", "Portable Charger",
                    "Smart Watch", "Bluetooth Speaker", "Monitor Stand"],
    "Clothing": ["Cotton T-Shirt", "Denim Jacket", "Running Shoes", "Wool Sweater", "Cargo Pants",
                 "Baseball Cap", "Silk Scarf", "Leather Belt"],
    "Books": ["Python Cookbook", "Data Science 101", "AI Fundamentals", "Web Dev Guide", "SQL Mastery",
              "Cloud Architecture", "DevOps Handbook", "ML Engineering"],
    "Food": ["Organic Coffee", "Protein Bars", "Green Tea", "Trail Mix", "Dark Chocolate",
             "Almond Butter", "Energy Drink", "Granola"],
    "Home": ["Desk Lamp", "Plant Pot", "Wall Clock", "Throw Pillow", "Candle Set",
             "Storage Box", "Door Mat", "Picture Frame"],
    "Sports": ["Yoga Mat", "Resistance Bands", "Water Bottle", "Jump Rope", "Foam Roller",
               "Tennis Balls", "Gym Bag", "Wrist Wraps"],
    "Toys": ["Board Game", "Puzzle Set", "Card Game", "Building Blocks", "RC Car",
             "Art Kit", "Science Kit", "Drone Mini"],
    "Health": ["Vitamins Pack", "First Aid Kit", "Hand Sanitizer", "Face Mask Pack", "Thermometer",
               "Blood Pressure Monitor", "Fitness Tracker", "Sleep Aid"]
}
pid = 1
for cat, names in product_names.items():
    for pname in names:
        price = round(random.uniform(5, 200), 2)
        stock = random.randint(0, 500)
        products.append((pid, pname, cat, price, stock))
        pid += 1

cur.executemany("INSERT OR IGNORE INTO products VALUES (?,?,?,?,?)", products)

# Orders
orders = []
order_statuses = ["completed", "completed", "completed", "pending", "refunded", "cancelled"]
for oid in range(1, 3001):
    uid = random.randint(1, 500)
    user_signup = datetime.strptime(users[uid-1][4], "%Y-%m-%d")
    order_date = user_signup + timedelta(days=random.randint(1, max(1, (now - user_signup).days)))
    cat = random.choice(categories)
    amount = round(random.uniform(5, 500), 2)
    status = random.choice(order_statuses)
    orders.append((oid, uid, amount, cat, status, order_date.strftime("%Y-%m-%d")))

cur.executemany("INSERT OR IGNORE INTO orders VALUES (?,?,?,?,?,?)", orders)

# Page Views
views = []
for vid in range(1, 10001):
    uid = random.randint(1, 500)
    page = random.choice(pages)
    view_date = base_date + timedelta(days=random.randint(0, 430))
    duration = random.randint(5, 600)
    views.append((vid, uid, page, view_date.strftime("%Y-%m-%d"), duration))

cur.executemany("INSERT OR IGNORE INTO page_views VALUES (?,?,?,?,?)", views)

# Support Tickets
tickets = []
for tid in range(1, 801):
    uid = random.randint(1, 500)
    subject = random.choice(ticket_subjects)
    priority = random.choices(priorities, weights=[0.3, 0.4, 0.2, 0.1], k=1)[0]
    status = random.choice(statuses_ticket)
    created = base_date + timedelta(days=random.randint(0, 430))
    resolved = None
    if status in ("resolved", "closed"):
        resolved = created + timedelta(days=random.randint(0, 14))
    tickets.append((tid, uid, subject, priority, status,
                    created.strftime("%Y-%m-%d"),
                    resolved.strftime("%Y-%m-%d") if resolved else None))

cur.executemany("INSERT OR IGNORE INTO support_tickets VALUES (?,?,?,?,?,?,?)", tickets)

conn.commit()
conn.close()

print(f"Demo database created: {DB_PATH}")
print("  500 users | 3000 orders | 64 products | 10000 page views | 800 tickets")
print("  ~20% churn rate built in")
print()
print("Tables: users, orders, products, page_views, support_tickets")
print()
print("Try questions like:")
print('  "What is the churn rate by month?"')
print('  "Top 10 customers by total spend"')
print('  "Monthly revenue trend"')
print('  "Which product categories have the most orders?"')
print('  "Average ticket resolution time by priority"')
