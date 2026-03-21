import os
import json
import re
import sqlite3
import time
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="static")


# ---------------------------------------------------------------------------
# LLM Provider Registry
# ---------------------------------------------------------------------------

def load_llm_providers():
    providers = {}

    if os.environ.get("GROQ_API_KEY"):
        providers["groq"] = {
            "name": "Groq (Free & Fast)",
            "models": [
                {"id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B (Best Free)"},
                {"id": "llama-3.1-8b-instant", "name": "Llama 3.1 8B (Fastest)"},
                {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B"},
                {"id": "gemma2-9b-it", "name": "Gemma 2 9B"},
            ],
            "default_model": "llama-3.3-70b-versatile",
        }

    if os.environ.get("ANTHROPIC_API_KEY"):
        providers["claude"] = {
            "name": "Claude (Anthropic)",
            "models": [
                {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4"},
                {"id": "claude-haiku-4-5-20251001", "name": "Claude Haiku 4.5"},
                {"id": "claude-opus-4-20250514", "name": "Claude Opus 4"},
            ],
            "default_model": "claude-sonnet-4-20250514",
        }

    if os.environ.get("OPENAI_API_KEY"):
        providers["openai"] = {
            "name": "OpenAI",
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o"},
                {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
            ],
            "default_model": "gpt-4o",
        }

    if os.environ.get("GEMINI_API_KEY"):
        providers["gemini"] = {
            "name": "Google Gemini (Free Tier)",
            "models": [
                {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash"},
                {"id": "gemini-2.5-pro-preview-06-05", "name": "Gemini 2.5 Pro"},
            ],
            "default_model": "gemini-2.0-flash",
        }

    ollama_url = os.environ.get("OLLAMA_URL", "").strip()
    if ollama_url:
        ollama_models = []
        try:
            import httpx
            resp = httpx.get(f"{ollama_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                for m in resp.json().get("models", []):
                    name = m["name"]
                    size_gb = round(m.get("size", 0) / 1e9, 1)
                    ollama_models.append({"id": name, "name": f"{name} ({size_gb}GB)"})
        except Exception:
            pass
        if not ollama_models:
            ollama_models = [{"id": "llama3", "name": "Llama 3 8B"}]
        providers["ollama"] = {
            "name": "Ollama (Local & Free)",
            "models": ollama_models,
            "default_model": ollama_models[0]["id"],
            "url": ollama_url,
        }

    return providers


LLM_PROVIDERS = load_llm_providers()


def call_llm(provider_key: str, model: str, prompt: str, max_tokens: int = 4096) -> str:
    if provider_key == "groq":
        import httpx
        resp = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['GROQ_API_KEY']}", "Content-Type": "application/json"},
            json={"model": model, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]},
            timeout=120,
        )
        if resp.status_code >= 400:
            raise ValueError(f"Groq API error ({resp.status_code}): {resp.text[:200]}")
        return resp.json()["choices"][0]["message"]["content"].strip()

    elif provider_key == "claude":
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        response = client.messages.create(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
        return response.content[0].text.strip()

    elif provider_key == "openai":
        import openai
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        response = client.chat.completions.create(model=model, max_tokens=max_tokens, messages=[{"role": "user", "content": prompt}])
        return response.choices[0].message.content.strip()

    elif provider_key == "gemini":
        import httpx
        api_key = os.environ["GEMINI_API_KEY"]
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"maxOutputTokens": max_tokens}}
        for attempt in range(4):
            resp = httpx.post(url, json=payload, timeout=120)
            if resp.status_code == 429:
                time.sleep((2 ** attempt) + 1)
                continue
            if resp.status_code >= 400:
                raise ValueError(f"Gemini API error ({resp.status_code}): {resp.text.replace(api_key, '***')[:200]}")
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        raise ValueError("Gemini rate limit exceeded. Wait a minute and retry.")

    elif provider_key == "ollama":
        import httpx
        ollama_url = LLM_PROVIDERS["ollama"]["url"].rstrip("/")
        payload = {"model": model, "prompt": prompt, "stream": False, "options": {"num_predict": max_tokens}}
        resp = httpx.post(f"{ollama_url}/api/generate", json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json()["response"].strip()

    else:
        raise ValueError(f"Unknown LLM provider: {provider_key}")


# ---------------------------------------------------------------------------
# Database registry & adapters
# ---------------------------------------------------------------------------

def load_db_configs():
    configs = {}
    demo_path = os.path.join(os.path.dirname(__file__), "demo.db")
    if os.path.exists(demo_path):
        configs["demo"] = {"name": "Demo (SQLite)", "type": "sqlite", "path": demo_path}
    if os.environ.get("DATABASE_URL"):
        configs["primary"] = {"name": "Primary (PostgreSQL)", "type": "postgres", "url": os.environ["DATABASE_URL"]}
    if os.environ.get("MYSQL_URL"):
        configs["mysql"] = {"name": "MySQL", "type": "mysql", "url": os.environ["MYSQL_URL"]}
    extra = os.environ.get("EXTRA_DATABASES")
    if extra:
        for db in json.loads(extra):
            configs[db["key"]] = {k: v for k, v in db.items() if k != "key"}
    return configs

DB_CONFIGS = load_db_configs()


def get_connection(db_key: str):
    cfg = DB_CONFIGS.get(db_key)
    if not cfg:
        raise ValueError(f"Unknown database: {db_key}")
    db_type = cfg["type"]
    if db_type == "sqlite":
        conn = sqlite3.connect(cfg["path"])
        conn.row_factory = sqlite3.Row
        return conn
    if db_type == "postgres":
        import psycopg2
        return psycopg2.connect(cfg["url"])
    if db_type == "mysql":
        import pymysql, pymysql.cursors
        url = cfg["url"]
        m = re.match(r"mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)", url)
        if not m:
            raise ValueError("Invalid MYSQL_URL format")
        return pymysql.connect(host=m.group(3), port=int(m.group(4)), user=m.group(1), password=m.group(2), database=m.group(5), cursorclass=pymysql.cursors.DictCursor)
    raise ValueError(f"Unsupported database type: {db_type}")


def get_db_schema(db_key: str) -> str:
    cfg = DB_CONFIGS[db_key]
    db_type = cfg["type"]
    conn = get_connection(db_key)
    try:
        cur = conn.cursor()
        if db_type == "sqlite":
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in cur.fetchall()]
            schema = {}
            for table in tables:
                cur.execute(f'PRAGMA table_info("{table}")')
                schema[table] = [f"{c[1]} ({c[2]})" for c in cur.fetchall()]
        elif db_type == "postgres":
            cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' ORDER BY table_name, ordinal_position")
            schema = {}
            for table, column, dtype in cur.fetchall():
                schema.setdefault(table, []).append(f"{column} ({dtype})")
        elif db_type == "mysql":
            cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = DATABASE() ORDER BY table_name, ordinal_position")
            schema = {}
            for row in cur.fetchall():
                t = row["TABLE_NAME"] if isinstance(row, dict) else row[0]
                c = row["COLUMN_NAME"] if isinstance(row, dict) else row[1]
                d = row["DATA_TYPE"] if isinstance(row, dict) else row[2]
                schema.setdefault(t, []).append(f"{c} ({d})")
        else:
            schema = {}
    finally:
        conn.close()
    lines = []
    for table, cols in schema.items():
        lines.append(f"TABLE {table}: {', '.join(cols)}")
    return "\n".join(lines)


