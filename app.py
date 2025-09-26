
import os
import sqlite3
import threading, webbrowser
from flask import Flask, request, render_template, jsonify
from groq import Groq
import pymysql
import psycopg2
import re

GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY",
    "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"
)
if GROQ_API_KEY == "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":
    print("Warning: Set your GROQ_API_KEY environment variable!")

groq_client = Groq(api_key=GROQ_API_KEY)
DB_FOLDER = "databases"
os.makedirs(DB_FOLDER, exist_ok=True)
app = Flask(__name__)

def get_db_path(db_name):
    return os.path.join(DB_FOLDER, db_name)

def connect_db(db_name):
    """Connect to SQLite database (case-insensitive for text)."""
    path = get_db_path(db_name)
    if not os.path.exists(path):
        raise ValueError(f"Database {db_name} not found!")
    conn = sqlite3.connect(path, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA case_sensitive_like = OFF;")
    conn.row_factory = sqlite3.Row
    return conn

def get_schema_info(conn):
    """Return schema with lowercase table and column names."""
    cursor = conn.cursor()
    tables = cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    ).fetchall()
    schema = {}
    for (table_name,) in tables:
        cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
        schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
    return schema


def generate_sql_with_groq(user_prompt, schema_info):
    system_message = {
        "role": "system",
        # "content": "You are a SQL assistant. Given a user's question and a database schema, generate a valid SQL query only."
        "content": (
            "You are a SQL assistant. Your job is to translate natural language questions into SQL queries.\n"
            "STRICT RULES:\n"
            "1. Only return a valid SQL query — do NOT include explanations, formatting, markdown, or backticks.\n"
            "2. Always wrap string comparisons in LOWER() for case-insensitive matching. Example: "
            "WHERE LOWER(students.name) = 'john'.\n"
            "3. If multiple tables have a 'name' column (e.g., students, courses, departments), "
            "always prefix with the table name and alias it properly. Example: "
            "students.name AS student_name, courses.name AS course_name.\n"
            "4. Avoid SELECT * — explicitly list columns with clear aliases.\n"
            "Your output must ONLY be pure SQL that can be executed directly."
        )
    }
    user_message = {
        "role": "user",
        "content": f"Schema:\n{schema_info}\n\nQuestion: {user_prompt}"
    }
    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[system_message, user_message]
    )
    sql_query = resp.choices[0].message.content.strip()
    if sql_query.startswith("```sql"):
        sql_query = sql_query.strip("```sql").strip("```").strip()
    return sql_query

def fix_sql_string_literals(sql):
    pattern = r"(LOWER\([^)]+\)\s*=\s*)([^\s'\"()]+)"
    def replacer(match):
        return f"{match.group(1)}'{match.group(2)}'"
    return re.sub(pattern, replacer, sql, flags=re.IGNORECASE)

def run_sql(conn, query):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description] if cursor.description else []
        results = [dict(row) for row in rows]
        return {"columns": cols, "rows": results}
    except Exception as e:
        return {"error": str(e)}


def get_connection(db_type, **kwargs):
    """Return DB connection (SQLite, MySQL, PostgreSQL)"""
    if db_type.lower() == "sqlite":
        path = kwargs.get("path")
        if not os.path.exists(path):
            raise ValueError("SQLite DB file not found!")
        conn = sqlite3.connect(path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA case_sensitive_like = OFF;")
        return conn
    elif db_type.lower() == "mysql":
        conn = pymysql.connect(
            host=kwargs.get("host"),
            port=int(kwargs.get("port", 3306)),
            user=kwargs.get("user"),
            password=kwargs.get("password"),
            database=kwargs.get("database"),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    elif db_type.lower() == "postgresql":
        conn = psycopg2.connect(
            host=kwargs.get("host"),
            port=int(kwargs.get("port", 5432)),
            user=kwargs.get("user"),
            password=kwargs.get("password"),
            dbname=kwargs.get("database")
        )
        return conn
    else:
        raise ValueError(f"Unsupported DB type: {db_type}")

def get_schema(conn, db_type):
    """Return schema for any DB with lowercase table/column names"""
    schema = {}
    cursor = conn.cursor()
    if db_type.lower() == "sqlite":
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()
        for (table_name,) in tables:
            cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
            schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
    elif db_type.lower() == "mysql":
        cursor.execute("SHOW TABLES;")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"DESCRIBE {table};")
            cols = cursor.fetchall()
            schema[table.lower()] = [{"name": c['Field'].lower(), "type": c['Type']} for c in cols]
    elif db_type.lower() == "postgresql":
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
        )
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(
                f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';"
            )
            cols = cursor.fetchall()
            schema[table.lower()] = [{"name": c[0].lower(), "type": c[1]} for c in cols]
    return schema
