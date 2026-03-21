# SQL Visualizer

Ask questions about your database in plain English. Get beautiful charts and tables back. Export to PDF.

Supports **PostgreSQL**, **MySQL**, and **SQLite**.

## Setup (3 minutes)

### 1. Clone and install

```bash
cd sql-visualizer
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create the demo database (optional but recommended)

```bash
python setup_demo_db.py
```

This creates a `demo.db` SQLite file with 500 users, 3000 orders, products, page views, and support tickets — ready to query immediately.

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```
ANTHROPIC_API_KEY=sk-ant-xxxxx          # Get from https://console.anthropic.com
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb    # Optional if using demo
```

### 4. Run

```bash
python app.py
```

Open **http://localhost:5000**. Pick a database from the dropdown, type a question, hit Visualize.

## Supported Databases

| Type       | Config                          | Driver         |
|------------|---------------------------------|----------------|
| PostgreSQL | `DATABASE_URL=postgresql://...` | psycopg2       |
| MySQL      | `MYSQL_URL=mysql://...`         | pymysql        |
| SQLite     | Auto-detected (`demo.db`)       | built-in       |

### Adding multiple databases

Set `EXTRA_DATABASES` in `.env` as a JSON array:

```
EXTRA_DATABASES=[{"key":"analytics","name":"Analytics DB","type":"postgres","url":"postgresql://..."},{"key":"warehouse","name":"Data Warehouse","type":"mysql","url":"mysql://user:pass@host:3306/db"}]
```

## Features

- Natural language to SQL (powered by Claude)
- Auto-detects your schema — no config needed
- Beautiful Chart.js visualizations
- Export to PDF or HTML
- Query history (saved in browser)
- Multi-database support with dropdown switcher
- SQL safety: only SELECT queries allowed

## Example Questions (with demo database)

- "What is the churn rate by month?"
- "Top 10 customers by total spend"
- "Monthly revenue trend"
- "Which product categories have the most orders?"
- "Average ticket resolution time by priority"
- "Show me user signups by plan type over time"

## Requirements

- Python 3.9+
- Anthropic API key (~$0.01-0.05 per query)
- A database (or just use the included demo)