def get_db_schema_structured(db_key: str):
    cfg = DB_CONFIGS[db_key]
    db_type = cfg["type"]
    conn = get_connection(db_key)
    tables = {}
    try:
        cur = conn.cursor()
        if db_type == "sqlite":
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            for (tname,) in cur.fetchall():
                cur.execute(f'PRAGMA table_info("{tname}")')
                cols = [{"name": c[1], "type": c[2]} for c in cur.fetchall()]
                cur.execute(f'SELECT COUNT(*) FROM "{tname}"')
                tables[tname] = {"columns": cols, "row_count": cur.fetchone()[0]}
        elif db_type == "postgres":
            cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'public' ORDER BY table_name, ordinal_position")
            for table, column, dtype in cur.fetchall():
                if table not in tables:
                    tables[table] = {"columns": [], "row_count": 0}
                tables[table]["columns"].append({"name": column, "type": dtype})
        elif db_type == "mysql":
            cur.execute("SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = DATABASE() ORDER BY table_name, ordinal_position")
            for row in cur.fetchall():
                t = row["TABLE_NAME"] if isinstance(row, dict) else row[0]
                c = row["COLUMN_NAME"] if isinstance(row, dict) else row[1]
                d = row["DATA_TYPE"] if isinstance(row, dict) else row[2]
                if t not in tables:
                    tables[t] = {"columns": [], "row_count": 0}
                tables[t]["columns"].append({"name": c, "type": d})
    finally:
        conn.close()
    return tables