def get_schema(conn, db_type):
    schema = {}
    cursor = conn.cursor()
    if db_type.lower() == "sqlite":
        tables = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        ).fetchall()
        for (table_name,) in tables:
            cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
            schema[table_name] = [{"name": c[1], "type": c[2]} for c in cols]
    elif db_type.lower() == "mysql":
        cursor.execute("SHOW TABLES;")
        tables = [list(row.values())[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(f"DESCRIBE {table};")
            cols = cursor.fetchall()
            schema[table] = [{"name": c['Field'], "type": c['Type']} for c in cols]
    elif db_type.lower() == "postgresql":
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
        )
        tables = [row[0] for row in cursor.fetchall()]
        for table in tables:
            cursor.execute(
                f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';"
            )
            cols = cursor.fetchall()
            schema[table] = [{"name": c[0], "type": c[1]} for c in cols]
    return schema

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/databases", methods=["GET"])
def list_databases():
    dbs = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db")]
    return jsonify({"databases": dbs})

@app.route("/schema", methods=["POST"])
def schema():
    data = request.json
    db_name = data.get("db_name")
    try:
        with connect_db(db_name) as conn:
            schema_info = get_schema_info(conn)
        return jsonify({"schema": schema_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
@app.route("/visualize", methods=["POST"])
def visualize():
    data = request.json
    db_name = data.get("db_name")
    prompt = data.get("prompt")

    try:
        with connect_db(db_name) as conn:
            schema_info = get_schema_info(conn)
            sql_query = generate_sql_with_groq(prompt, schema_info)
            result = run_sql(conn, sql_query)

            if result.get("error"):
                return jsonify({"error": result["error"]}), 400

            # Create a short summary
            user_msg = {
                "role": "user",
                "content": (
                    f"Here is the data returned by SQL:\n"
                    f"Columns: {result['columns']}\nRows: {result['rows'][:5]}...\n\n"
                    "Write 2-3 concise sentences summarizing the key insights "
                    "for a professional data visualization caption."
                )
            }
            resp = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "You are a data analyst."}, user_msg]
            )
            summary = resp.choices[0].message.content.strip()

        return jsonify({
            "sql": sql_query,
            "columns": result["columns"],
            "rows": result["rows"],
            "summary": summary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/db_description", methods=["POST"])
def db_description():
    data = request.json
    db_name = data.get("db_name")
    try:
        with connect_db(db_name) as conn:
            schema_info = get_schema_info(conn)

        schema_lower = {
            k.lower(): [{'name': c['name'].lower(), 'type': c['type']} for c in v]
            for k, v in schema_info.items()
        }

        system_message = {
            "role": "system",
            "content": (
                "You are a helpful assistant that summarizes database schemas "
                "in simple English for laymen. Keep it short and clear."
            )
        }
        user_message = {
            "role": "user",
            "content": (
                f"Schema:\n{schema_lower}\n\n"
                "Provide a 2–3 line description of what this database is about "
                "and what kind of information it stores."
            )
        }

        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[system_message, user_message]
        )

        description = resp.choices[0].message.content.strip()
        return jsonify({"description": description})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    db_name = data.get("db_name")
    question = data.get("question")
    try:
        with connect_db(db_name) as conn:
            schema_info = get_schema_info(conn)
            sql_query = generate_sql_with_groq(question, schema_info)

            sql_query = fix_sql_string_literals(sql_query)

            result = run_sql(conn, sql_query)
        return jsonify({"sql": sql_query, "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/create_db", methods=["POST"])
def create_db():
    data = request.json
    db_name = data.get("db_name")
    prompt = data.get("prompt")
    if not db_name.endswith(".db"):
        db_name += ".db"
    db_path = get_db_path(db_name)
    if os.path.exists(db_path):
        return jsonify({"error": "Database already exists!"}), 400
    try:
        system_message = {
            "role": "system",
            "content": "You are a SQL assistant. Generate only SQL CREATE TABLE statements based on the user's description. Do not add data, comments or explanation."
        }
        user_message = {"role": "user", "content": prompt}
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[system_message, user_message]
        )
        sql_schema = resp.choices[0].message.content.strip()
        if sql_schema.startswith("```sql"):
            sql_schema = sql_schema.strip("```sql").strip("```").strip()
        with sqlite3.connect(db_path, timeout=10) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.executescript(sql_schema)
            conn.commit()
        return jsonify({"status": "Database created", "sql_schema": sql_schema})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/add_row", methods=["POST"])
def add_row():
    data = request.json
    db_name = data.get("db_name")
    table_name = data.get("table")
    values_text = data.get("values")
    try:
        with connect_db(db_name) as conn:
            cursor = conn.cursor()
            schema = get_schema_info(conn)
            table_key = table_name.lower()
            if table_key not in schema:
                return jsonify({"error": f"Table {table_name} not found!"}), 400

            columns = [c["name"] for c in schema[table_key]]

            raw_values = values_text.strip()
            values = [v.strip() for v in raw_values.split(",")]

            if len(values) != len(columns):
                return jsonify({"error": f"Expected {len(columns)} values, got {len(values)}"}), 400

            placeholders = ",".join("?" * len(values))
            sql = f'INSERT INTO "{table_key}" ({",".join(columns)}) VALUES ({placeholders})'

            cursor.execute(sql, values)
            conn.commit()

        return jsonify({"status": "Row added"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
@app.route("/delete_row", methods=["POST"])
def delete_row():
    """
    Request JSON:
        { "db_name": "school.db",
          "table": "students",
          "condition": "student_id=1" }
    """
    data = request.json
    db_name  = data.get("db_name")
    table    = data.get("table")
    condition = data.get("condition")

    if not all([db_name, table, condition]):
        return jsonify({"error": "db_name, table and condition are required"}), 400

    try:
        with connect_db(db_name) as conn:
            cur = conn.cursor()

            cur.execute(f'PRAGMA table_info("{table}")')
            cols_info = cur.fetchall()
            valid_cols = {row[1] for row in cols_info}
            pk_cols    = [row[1] for row in cols_info if row[5] == 1]  # primary key(s)

            left_side = condition.split('=')[0].strip().strip('"')

            if left_side not in valid_cols and len(pk_cols) == 1:
                pk = pk_cols[0]
                condition = condition.replace(left_side, pk, 1)

            left_side_final = condition.split('=')[0].strip().strip('"')
            if left_side_final not in valid_cols:
                return jsonify({"error": f"Invalid column name: {left_side_final}"}), 400

            sql = f'DELETE FROM "{table}" WHERE {condition}'
            cur.execute(sql)
            conn.commit()

        return jsonify({"status": "Row deleted", "rows_affected": cur.rowcount})

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/connect_db", methods=["POST"])
def connect_db_route():
    data = request.json
    db_type = data.get("db_type")
    conn_info = data.copy()
    conn_info.pop("db_type", None)
    try:
        conn = get_connection(db_type, **conn_info)
        schema = get_schema(conn, db_type)
        conn.close()
        return jsonify({"schema": schema})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    threading.Timer(
        1.5,
        lambda: webbrowser.open("http://127.0.0.1:5000/")
    ).start()

    app.run(host="0.0.0.0", port=5000, debug=True)