def get_dialect(db_key: str) -> str:
    return {"sqlite": "SQLite", "postgres": "PostgreSQL", "mysql": "MySQL"}.get(DB_CONFIGS[db_key]["type"], "SQL")


# ---------------------------------------------------------------------------
# Text to SQL
# ---------------------------------------------------------------------------

def build_prompt(question: str, schema: str, dialect: str) -> str:
    return f"""You are a {dialect} expert. Given the database schema below, convert the user's question into a single valid {dialect} SELECT query.

SCHEMA:
{schema}

RULES:
- Return ONLY the raw SQL query, no markdown, no explanation, no code fences.
- Use only SELECT statements. Never INSERT, UPDATE, DELETE, DROP, ALTER, or TRUNCATE.
- If the question is ambiguous, make reasonable assumptions.
- Use proper date formats and aggregations as needed.
- Use {dialect}-compatible syntax only.
- Limit results to 500 rows max.

QUESTION: {question}"""


def validate_sql(sql: str):
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT") and not normalized.startswith("WITH"):
        raise ValueError("Only SELECT queries are allowed.")
    for kw in ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE", "CREATE", "GRANT", "REVOKE"]:
        if re.search(rf';\s*{kw}\b', normalized):
            raise ValueError(f"Forbidden keyword detected: {kw}")


def run_query(sql: str, db_key: str):
    cfg = DB_CONFIGS[db_key]
    db_type = cfg["type"]
    conn = get_connection(db_key)
    try:
        cur = conn.cursor()
        if db_type == "sqlite":
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            clean_rows = [dict(row) for row in rows]
        elif db_type == "postgres":
            import psycopg2.extras
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(sql)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []
            clean_rows = [dict(row) for row in rows]
        elif db_type == "mysql":
            cur.execute(sql)
            rows = cur.fetchall()
            if rows and isinstance(rows[0], dict):
                columns = list(rows[0].keys())
                clean_rows = rows
            else:
                columns = [desc[0] for desc in cur.description] if cur.description else []
                clean_rows = [dict(zip(columns, row)) for row in rows]
        else:
            columns, clean_rows = [], []
    finally:
        conn.close()
    return columns, clean_rows


# --- Routes ---

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/api/databases", methods=["GET"])
def list_databases():
    return jsonify([{"key": k, "name": c["name"], "type": c["type"]} for k, c in DB_CONFIGS.items()])

@app.route("/api/schema/<db_key>", methods=["GET"])
def get_schema(db_key):
    if db_key not in DB_CONFIGS:
        return jsonify({"error": f"Unknown database: {db_key}"}), 400
    try:
        return jsonify(get_db_schema_structured(db_key))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/providers", methods=["GET"])
def list_providers():
    return jsonify([{"key": k, "name": c["name"], "models": c["models"], "default_model": c["default_model"]} for k, c in LLM_PROVIDERS.items()])

@app.route("/api/ask", methods=["POST"])
def ask():
    body = request.get_json()
    question = body.get("question", "").strip()
    db_key = body.get("database", "").strip()
    provider_key = body.get("provider", "").strip()
    model = body.get("model", "").strip()

    if not question:
        return jsonify({"error": "Please provide a question."}), 400
    if not db_key:
        db_key = next(iter(DB_CONFIGS)) if DB_CONFIGS else None
    if not db_key or db_key not in DB_CONFIGS:
        return jsonify({"error": "No database available."}), 400
    if not provider_key:
        provider_key = next(iter(LLM_PROVIDERS)) if LLM_PROVIDERS else None
    if not provider_key or provider_key not in LLM_PROVIDERS:
        return jsonify({"error": "No LLM provider available."}), 400
    if not model:
        model = LLM_PROVIDERS[provider_key]["default_model"]

    debug = {}  # Collects input/output for every step
    MAX_RETRIES = 3

    try:
        # STEP 1: Read schema
        t0 = time.time()
        schema = get_db_schema(db_key)
        t1 = time.time()
        if not schema:
            return jsonify({"error": "No tables found in the database."}), 400
        debug["step1_schema"] = {
            "input": f"Database: {DB_CONFIGS[db_key]['name']} ({DB_CONFIGS[db_key]['type']})",
            "output": schema,
            "duration_ms": round((t1 - t0) * 1000),
        }

        # STEP 2: Build prompt & call LLM (with auto-retry on SQL errors)
        dialect = get_dialect(db_key)
        prompt = build_prompt(question, schema, dialect)
        attempts = []
        sql = None
        columns = None
        rows = None
        last_error = None

        for attempt in range(MAX_RETRIES):
            # Generate SQL
            if attempt == 0:
                current_prompt = prompt
            else:
                # Build a retry prompt with error context
                current_prompt = f"""{prompt}

IMPORTANT: Your previous SQL query failed with this error:
  SQL: {sql}
  Error: {last_error}

Fix the query. Use only valid {dialect} syntax. Return ONLY the corrected SQL, nothing else."""

            t2 = time.time()
            raw_llm_output = call_llm(provider_key, model, current_prompt, max_tokens=1024)
            t3 = time.time()
            sql = re.sub(r"^```(?:sql)?\s*", "", raw_llm_output)
            sql = re.sub(r"\s*```$", "", sql).strip()

            attempt_info = {
                "attempt": attempt + 1,
                "prompt": current_prompt if attempt > 0 else "(initial prompt)",
                "raw_output": raw_llm_output,
                "sql": sql,
                "duration_ms": round((t3 - t2) * 1000),
            }

            # Validate SQL
            try:
                validate_sql(sql)
            except ValueError as ve:
                attempt_info["error"] = str(ve)
                attempts.append(attempt_info)
                last_error = str(ve)
                continue

            # Try executing
            try:
                t4 = time.time()
                columns, rows = run_query(sql, db_key)
                t5 = time.time()
                attempt_info["success"] = True
                attempt_info["exec_ms"] = round((t5 - t4) * 1000)
                attempts.append(attempt_info)
                last_error = None
                break  # Success!
            except Exception as e:
                attempt_info["error"] = str(e)
                attempts.append(attempt_info)
                last_error = str(e)
                continue

        # Store debug info
        total_llm_ms = sum(a.get("duration_ms", 0) for a in attempts)
        debug["step2_llm"] = {
            "input": prompt,
            "output": raw_llm_output,
            "sql_cleaned": sql,
            "provider": provider_key,
            "model": model,
            "duration_ms": total_llm_ms,
            "attempts": len(attempts),
            "retries": [{"attempt": a["attempt"], "error": a.get("error"), "sql": a.get("sql"), "duration_ms": a.get("duration_ms")} for a in attempts if a.get("error")],
        }

        # If all attempts failed, return the last error
        if last_error:
            return jsonify({"error": f"Failed after {len(attempts)} attempts: {last_error}", "debug": debug}), 400

        # STEP 3: Query succeeded
        exec_ms = attempts[-1].get("exec_ms", 0)
        debug["step3_query"] = {
            "input": sql,
            "output_columns": columns,
            "output_row_count": len(rows),
            "output_sample": rows[:5],
            "duration_ms": exec_ms,
        }

        return jsonify({
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "question": question,
            "debug": debug,
        })

    except ValueError as e:
        return jsonify({"error": str(e), "debug": debug}), 400
    except Exception as e:
        err_msg = str(e)
        for env_key in ("GEMINI_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"):
            secret = os.environ.get(env_key, "")
            if secret and secret in err_msg:
                err_msg = err_msg.replace(secret, "***")
        return jsonify({"error": f"Error: {err_msg}", "debug": debug}), 500


@app.route("/api/run-sql", methods=["POST"])
def run_sql_direct():
    body = request.get_json()
    sql = body.get("sql", "").strip()
    db_key = body.get("database", "").strip()
    question = body.get("question", "Manual SQL").strip()

    if not sql:
        return jsonify({"error": "No SQL provided."}), 400
    if not db_key or db_key not in DB_CONFIGS:
        db_key = next(iter(DB_CONFIGS)) if DB_CONFIGS else None
    if not db_key:
        return jsonify({"error": "No database available."}), 400

    try:
        validate_sql(sql)
        t0 = time.time()
        columns, rows = run_query(sql, db_key)
        t1 = time.time()
        return jsonify({
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "question": question,
            "debug": {
                "step3_query": {
                    "input": sql,
                    "output_columns": columns,
                    "output_row_count": len(rows),
                    "output_sample": rows[:5],
                    "duration_ms": round((t1 - t0) * 1000),
                }
            },
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"\n  Chat2Chart running at http://localhost:{port}")
    print(f"  Databases: {list(DB_CONFIGS.keys())}")
    print(f"  LLM Providers: {list(LLM_PROVIDERS.keys())}\n")
    if not LLM_PROVIDERS:
        print("  WARNING: No LLM providers configured!")
        print("  Set at least one: GROQ_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, or OLLAMA_URL\n")
    app.run(debug=True, host="0.0.0.0", port=port)
