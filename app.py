
# # # import os
# # # import sqlite3
# # # import threading, webbrowser
# # # from flask import Flask, request, render_template, jsonify
# # # from groq import Groq
# # # import pymysql
# # # import psycopg2
# # # import re

# # # GROQ_API_KEY = os.environ.get(
# # #     "GROQ_API_KEY",
# # #     "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"
# # # )
# # # if GROQ_API_KEY == "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":
# # #     print("Warning: Set your GROQ_API_KEY environment variable!")

# # # groq_client = Groq(api_key=GROQ_API_KEY)
# # # DB_FOLDER = "databases"
# # # os.makedirs(DB_FOLDER, exist_ok=True)
# # # app = Flask(__name__)

# # # def get_db_path(db_name):
# # #     return os.path.join(DB_FOLDER, db_name)

# # # def connect_db(db_name):
# # #     """Connect to SQLite database (case-insensitive for text)."""
# # #     path = get_db_path(db_name)
# # #     if not os.path.exists(path):
# # #         raise ValueError(f"Database {db_name} not found!")
# # #     conn = sqlite3.connect(path, timeout=10)
# # #     conn.execute("PRAGMA journal_mode=WAL;")
# # #     conn.execute("PRAGMA case_sensitive_like = OFF;")
# # #     conn.row_factory = sqlite3.Row
# # #     return conn

# # # def get_schema_info(conn):
# # #     """Return schema with lowercase table and column names."""
# # #     cursor = conn.cursor()
# # #     tables = cursor.execute(
# # #         "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
# # #     ).fetchall()
# # #     schema = {}
# # #     for (table_name,) in tables:
# # #         cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
# # #         schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
# # #     return schema


# # # def generate_sql_with_groq(user_prompt, schema_info):
# # #     system_message = {
# # #         "role": "system",
# # #         # "content": "You are a SQL assistant. Given a user's question and a database schema, generate a valid SQL query only."
# # #         "content": (
# # #             "You are a SQL assistant. Your job is to translate natural language questions into SQL queries.\n"
# # #             "STRICT RULES:\n"
# # #             "1. Only return a valid SQL query — do NOT include explanations, formatting, markdown, or backticks.\n"
# # #             "2. Always wrap string comparisons in LOWER() for case-insensitive matching. Example: "
# # #             "WHERE LOWER(students.name) = 'john'.\n"
# # #             "3. If multiple tables have a 'name' column (e.g., students, courses, departments), "
# # #             "always prefix with the table name and alias it properly. Example: "
# # #             "students.name AS student_name, courses.name AS course_name.\n"
# # #             "4. Avoid SELECT * — explicitly list columns with clear aliases.\n"
# # #             "Your output must ONLY be pure SQL that can be executed directly."
# # #         )
# # #     }
# # #     user_message = {
# # #         "role": "user",
# # #         "content": f"Schema:\n{schema_info}\n\nQuestion: {user_prompt}"
# # #     }
# # #     resp = groq_client.chat.completions.create(
# # #         model="llama-3.3-70b-versatile",
# # #         messages=[system_message, user_message]
# # #     )
# # #     sql_query = resp.choices[0].message.content.strip()
# # #     if sql_query.startswith("```sql"):
# # #         sql_query = sql_query.strip("```sql").strip("```").strip()
# # #     return sql_query

# # # def fix_sql_string_literals(sql):
# # #     pattern = r"(LOWER\([^)]+\)\s*=\s*)([^\s'\"()]+)"
# # #     def replacer(match):
# # #         return f"{match.group(1)}'{match.group(2)}'"
# # #     return re.sub(pattern, replacer, sql, flags=re.IGNORECASE)

# # # def run_sql(conn, query):
# # #     try:
# # #         cursor = conn.cursor()
# # #         cursor.execute(query)
# # #         rows = cursor.fetchall()
# # #         cols = [desc[0] for desc in cursor.description] if cursor.description else []
# # #         results = [dict(row) for row in rows]
# # #         return {"columns": cols, "rows": results}
# # #     except Exception as e:
# # #         return {"error": str(e)}


# # # def get_connection(db_type, **kwargs):
# # #     """Return DB connection (SQLite, MySQL, PostgreSQL)"""
# # #     if db_type.lower() == "sqlite":
# # #         path = kwargs.get("path")
# # #         if not os.path.exists(path):
# # #             raise ValueError("SQLite DB file not found!")
# # #         conn = sqlite3.connect(path, timeout=10)
# # #         conn.row_factory = sqlite3.Row
# # #         conn.execute("PRAGMA journal_mode=WAL;")
# # #         conn.execute("PRAGMA case_sensitive_like = OFF;")
# # #         return conn
# # #     elif db_type.lower() == "mysql":
# # #         conn = pymysql.connect(
# # #             host=kwargs.get("host"),
# # #             port=int(kwargs.get("port", 3306)),
# # #             user=kwargs.get("user"),
# # #             password=kwargs.get("password"),
# # #             database=kwargs.get("database"),
# # #             charset='utf8mb4',
# # #             cursorclass=pymysql.cursors.DictCursor
# # #         )
# # #         return conn
# # #     elif db_type.lower() == "postgresql":
# # #         conn = psycopg2.connect(
# # #             host=kwargs.get("host"),
# # #             port=int(kwargs.get("port", 5432)),
# # #             user=kwargs.get("user"),
# # #             password=kwargs.get("password"),
# # #             dbname=kwargs.get("database")
# # #         )
# # #         return conn
# # #     else:
# # #         raise ValueError(f"Unsupported DB type: {db_type}")

# # # def get_schema(conn, db_type):
# # #     """Return schema for any DB with lowercase table/column names"""
# # #     schema = {}
# # #     cursor = conn.cursor()
# # #     if db_type.lower() == "sqlite":
# # #         tables = cursor.execute(
# # #             "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
# # #         ).fetchall()
# # #         for (table_name,) in tables:
# # #             cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
# # #             schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
# # #     elif db_type.lower() == "mysql":
# # #         cursor.execute("SHOW TABLES;")
# # #         tables = [list(row.values())[0] for row in cursor.fetchall()]
# # #         for table in tables:
# # #             cursor.execute(f"DESCRIBE {table};")
# # #             cols = cursor.fetchall()
# # #             schema[table.lower()] = [{"name": c['Field'].lower(), "type": c['Type']} for c in cols]
# # #     elif db_type.lower() == "postgresql":
# # #         cursor.execute(
# # #             "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
# # #         )
# # #         tables = [row[0] for row in cursor.fetchall()]
# # #         for table in tables:
# # #             cursor.execute(
# # #                 f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';"
# # #             )
# # #             cols = cursor.fetchall()
# # #             schema[table.lower()] = [{"name": c[0].lower(), "type": c[1]} for c in cols]
# # #     return schema
# # # def get_schema(conn, db_type):
# # #     schema = {}
# # #     cursor = conn.cursor()
# # #     if db_type.lower() == "sqlite":
# # #         tables = cursor.execute(
# # #             "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
# # #         ).fetchall()
# # #         for (table_name,) in tables:
# # #             cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
# # #             schema[table_name] = [{"name": c[1], "type": c[2]} for c in cols]
# # #     elif db_type.lower() == "mysql":
# # #         cursor.execute("SHOW TABLES;")
# # #         tables = [list(row.values())[0] for row in cursor.fetchall()]
# # #         for table in tables:
# # #             cursor.execute(f"DESCRIBE {table};")
# # #             cols = cursor.fetchall()
# # #             schema[table] = [{"name": c['Field'], "type": c['Type']} for c in cols]
# # #     elif db_type.lower() == "postgresql":
# # #         cursor.execute(
# # #             "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
# # #         )
# # #         tables = [row[0] for row in cursor.fetchall()]
# # #         for table in tables:
# # #             cursor.execute(
# # #                 f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';"
# # #             )
# # #             cols = cursor.fetchall()
# # #             schema[table] = [{"name": c[0], "type": c[1]} for c in cols]
# # #     return schema

# # # @app.route("/")
# # # def index():
# # #     return render_template("index.html")

# # # @app.route("/databases", methods=["GET"])
# # # def list_databases():
# # #     dbs = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db")]
# # #     return jsonify({"databases": dbs})

# # # @app.route("/schema", methods=["POST"])
# # # def schema():
# # #     data = request.json
# # #     db_name = data.get("db_name")
# # #     try:
# # #         with connect_db(db_name) as conn:
# # #             schema_info = get_schema_info(conn)
# # #         return jsonify({"schema": schema_info})
# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 400
# # # @app.route("/visualize", methods=["POST"])
# # # def visualize():
# # #     data = request.json
# # #     db_name = data.get("db_name")
# # #     prompt = data.get("prompt")

# # #     try:
# # #         with connect_db(db_name) as conn:
# # #             schema_info = get_schema_info(conn)
# # #             sql_query = generate_sql_with_groq(prompt, schema_info)
# # #             result = run_sql(conn, sql_query)

# # #             if result.get("error"):
# # #                 return jsonify({"error": result["error"]}), 400

# # #             # Create a short summary
# # #             user_msg = {
# # #                 "role": "user",
# # #                 "content": (
# # #                     f"Here is the data returned by SQL:\n"
# # #                     f"Columns: {result['columns']}\nRows: {result['rows'][:5]}...\n\n"
# # #                     "Write 2-3 concise sentences summarizing the key insights "
# # #                     "for a professional data visualization caption."
# # #                 )
# # #             }
# # #             resp = groq_client.chat.completions.create(
# # #                 model="llama-3.3-70b-versatile",
# # #                 messages=[{"role": "system", "content": "You are a data analyst."}, user_msg]
# # #             )
# # #             summary = resp.choices[0].message.content.strip()

# # #         return jsonify({
# # #             "sql": sql_query,
# # #             "columns": result["columns"],
# # #             "rows": result["rows"],
# # #             "summary": summary
# # #         })
# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 400


# # # @app.route("/db_description", methods=["POST"])
# # # def db_description():
# # #     data = request.json
# # #     db_name = data.get("db_name")
# # #     try:
# # #         with connect_db(db_name) as conn:
# # #             schema_info = get_schema_info(conn)

# # #         schema_lower = {
# # #             k.lower(): [{'name': c['name'].lower(), 'type': c['type']} for c in v]
# # #             for k, v in schema_info.items()
# # #         }

# # #         system_message = {
# # #             "role": "system",
# # #             "content": (
# # #                 "You are a helpful assistant that summarizes database schemas "
# # #                 "in simple English for laymen. Keep it short and clear."
# # #             )
# # #         }
# # #         user_message = {
# # #             "role": "user",
# # #             "content": (
# # #                 f"Schema:\n{schema_lower}\n\n"
# # #                 "Provide a 2–3 line description of what this database is about "
# # #                 "and what kind of information it stores."
# # #             )
# # #         }

# # #         resp = groq_client.chat.completions.create(
# # #             model="llama-3.3-70b-versatile",
# # #             messages=[system_message, user_message]
# # #         )

# # #         description = resp.choices[0].message.content.strip()
# # #         return jsonify({"description": description})

# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 400

# # # @app.route("/ask", methods=["POST"])
# # # def ask():
# # #     data = request.json
# # #     db_name = data.get("db_name")
# # #     question = data.get("question")
# # #     try:
# # #         with connect_db(db_name) as conn:
# # #             schema_info = get_schema_info(conn)
# # #             sql_query = generate_sql_with_groq(question, schema_info)

# # #             sql_query = fix_sql_string_literals(sql_query)

# # #             result = run_sql(conn, sql_query)
# # #         return jsonify({"sql": sql_query, "result": result})
# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 400

# # # @app.route("/create_db", methods=["POST"])
# # # def create_db():
# # #     data = request.json
# # #     db_name = data.get("db_name")
# # #     prompt = data.get("prompt")
# # #     if not db_name.endswith(".db"):
# # #         db_name += ".db"
# # #     db_path = get_db_path(db_name)
# # #     if os.path.exists(db_path):
# # #         return jsonify({"error": "Database already exists!"}), 400
# # #     try:
# # #         system_message = {
# # #             "role": "system",
# # #             "content": "You are a SQL assistant. Generate only SQL CREATE TABLE statements based on the user's description. Do not add data, comments or explanation."
# # #         }
# # #         user_message = {"role": "user", "content": prompt}
# # #         resp = groq_client.chat.completions.create(
# # #             model="llama-3.3-70b-versatile",
# # #             messages=[system_message, user_message]
# # #         )
# # #         sql_schema = resp.choices[0].message.content.strip()
# # #         if sql_schema.startswith("```sql"):
# # #             sql_schema = sql_schema.strip("```sql").strip("```").strip()
# # #         with sqlite3.connect(db_path, timeout=10) as conn:
# # #             conn.execute("PRAGMA journal_mode=WAL;")
# # #             conn.executescript(sql_schema)
# # #             conn.commit()
# # #         return jsonify({"status": "Database created", "sql_schema": sql_schema})
# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 400

# # # @app.route("/add_row", methods=["POST"])
# # # def add_row():
# # #     data = request.json
# # #     db_name = data.get("db_name")
# # #     table_name = data.get("table")
# # #     values_text = data.get("values")
# # #     try:
# # #         with connect_db(db_name) as conn:
# # #             cursor = conn.cursor()
# # #             schema = get_schema_info(conn)
# # #             table_key = table_name.lower()
# # #             if table_key not in schema:
# # #                 return jsonify({"error": f"Table {table_name} not found!"}), 400

# # #             columns = [c["name"] for c in schema[table_key]]

# # #             raw_values = values_text.strip()
# # #             values = [v.strip() for v in raw_values.split(",")]

# # #             if len(values) != len(columns):
# # #                 return jsonify({"error": f"Expected {len(columns)} values, got {len(values)}"}), 400

# # #             placeholders = ",".join("?" * len(values))
# # #             sql = f'INSERT INTO "{table_key}" ({",".join(columns)}) VALUES ({placeholders})'

# # #             cursor.execute(sql, values)
# # #             conn.commit()

# # #         return jsonify({"status": "Row added"})
# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 400
# # # @app.route("/delete_row", methods=["POST"])
# # # def delete_row():
# # #     """
# # #     Request JSON:
# # #         { "db_name": "school.db",
# # #           "table": "students",
# # #           "condition": "student_id=1" }
# # #     """
# # #     data = request.json
# # #     db_name  = data.get("db_name")
# # #     table    = data.get("table")
# # #     condition = data.get("condition")

# # #     if not all([db_name, table, condition]):
# # #         return jsonify({"error": "db_name, table and condition are required"}), 400

# # #     try:
# # #         with connect_db(db_name) as conn:
# # #             cur = conn.cursor()

# # #             cur.execute(f'PRAGMA table_info("{table}")')
# # #             cols_info = cur.fetchall()
# # #             valid_cols = {row[1] for row in cols_info}
# # #             pk_cols    = [row[1] for row in cols_info if row[5] == 1]  # primary key(s)

# # #             left_side = condition.split('=')[0].strip().strip('"')

# # #             if left_side not in valid_cols and len(pk_cols) == 1:
# # #                 pk = pk_cols[0]
# # #                 condition = condition.replace(left_side, pk, 1)

# # #             left_side_final = condition.split('=')[0].strip().strip('"')
# # #             if left_side_final not in valid_cols:
# # #                 return jsonify({"error": f"Invalid column name: {left_side_final}"}), 400

# # #             sql = f'DELETE FROM "{table}" WHERE {condition}'
# # #             cur.execute(sql)
# # #             conn.commit()

# # #         return jsonify({"status": "Row deleted", "rows_affected": cur.rowcount})

# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 400

# # # @app.route("/connect_db", methods=["POST"])
# # # def connect_db_route():
# # #     data = request.json
# # #     db_type = data.get("db_type")
# # #     conn_info = data.copy()
# # #     conn_info.pop("db_type", None)
# # #     try:
# # #         conn = get_connection(db_type, **conn_info)
# # #         schema = get_schema(conn, db_type)
# # #         conn.close()
# # #         return jsonify({"schema": schema})
# # #     except Exception as e:
# # #         return jsonify({"error": str(e)}), 400

# # # if __name__ == "__main__":
# # #     threading.Timer(
# # #         1.5,
# # #         lambda: webbrowser.open("http://127.0.0.1:5000/")
# # #     ).start()

# # #     app.run(host="0.0.0.0", port=5000, debug=True)

# # import os
# # import sqlite3
# # import threading
# # import webbrowser
# # import json
# # import re
# # from flask import Flask, request, render_template, jsonify, url_for
# # from groq import Groq
# # import pymysql
# # import psycopg2

# # # ---------- Config & Keys ----------
# # GROQ_API_KEY = os.environ.get(
# #     "GROQ_API_KEY",
# #     "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"
# # )
# # if GROQ_API_KEY == "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":
# #     print("Warning: Set your GROQ_API_KEY environment variable!")

# # groq_client = Groq(api_key=GROQ_API_KEY)

# # STRIPE_SECRET_KEY="sk_test_51SCZrEBHO8g2Q8ZQjcKLrhyyvXwjPHfjANMf2ppwxrkZTMrroWLWxI6s6KfWV3tGQZzz9VqG0nA8pySzJK1njZSr002baWcZmf"
# # STRIPE_PUBLISHABLE_KEY="pk_test_51SCZrEBHO8g2Q8ZQ0P7oN581Q1Fq3l0VzzpLv8yroTjAV1DIFnhV64bMLjyfDh0Kp6Snf2oKHNi2xUC3TEu4zJxl00yE3q5phJ"
# # STRIPE_WEBHOOK_SECRET="whsec_d089c53f00ae2edbea1e23f8fc82d24c2d5b821940b28be5e43fdb6aa52f42f7"

# # if not STRIPE_SECRET_KEY:
# #     print("Warning: STRIPE_SECRET_KEY not set. Stripe endpoints will raise errors until set.")
# # else:
# #     import stripe
# #     stripe.api_key = STRIPE_SECRET_KEY

# # DB_FOLDER = "databases"
# # os.makedirs(DB_FOLDER, exist_ok=True)
# # app = Flask(__name__, static_folder=".", template_folder=".")

# # # ---------- Your existing DB & Groq utilities (unchanged) ----------
# # def get_db_path(db_name):
# #     return os.path.join(DB_FOLDER, db_name)

# # def connect_db(db_name):
# #     """Connect to SQLite database (case-insensitive for text)."""
# #     path = get_db_path(db_name)
# #     if not os.path.exists(path):
# #         raise ValueError(f"Database {db_name} not found!")
# #     conn = sqlite3.connect(path, timeout=10)
# #     conn.execute("PRAGMA journal_mode=WAL;")
# #     conn.execute("PRAGMA case_sensitive_like = OFF;")
# #     conn.row_factory = sqlite3.Row
# #     return conn

# # def get_schema_info(conn):
# #     """Return schema with lowercase table and column names."""
# #     cursor = conn.cursor()
# #     tables = cursor.execute(
# #         "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
# #     ).fetchall()
# #     schema = {}
# #     for (table_name,) in tables:
# #         cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
# #         schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
# #     return schema

# # def generate_sql_with_groq(user_prompt, schema_info):
# #     system_message = {
# #         "role": "system",
# #         "content": (
# #             "You are a SQL assistant. Your job is to translate natural language questions into SQL queries.\n"
# #             "STRICT RULES:\n"
# #             "1. Only return a valid SQL query — do NOT include explanations, formatting, markdown, or backticks.\n"
# #             "2. Always wrap string comparisons in LOWER() for case-insensitive matching. Example: "
# #             "WHERE LOWER(students.name) = 'john'.\n"
# #             "3. If multiple tables have a 'name' column (e.g., students, courses, departments), "
# #             "always prefix with the table name and alias it properly. Example: "
# #             "students.name AS student_name, courses.name AS course_name.\n"
# #             "4. Avoid SELECT * — explicitly list columns with clear aliases.\n"
# #             "Your output must ONLY be pure SQL that can be executed directly."
# #         )
# #     }
# #     user_message = {
# #         "role": "user",
# #         "content": f"Schema:\n{schema_info}\n\nQuestion: {user_prompt}"
# #     }
# #     resp = groq_client.chat.completions.create(
# #         model="llama-3.3-70b-versatile",
# #         messages=[system_message, user_message]
# #     )
# #     sql_query = resp.choices[0].message.content.strip()
# #     if sql_query.startswith("```sql"):
# #         sql_query = sql_query.strip("```sql").strip("```").strip()
# #     return sql_query

# # def fix_sql_string_literals(sql):
# #     pattern = r"(LOWER\([^)]+\)\s*=\s*)([^\s'\"()]+)"
# #     def replacer(match):
# #         return f"{match.group(1)}'{match.group(2)}'"
# #     return re.sub(pattern, replacer, sql, flags=re.IGNORECASE)

# # def run_sql(conn, query):
# #     try:
# #         cursor = conn.cursor()
# #         cursor.execute(query)
# #         rows = cursor.fetchall()
# #         cols = [desc[0] for desc in cursor.description] if cursor.description else []
# #         results = [dict(row) for row in rows]
# #         return {"columns": cols, "rows": results}
# #     except Exception as e:
# #         return {"error": str(e)}

# # def get_connection(db_type, **kwargs):
# #     """Return DB connection (SQLite, MySQL, PostgreSQL)"""
# #     if db_type.lower() == "sqlite":
# #         path = kwargs.get("path")
# #         if not os.path.exists(path):
# #             raise ValueError("SQLite DB file not found!")
# #         conn = sqlite3.connect(path, timeout=10)
# #         conn.row_factory = sqlite3.Row
# #         conn.execute("PRAGMA journal_mode=WAL;")
# #         conn.execute("PRAGMA case_sensitive_like = OFF;")
# #         return conn
# #     elif db_type.lower() == "mysql":
# #         conn = pymysql.connect(
# #             host=kwargs.get("host"),
# #             port=int(kwargs.get("port", 3306)),
# #             user=kwargs.get("user"),
# #             password=kwargs.get("password"),
# #             database=kwargs.get("database"),
# #             charset='utf8mb4',
# #             cursorclass=pymysql.cursors.DictCursor
# #         )
# #         return conn
# #     elif db_type.lower() == "postgresql":
# #         conn = psycopg2.connect(
# #             host=kwargs.get("host"),
# #             port=int(kwargs.get("port", 5432)),
# #             user=kwargs.get("user"),
# #             password=kwargs.get("password"),
# #             dbname=kwargs.get("database")
# #         )
# #         return conn
# #     else:
# #         raise ValueError(f"Unsupported DB type: {db_type}")

# # def get_schema(conn, db_type):
# #     """Return schema for any DB with lowercase table/column names"""
# #     schema = {}
# #     cursor = conn.cursor()
# #     if db_type.lower() == "sqlite":
# #         tables = cursor.execute(
# #             "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
# #         ).fetchall()
# #         for (table_name,) in tables:
# #             cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
# #             schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
# #     elif db_type.lower() == "mysql":
# #         cursor.execute("SHOW TABLES;")
# #         tables = [list(row.values())[0] for row in cursor.fetchall()]
# #         for table in tables:
# #             cursor.execute(f"DESCRIBE {table};")
# #             cols = cursor.fetchall()
# #             schema[table.lower()] = [{"name": c['Field'].lower(), "type": c['Type']} for c in cols]
# #     elif db_type.lower() == "postgresql":
# #         cursor.execute(
# #             "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
# #         )
# #         tables = [row[0] for row in cursor.fetchall()]
# #         for table in tables:
# #             cursor.execute(
# #                 f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';"
# #             )
# #             cols = cursor.fetchall()
# #             schema[table.lower()] = [{"name": c[0].lower(), "type": c[1]} for c in cols]
# #     return schema

# # # ---------- End existing utilities ----------

# # @app.route("/")
# # def index():
# #     # serve the existing index.html
# #     return render_template("index.html")

# # @app.route("/databases", methods=["GET"])
# # def list_databases():
# #     dbs = [f for f in os.listdir(DB_FOLDER) if f.endswith(".db")]
# #     return jsonify({"databases": dbs})

# # @app.route("/schema", methods=["POST"])
# # def schema():
# #     data = request.json
# #     db_name = data.get("db_name")
# #     try:
# #         with connect_db(db_name) as conn:
# #             schema_info = get_schema_info(conn)
# #         return jsonify({"schema": schema_info})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/visualize", methods=["POST"])
# # def visualize():
# #     data = request.json
# #     db_name = data.get("db_name")
# #     prompt = data.get("prompt")

# #     try:
# #         with connect_db(db_name) as conn:
# #             schema_info = get_schema_info(conn)
# #             sql_query = generate_sql_with_groq(prompt, schema_info)
# #             result = run_sql(conn, sql_query)

# #             if result.get("error"):
# #                 return jsonify({"error": result["error"]}), 400

# #             # Create a short summary
# #             user_msg = {
# #                 "role": "user",
# #                 "content": (
# #                     f"Here is the data returned by SQL:\n"
# #                     f"Columns: {result['columns']}\nRows: {result['rows'][:5]}...\n\n"
# #                     "Write 2-3 concise sentences summarizing the key insights "
# #                     "for a professional data visualization caption."
# #                 )
# #             }
# #             resp = groq_client.chat.completions.create(
# #                 model="llama-3.3-70b-versatile",
# #                 messages=[{"role": "system", "content": "You are a data analyst."}, user_msg]
# #             )
# #             summary = resp.choices[0].message.content.strip()

# #         return jsonify({
# #             "sql": sql_query,
# #             "columns": result["columns"],
# #             "rows": result["rows"],
# #             "summary": summary
# #         })
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/db_description", methods=["POST"])
# # def db_description():
# #     data = request.json
# #     db_name = data.get("db_name")
# #     try:
# #         with connect_db(db_name) as conn:
# #             schema_info = get_schema_info(conn)

# #         schema_lower = {
# #             k.lower(): [{'name': c['name'].lower(), 'type': c['type']} for c in v]
# #             for k, v in schema_info.items()
# #         }

# #         system_message = {
# #             "role": "system",
# #             "content": (
# #                 "You are a helpful assistant that summarizes database schemas "
# #                 "in simple English for laymen. Keep it short and clear."
# #             )
# #         }
# #         user_message = {
# #             "role": "user",
# #             "content": (
# #                 f"Schema:\n{schema_lower}\n\n"
# #                 "Provide a 2–3 line description of what this database is about "
# #                 "and what kind of information it stores."
# #             )
# #         }

# #         resp = groq_client.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[system_message, user_message]
# #         )

# #         description = resp.choices[0].message.content.strip()
# #         return jsonify({"description": description})

# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/ask", methods=["POST"])
# # def ask():
# #     data = request.json
# #     db_name = data.get("db_name")
# #     question = data.get("question")
# #     try:
# #         with connect_db(db_name) as conn:
# #             schema_info = get_schema_info(conn)
# #             sql_query = generate_sql_with_groq(question, schema_info)

# #             sql_query = fix_sql_string_literals(sql_query)

# #             result = run_sql(conn, sql_query)
# #         return jsonify({"sql": sql_query, "result": result})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/create_db", methods=["POST"])
# # def create_db():
# #     data = request.json
# #     db_name = data.get("db_name")
# #     prompt = data.get("prompt")
# #     if not db_name.endswith(".db"):
# #         db_name += ".db"
# #     db_path = get_db_path(db_name)
# #     if os.path.exists(db_path):
# #         return jsonify({"error": "Database already exists!"}), 400
# #     try:
# #         system_message = {
# #             "role": "system",
# #             "content": "You are a SQL assistant. Generate only SQL CREATE TABLE statements based on the user's description. Do not add data, comments or explanation."
# #         }
# #         user_message = {"role": "user", "content": prompt}
# #         resp = groq_client.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[system_message, user_message]
# #         )
# #         sql_schema = resp.choices[0].message.content.strip()
# #         if sql_schema.startswith("```sql"):
# #             sql_schema = sql_schema.strip("```sql").strip("```").strip()
# #         with sqlite3.connect(db_path, timeout=10) as conn:
# #             conn.execute("PRAGMA journal_mode=WAL;")
# #             conn.executescript(sql_schema)
# #             conn.commit()
# #         return jsonify({"status": "Database created", "sql_schema": sql_schema})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/add_row", methods=["POST"])
# # def add_row():
# #     data = request.json
# #     db_name = data.get("db_name")
# #     table_name = data.get("table")
# #     values_text = data.get("values")
# #     try:
# #         with connect_db(db_name) as conn:
# #             cursor = conn.cursor()
# #             schema = get_schema_info(conn)
# #             table_key = table_name.lower()
# #             if table_key not in schema:
# #                 return jsonify({"error": f"Table {table_name} not found!"}), 400

# #             columns = [c["name"] for c in schema[table_key]]

# #             raw_values = values_text.strip()
# #             values = [v.strip() for v in raw_values.split(",")]

# #             if len(values) != len(columns):
# #                 return jsonify({"error": f"Expected {len(columns)} values, got {len(values)}"}), 400

# #             placeholders = ",".join("?" * len(values))
# #             sql = f'INSERT INTO "{table_key}" ({",".join(columns)}) VALUES ({placeholders})'

# #             cursor.execute(sql, values)
# #             conn.commit()

# #         return jsonify({"status": "Row added"})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/delete_row", methods=["POST"])
# # def delete_row():
# #     data = request.json
# #     db_name  = data.get("db_name")
# #     table    = data.get("table")
# #     condition = data.get("condition")

# #     if not all([db_name, table, condition]):
# #         return jsonify({"error": "db_name, table and condition are required"}), 400

# #     try:
# #         with connect_db(db_name) as conn:
# #             cur = conn.cursor()

# #             cur.execute(f'PRAGMA table_info("{table}")')
# #             cols_info = cur.fetchall()
# #             valid_cols = {row[1] for row in cols_info}
# #             pk_cols    = [row[1] for row in cols_info if row[5] == 1]  # primary key(s)

# #             left_side = condition.split('=')[0].strip().strip('"')

# #             if left_side not in valid_cols and len(pk_cols) == 1:
# #                 pk = pk_cols[0]
# #                 condition = condition.replace(left_side, pk, 1)

# #             left_side_final = condition.split('=')[0].strip().strip('"')
# #             if left_side_final not in valid_cols:
# #                 return jsonify({"error": f"Invalid column name: {left_side_final}"}), 400

# #             sql = f'DELETE FROM "{table}" WHERE {condition}'
# #             cur.execute(sql)
# #             conn.commit()

# #         return jsonify({"status": "Row deleted", "rows_affected": cur.rowcount})

# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/connect_db", methods=["POST"])
# # def connect_db_route():
# #     data = request.json
# #     db_type = data.get("db_type")
# #     conn_info = data.copy()
# #     conn_info.pop("db_type", None)
# #     try:
# #         conn = get_connection(db_type, **conn_info)
# #         schema = get_schema(conn, db_type)
# #         conn.close()
# #         return jsonify({"schema": schema})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # # ---------- Stripe Integration ----------
# # PLANS = {
# #     # plan_id : (nickname, price_cents)
# #     "basic": ("Basic", 1000),     # $10.00 / month
# #     "standard": ("Standard", 1500),# $15.00 / month
# #     "premium": ("Premium", 2500)  # $25.00 / month
# # }

# # @app.route("/stripe_config", methods=["GET"])
# # def stripe_config():
# #     """Return publishable key for front-end to use."""
# #     return jsonify({
# #         "publishableKey": STRIPE_PUBLISHABLE_KEY or "",
# #         "plans": {k: {"nickname": v[0], "amount_cents": v[1]} for k, v in PLANS.items()}
# #     })

# # @app.route("/create-checkout-session", methods=["POST"])
# # def create_checkout_session():
# #     if not STRIPE_SECRET_KEY:
# #         return jsonify({"error": "Stripe secret key not configured on server."}), 500

# #     data = request.json or {}
# #     plan = data.get("plan")
# #     email = data.get("email")  # optional: prefill customer email

# #     if plan not in PLANS:
# #         return jsonify({"error": "Invalid plan"}), 400

# #     nickname, amount_cents = PLANS[plan]

# #     domain_url = request.host_url.rstrip("/")

# #     try:
# #         # Create a Checkout Session with inline price_data for a recurring monthly subscription
# #         session = stripe.checkout.Session.create(
# #             payment_method_types=["card"],
# #             mode="subscription",
# #             line_items=[{
# #                 "price_data": {
# #                     "currency": "usd",
# #                     "product_data": {"name": f"SQL Playground - {nickname} Plan"},
# #                     "recurring": {"interval": "month"},
# #                     "unit_amount": amount_cents
# #                 },
# #                 "quantity": 1
# #             }],
# #             success_url=domain_url + "/?checkout=success&session_id={CHECKOUT_SESSION_ID}",
# #             cancel_url=domain_url + "/?checkout=cancelled",
# #             customer_email=email if email else None,
# #             allow_promotion_codes=True
# #         )
# #         return jsonify({"url": session.url, "id": session.id})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/stripe_webhook", methods=["POST"])
# # def stripe_webhook():
# #     # For local testing with stripe CLI you can set STRIPE_WEBHOOK_SECRET and verify signature.
# #     payload = request.data
# #     sig_header = request.headers.get("Stripe-Signature", None)
# #     event = None

# #     if STRIPE_WEBHOOK_SECRET and sig_header:
# #         try:
# #             event = stripe.Webhook.construct_event(
# #                 payload=payload, sig_header=sig_header, secret=STRIPE_WEBHOOK_SECRET
# #             )
# #         except ValueError as e:
# #             # Invalid payload
# #             return jsonify({"error": "Invalid payload"}), 400
# #         except stripe.error.SignatureVerificationError as e:
# #             return jsonify({"error": "Invalid signature"}), 400
# #     else:
# #         # No webhook secret configured -- try to parse but warn
# #         try:
# #             event = json.loads(payload)
# #         except Exception as e:
# #             return jsonify({"error": "Invalid payload and no webhook secret configured."}), 400

# #     # Handle the event
# #     evt_type = event.get("type")
# #     data_obj = event.get("data", {}).get("object", {})

# #     # Handle a few subscription events
# #     if evt_type in ("checkout.session.completed", "invoice.paid", "customer.subscription.created", "customer.subscription.updated", "invoice.payment_failed"):
# #         # Note: implement storing subscription/customer details in your DB if needed
# #         print(f"Received Stripe event: {evt_type}")
# #         # Example: log to a local sqlite table `stripe_events` (create if not exists)
# #         try:
# #             db_path = get_db_path("stripe_events.db")
# #             conn = sqlite3.connect(db_path, timeout=10)
# #             conn.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, type TEXT, payload TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
# #             evt_id = event.get("id", "")
# #             conn.execute("INSERT OR REPLACE INTO events (id, type, payload) VALUES (?, ?, ?)",
# #                          (evt_id, evt_type, json.dumps(event)))
# #             conn.commit()
# #             conn.close()
# #         except Exception as e:
# #             print("Failed to log stripe event:", e)

# #     # Return a 200 to acknowledge receipt of the event
# #     return jsonify({"status": "success"})

# # # ---------- Start server ----------
# # if __name__ == "__main__":
# #     # Open browser after a short delay
# #     threading.Timer(
# #         1.5,
# #         lambda: webbrowser.open("http://127.0.0.1:5000/")
# #     ).start()

# #     app.run(host="0.0.0.0", port=5000, debug=True)


# # import os
# # import sqlite3
# # import threading
# # import webbrowser
# # import json
# # import re
# # from flask import Flask, request, render_template, jsonify, url_for, session
# # from groq import Groq
# # import pymysql
# # import psycopg2
# # from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# # import bcrypt
# # import stripe
# # from authlib.integrations.flask_client import OAuth
# # # ---------- Config & Keys ----------
# # GROQ_API_KEY = os.environ.get(
# #     "GROQ_API_KEY",
# #     "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"
# # )
# # if GROQ_API_KEY == "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":
# #     print("Warning: Set your GROQ_API_KEY environment variable!")

# # groq_client = Groq(api_key=GROQ_API_KEY)

# # STRIPE_SECRET_KEY = "sk_test_51SCZrEBHO8g2Q8ZQjcKLrhyyvXwjPHfjANMf2ppwxrkZTMrroWLWxI6s6KfWV3tGQZzz9VqG0nA8pySzJK1njZSr002baWcZmf"
# # STRIPE_PUBLISHABLE_KEY = "pk_test_51SCZrEBHO8g2Q8ZQ0P7oN581Q1Fq3l0VzzpLv8yroTjAV1DIFnhV64bMLjyfDh0Kp6Snf2oKHNi2xUC3TEu4zJxl00yE3q5phJ"
# # STRIPE_WEBHOOK_SECRET = "whsec_d089c53f00ae2edbea1e23f8fc82d24c2d5b821940b28be5e43fdb6aa52f42f7"

# # if not STRIPE_SECRET_KEY:
# #     print("Warning: STRIPE_SECRET_KEY not set. Stripe endpoints will raise errors until set.")
# # else:
# #     stripe.api_key = STRIPE_SECRET_KEY
# # # OAuth Configuration
# # GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-google-client-id")
# # GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
# # GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "your-github-client-id")
# # GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "your-github-client-secret")
# # DB_FOLDER = "databases"
# # os.makedirs(DB_FOLDER, exist_ok=True)
# # app = Flask(__name__, static_folder=".", template_folder=".")
# # app.secret_key = os.urandom(24)  # Required for sessions

# # # OAuth Setup
# # oauth = OAuth(app)
# # google = oauth.register(
# #     name='google',
# #     client_id=GOOGLE_CLIENT_ID,
# #     client_secret=GOOGLE_CLIENT_SECRET,
# #     authorize_url='https://accounts.google.com/o/oauth2/auth',
# #     access_token_url='https://accounts.google.com/o/oauth2/token',
# #     api_base_url='https://www.googleapis.com/oauth2/v1/',
# #     client_kwargs={'scope': 'email profile'},
# # )
# # github = oauth.register(
# #     name='github',
# #     client_id=GITHUB_CLIENT_ID,
# #     client_secret=GITHUB_CLIENT_SECRET,
# #     authorize_url='https://github.com/login/oauth/authorize',
# #     access_token_url='https://github.com/login/oauth/access_token',
# #     api_base_url='https://api.github.com/',
# #     client_kwargs={'scope': 'user:email'},
# # )

# # # ---------- User Database Setup ----------
# # USER_DB = "users.db"

# # def init_user_db():
# #     with sqlite3.connect(USER_DB) as conn:
# #         conn.execute("""
# #             CREATE TABLE IF NOT EXISTS users (
# #                 id INTEGER PRIMARY KEY AUTOINCREMENT,
# #                 email TEXT UNIQUE NOT NULL,
# #                 password TEXT NOT NULL,
# #                 subscription_tier TEXT DEFAULT 'premium'
# #             )
# #         """)
# #         conn.execute("""
# #             CREATE TABLE IF NOT EXISTS user_dbs (
# #                 user_id INTEGER,
# #                 db_name TEXT,
# #                 db_type TEXT,
# #                 db_path TEXT,
# #                 FOREIGN KEY (user_id) REFERENCES users(id)
# #             )
# #         """)
# #         conn.commit()

# # init_user_db()

# # # ---------- Flask-Login Setup ----------
# # login_manager = LoginManager()
# # login_manager.init_app(app)
# # login_manager.login_view = "login"

# # class User(UserMixin):
# #     def __init__(self, id, email, subscription_tier):
# #         self.id = id
# #         self.email = email
# #         self.subscription_tier = subscription_tier

# # @login_manager.user_loader
# # def load_user(user_id):
# #     with sqlite3.connect(USER_DB) as conn:
# #         cursor = conn.cursor()
# #         cursor.execute("SELECT id, email, subscription_tier FROM users WHERE id = ?", (user_id,))
# #         user = cursor.fetchone()
# #         if user:
# #             return User(user[0], user[1], user[2])
# #         return None

# # @app.route("/signup", methods=["POST"])
# # def signup():
# #     data = request.json
# #     email = data.get("email")
# #     password = data.get("password")
# #     if not email or not password:
# #         return jsonify({"error": "Email and password are required"}), 400
# #     try:
# #         hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("INSERT INTO users (email, password, subscription_tier) VALUES (?, ?, 'premium')", (email, hashed))
# #             conn.commit()
# #             cursor.execute("SELECT id, email, subscription_tier FROM users WHERE email = ?", (email,))
# #             user = cursor.fetchone()
# #             login_user(User(user[0], user[1], user[2]))
# #         return jsonify({"status": "User created", "tier": "premium"})
# #     except sqlite3.IntegrityError:
# #         return jsonify({"error": "Email already exists"}), 400
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400
    

    
# # @app.route("/login", methods=["POST"])
# # def login():
# #     data = request.json
# #     email = data.get("email")
# #     password = data.get("password")
# #     if not email or not password:
# #         return jsonify({"error": "Email and password are required"}), 400
# #     try:
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("SELECT id, email, password, subscription_tier FROM users WHERE email = ?", (email,))
# #             user = cursor.fetchone()
# #             if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
# #                 login_user(User(user[0], user[1], user[3]))
# #                 return jsonify({"status": "Logged in", "tier": user[3]})
# #             return jsonify({"error": "Invalid credentials"}), 401
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/logout", methods=["POST"])
# # @login_required
# # def logout():
# #     logout_user()
# #     return jsonify({"status": "Logged out"})

# # @app.route("/user_info", methods=["GET"])
# # def user_info():
# #     if current_user.is_authenticated:
# #         return jsonify({"email": current_user.email, "tier": current_user.subscription_tier})
# #     return jsonify({"error": "Not logged in"}), 401

# # # ---------- DB & Groq Utilities ----------
# # def get_db_path(db_name):
# #     return os.path.join(DB_FOLDER, db_name)

# # def connect_db(db_name):
# #     """Connect to SQLite database (case-insensitive for text)."""
# #     path = get_db_path(db_name)
# #     if not os.path.exists(path):
# #         raise ValueError(f"Database {db_name} not found!")
# #     conn = sqlite3.connect(path, timeout=10)
# #     conn.execute("PRAGMA journal_mode=WAL;")
# #     conn.execute("PRAGMA case_sensitive_like = OFF;")
# #     conn.row_factory = sqlite3.Row
# #     return conn

# # def get_schema_info(conn):
# #     """Return schema with lowercase table and column names."""
# #     cursor = conn.cursor()
# #     tables = cursor.execute(
# #         "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
# #     ).fetchall()
# #     schema = {}
# #     for (table_name,) in tables:
# #         cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
# #         schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
# #     return schema

# # def generate_sql_with_groq(user_prompt, schema_info):
# #     system_message = {
# #         "role": "system",
# #         "content": (
# #             "You are a SQL assistant. Your job is to translate natural language questions into SQL queries.\n"
# #             "STRICT RULES:\n"
# #             "1. Only return a valid SQL query — do NOT include explanations, formatting, markdown, or backticks.\n"
# #             "2. Always wrap string comparisons in LOWER() for case-insensitive matching. Example: "
# #             "WHERE LOWER(students.name) = 'john'.\n"
# #             "3. If multiple tables have a 'name' column (e.g., students, courses, departments), "
# #             "always prefix with the table name and alias it properly. Example: "
# #             "students.name AS student_name, courses.name AS course_name.\n"
# #             "4. Avoid SELECT * — explicitly list columns with clear aliases.\n"
# #             "Your output must ONLY be pure SQL that can be executed directly"
# #         )
# #     }
# #     user_message = {
# #         "role": "user",
# #         "content": f"Schema:\n{schema_info}\n\nQuestion: {user_prompt}"
# #     }
# #     resp = groq_client.chat.completions.create(
# #         model="llama-3.3-70b-versatile",
# #         messages=[system_message, user_message]
# #     )
# #     sql_query = resp.choices[0].message.content.strip()
# #     if sql_query.startswith("```sql"):
# #         sql_query = sql_query.strip("```sql").strip("```").strip()
# #     return sql_query

# # def fix_sql_string_literals(sql):
# #     pattern = r"(LOWER\([^)]+\)\s*=\s*)([^\s'\"()]+)"
# #     def replacer(match):
# #         return f"{match.group(1)}'{match.group(2)}'"
# #     return re.sub(pattern, replacer, sql, flags=re.IGNORECASE)

# # def run_sql(conn, query):
# #     try:
# #         cursor = conn.cursor()
# #         cursor.execute(query)
# #         rows = cursor.fetchall()
# #         cols = [desc[0] for desc in cursor.description] if cursor.description else []
# #         results = [dict(row) for row in rows]
# #         return {"columns": cols, "rows": results}
# #     except Exception as e:
# #         return {"error": str(e)}

# # def get_connection(db_type, **kwargs):
# #     """Return DB connection (SQLite, MySQL, PostgreSQL)"""
# #     if db_type.lower() == "sqlite":
# #         path = kwargs.get("path")
# #         if not os.path.exists(path):
# #             raise ValueError("SQLite DB file not found!")
# #         conn = sqlite3.connect(path, timeout=10)
# #         conn.row_factory = sqlite3.Row
# #         conn.execute("PRAGMA journal_mode=WAL;")
# #         conn.execute("PRAGMA case_sensitive_like = OFF;")
# #         return conn
# #     elif db_type.lower() == "mysql":
# #         conn = pymysql.connect(
# #             host=kwargs.get("host"),
# #             port=int(kwargs.get("port", 3306)),
# #             user=kwargs.get("user"),
# #             password=kwargs.get("password"),
# #             database=kwargs.get("database"),
# #             charset='utf8mb4',
# #             cursorclass=pymysql.cursors.DictCursor
# #         )
# #         return conn
# #     elif db_type.lower() == "postgresql":
# #         conn = psycopg2.connect(
# #             host=kwargs.get("host"),
# #             port=int(kwargs.get("port", 5432)),
# #             user=kwargs.get("user"),
# #             password=kwargs.get("password"),
# #             dbname=kwargs.get("database")
# #         )
# #         return conn
# #     else:
# #         raise ValueError(f"Unsupported DB type: {db_type}")

# # def get_schema(conn, db_type):
# #     """Return schema for any DB with lowercase table/column names"""
# #     schema = {}
# #     cursor = conn.cursor()
# #     if db_type.lower() == "sqlite":
# #         tables = cursor.execute(
# #             "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
# #         ).fetchall()
# #         for (table_name,) in tables:
# #             cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
# #             schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
# #     elif db_type.lower() == "mysql":
# #         cursor.execute("SHOW TABLES;")
# #         tables = [list(row.values())[0] for row in cursor.fetchall()]
# #         for table in tables:
# #             cursor.execute(f"DESCRIBE {table};")
# #             cols = cursor.fetchall()
# #             schema[table.lower()] = [{"name": c['Field'].lower(), "type": c['Type']} for c in cols]
# #     elif db_type.lower() == "postgresql":
# #         cursor.execute(
# #             "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
# #         )
# #         tables = [row[0] for row in cursor.fetchall()]
# #         for table in tables:
# #             cursor.execute(
# #                 f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';"
# #             )
# #             cols = cursor.fetchall()
# #             schema[table.lower()] = [{"name": c[0].lower(), "type": c[1]} for c in cols]
# #     return schema

# # # ---------- Routes ----------
# # @app.route("/")
# # def index():
# #     return render_template("index.html")

# # @app.route("/databases", methods=["GET"])
# # @login_required
# # def list_databases():
# #     try:
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("SELECT db_name FROM user_dbs WHERE user_id = ?", (current_user.id,))
# #             dbs = [row[0] for row in cursor.fetchall()]
# #         return jsonify({"databases": dbs})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/schema", methods=["POST"])
# # @login_required
# # def schema():
# #     data = request.json
# #     db_name = data.get("db_name")
# #     try:
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
# #             db_info = cursor.fetchone()
# #             if not db_info:
# #                 return jsonify({"error": "Database not found or not owned by user"}), 403
# #         db_type, db_path = db_info
# #         if db_type == "sqlite":
# #             with connect_db(db_name) as conn:
# #                 schema_info = get_schema_info(conn)
# #         else:
# #             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
# #             schema_info = get_schema(conn, db_type)
# #             conn.close()
# #         return jsonify({"schema": schema_info})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/visualize", methods=["POST"])
# # @login_required
# # def visualize():
# #     if current_user.subscription_tier != "premium":
# #         return jsonify({"error": "Premium subscription required for visualization"}), 403
# #     data = request.json
# #     db_name = data.get("db_name")
# #     prompt = data.get("prompt")
# #     try:
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
# #             db_info = cursor.fetchone()
# #             if not db_info:
# #                 return jsonify({"error": "Database not found or not owned by user"}), 403
# #         db_type, db_path = db_info
# #         if db_type == "sqlite":
# #             conn = connect_db(db_name)
# #         else:
# #             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
# #         schema_info = get_schema(conn, db_type)
# #         sql_query = generate_sql_with_groq(prompt, schema_info)
# #         result = run_sql(conn, sql_query)
# #         conn.close()
# #         if result.get("error"):
# #             return jsonify({"error": result["error"]}), 400
# #         user_msg = {
# #             "role": "user",
# #             "content": (
# #                 f"Here is the data returned by SQL:\n"
# #                 f"Columns: {result['columns']}\nRows: {result['rows'][:5]}...\n\n"
# #                 "Write 2-3 concise sentences summarizing the key insights "
# #                 "for a professional data visualization caption."
# #             )
# #         }
# #         resp = groq_client.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[{"role": "system", "content": "You are a data analyst."}, user_msg]
# #         )
# #         summary = resp.choices[0].message.content.strip()
# #         return jsonify({
# #             "sql": sql_query,
# #             "columns": result["columns"],
# #             "rows": result["rows"],
# #             "summary": summary
# #         })
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/db_description", methods=["POST"])
# # @login_required
# # def db_description():
# #     data = request.json
# #     db_name = data.get("db_name")
# #     try:
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
# #             db_info = cursor.fetchone()
# #             if not db_info:
# #                 return jsonify({"error": "Database not found or not owned by user"}), 403
# #         db_type, db_path = db_info
# #         if db_type == "sqlite":
# #             conn = connect_db(db_name)
# #         else:
# #             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
# #         schema_info = get_schema(conn, db_type)
# #         conn.close()
# #         schema_lower = {
# #             k.lower(): [{'name': c['name'].lower(), 'type': c['type']} for c in v]
# #             for k, v in schema_info.items()
# #         }
# #         system_message = {
# #             "role": "system",
# #             "content": (
# #                 "You are a helpful assistant that summarizes database schemas "
# #                 "in simple English for laymen. Keep it short and clear."
# #             )
# #         }
# #         user_message = {
# #             "role": "user",
# #             "content": (
# #                 f"Schema:\n{schema_lower}\n\n"
# #                 "Provide a 2–3 line description of what this database is about "
# #                 "and what kind of information it stores."
# #             )
# #         }
# #         resp = groq_client.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[system_message, user_message]
# #         )
# #         description = resp.choices[0].message.content.strip()
# #         return jsonify({"description": description})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/ask", methods=["POST"])
# # @login_required
# # def ask():
# #     if current_user.subscription_tier not in ["standard", "premium"]:
# #         return jsonify({"error": "Standard or Premium subscription required for querying"}), 403
# #     data = request.json
# #     db_name = data.get("db_name")
# #     question = data.get("question")
# #     try:
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
# #             db_info = cursor.fetchone()
# #             if not db_info:
# #                 return jsonify({"error": "Database not found or not owned by user"}), 403
# #         db_type, db_path = db_info
# #         if db_type == "sqlite":
# #             conn = connect_db(db_name)
# #         else:
# #             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
# #         schema_info = get_schema(conn, db_type)
# #         sql_query = generate_sql_with_groq(question, schema_info)
# #         sql_query = fix_sql_string_literals(sql_query)
# #         result = run_sql(conn, sql_query)
# #         conn.close()
# #         return jsonify({"sql": sql_query, "result": result})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/create_db", methods=["POST"])
# # @login_required
# # def create_db():
# #     if current_user.subscription_tier not in ["free" ,"basic", "standard", "premium"]:
# #         return jsonify({"error": "free, Basic, Standard, or Premium subscription required for creating databases"}), 403
# #     data = request.json
# #     db_name = data.get("db_name")
# #     prompt = data.get("prompt")
# #     if not db_name.endswith(".db"):
# #         db_name += ".db"
# #     db_path = get_db_path(db_name)
# #     if os.path.exists(db_path):
# #         return jsonify({"error": "Database already exists!"}), 400
# #     try:
# #         system_message = {
# #             "role": "system",
# #             "content": "You are a SQL assistant. Generate only SQL CREATE TABLE statements based on the user's description. Do not add data, comments or explanation."
# #         }
# #         user_message = {"role": "user", "content": prompt}
# #         resp = groq_client.chat.completions.create(
# #             model="llama-3.3-70b-versatile",
# #             messages=[system_message, user_message]
# #         )
# #         sql_schema = resp.choices[0].message.content.strip()
# #         if sql_schema.startswith("```sql"):
# #             sql_schema = sql_schema.strip("```sql").strip("```").strip()
# #         with sqlite3.connect(db_path, timeout=10) as conn:
# #             conn.execute("PRAGMA journal_mode=WAL;")
# #             conn.executescript(sql_schema)
# #             conn.commit()
# #         with sqlite3.connect(USER_DB) as conn:
# #             conn.execute("INSERT INTO user_dbs (user_id, db_name, db_type, db_path) VALUES (?, ?, ?, ?)",
# #                          (current_user.id, db_name, "sqlite", db_path))
# #             conn.commit()
# #         return jsonify({"status": "Database created", "sql_schema": sql_schema})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/add_row", methods=["POST"])
# # @login_required
# # def add_row():
# #     if current_user.subscription_tier not in ["basic", "standard", "premium"]:
# #         return jsonify({"error": "Basic, Standard, or Premium subscription required for managing rows"}), 403
# #     data = request.json
# #     db_name = data.get("db_name")
# #     table_name = data.get("table")
# #     values_text = data.get("values")
# #     try:
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
# #             db_info = cursor.fetchone()
# #             if not db_info:
# #                 return jsonify({"error": "Database not found or not owned by user"}), 403
# #         db_type, db_path = db_info
# #         if db_type == "sqlite":
# #             conn = connect_db(db_name)
# #         else:
# #             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
# #         cursor = conn.cursor()
# #         schema = get_schema_info(conn) if db_type == "sqlite" else get_schema(conn, db_type)
# #         table_key = table_name.lower()
# #         if table_key not in schema:
# #             conn.close()
# #             return jsonify({"error": f"Table {table_name} not found!"}), 400
# #         columns = [c["name"] for c in schema[table_key]]
# #         raw_values = values_text.strip()
# #         values = [v.strip() for v in raw_values.split(",")]
# #         if len(values) != len(columns):
# #             conn.close()
# #             return jsonify({"error": f"Expected {len(columns)} values, got {len(values)}"}), 400
# #         placeholders = ",".join("?" * len(values))
# #         sql = f'INSERT INTO "{table_key}" ({",".join(columns)}) VALUES ({placeholders})'
# #         cursor.execute(sql, values)
# #         conn.commit()
# #         conn.close()
# #         return jsonify({"status": "Row added"})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/delete_row", methods=["POST"])
# # @login_required
# # def delete_row():
# #     if current_user.subscription_tier not in ["basic", "standard", "premium"]:
# #         return jsonify({"error": "Basic, Standard, or Premium subscription required for managing rows"}), 403
# #     data = request.json
# #     db_name = data.get("db_name")
# #     table = data.get("table")
# #     condition = data.get("condition")
# #     if not all([db_name, table, condition]):
# #         return jsonify({"error": "db_name, table and condition are required"}), 400
# #     try:
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
# #             db_info = cursor.fetchone()
# #             if not db_info:
# #                 return jsonify({"error": "Database not found or not owned by user"}), 403
# #         db_type, db_path = db_info
# #         if db_type == "sqlite":
# #             conn = connect_db(db_name)
# #         else:
# #             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
# #         cur = conn.cursor()
# #         cur.execute(f'PRAGMA table_info("{table}")')
# #         cols_info = cur.fetchall()
# #         valid_cols = {row[1] for row in cols_info}
# #         pk_cols = [row[1] for row in cols_info if row[5] == 1]
# #         left_side = condition.split('=')[0].strip().strip('"')
# #         if left_side not in valid_cols and len(pk_cols) == 1:
# #             pk = pk_cols[0]
# #             condition = condition.replace(left_side, pk, 1)
# #         left_side_final = condition.split('=')[0].strip().strip('"')
# #         if left_side_final not in valid_cols:
# #             conn.close()
# #             return jsonify({"error": f"Invalid column name: {left_side_final}"}), 400
# #         sql = f'DELETE FROM "{table}" WHERE {condition}'
# #         cur.execute(sql)
# #         conn.commit()
# #         conn.close()
# #         return jsonify({"status": "Row deleted", "rows_affected": cur.rowcount})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/connect_db", methods=["POST"])
# # @login_required
# # def connect_db_route():
# #     data = request.json
# #     db_type = data.get("db_type")
# #     db_name = data.get("db_name", data.get("database", "remote_db"))
# #     conn_info = data.copy()
# #     conn_info.pop("db_type", None)
# #     try:
# #         conn = get_connection(db_type, **conn_info)
# #         schema = get_schema(conn, db_type)
# #         conn.close()
# #         with sqlite3.connect(USER_DB) as conn:
# #             cursor = conn.cursor()
# #             cursor.execute("INSERT INTO user_dbs (user_id, db_name, db_type, db_path) VALUES (?, ?, ?, ?)",
# #                           (current_user.id, db_name, db_type, conn_info.get("path", "")))
# #             conn.commit()
# #         return jsonify({"schema": schema})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # # ---------- Stripe Integration ----------
# # PLANS = {
# #     "basic": ("Basic", 1000),
# #     "standard": ("Standard", 1500),
# #     "premium": ("Premium", 2500)
# # }

# # @app.route("/stripe_config", methods=["GET"])
# # def stripe_config():
# #     return jsonify({
# #         "publishableKey": STRIPE_PUBLISHABLE_KEY or "",
# #         "plans": {k: {"nickname": v[0], "amount_cents": v[1]} for k, v in PLANS.items()}
# #     })

# # @app.route("/create-checkout-session", methods=["POST"])
# # @login_required
# # def create_checkout_session():
# #     if not STRIPE_SECRET_KEY:
# #         return jsonify({"error": "Stripe secret key not configured on server."}), 500
# #     data = request.json or {}
# #     plan = data.get("plan")
# #     email = data.get("email") or current_user.email
# #     if plan not in PLANS:
# #         return jsonify({"error": "Invalid plan"}), 400
# #     nickname, amount_cents = PLANS[plan]
# #     domain_url = request.host_url.rstrip("/")
# #     try:
# #         session = stripe.checkout.Session.create(
# #             payment_method_types=["card"],
# #             mode="subscription",
# #             line_items=[{
# #                 "price_data": {
# #                     "currency": "usd",
# #                     "product_data": {"name": f"SQL Playground - {nickname} Plan"},
# #                     "recurring": {"interval": "month"},
# #                     "unit_amount": amount_cents
# #                 },
# #                 "quantity": 1
# #             }],
# #             success_url=domain_url + "/?checkout=success&session_id={CHECKOUT_SESSION_ID}",
# #             cancel_url=domain_url + "/?checkout=cancelled",
# #             customer_email=email,
# #             allow_promotion_codes=True,
# #             metadata={"user_id": str(current_user.id)}
# #         )
# #         return jsonify({"url": session.url, "id": session.id})
# #     except Exception as e:
# #         return jsonify({"error": str(e)}), 400

# # @app.route("/stripe_webhook", methods=["POST"])
# # def stripe_webhook():
# #     payload = request.data
# #     sig_header = request.headers.get("Stripe-Signature", None)
# #     event = None
# #     if STRIPE_WEBHOOK_SECRET and sig_header:
# #         try:
# #             event = stripe.Webhook.construct_event(
# #                 payload=payload, sig_header=sig_header, secret=STRIPE_WEBHOOK_SECRET
# #             )
# #         except ValueError as e:
# #             return jsonify({"error": "Invalid payload"}), 400
# #         except stripe.error.SignatureVerificationError as e:
# #             return jsonify({"error": "Invalid signature"}), 400
# #     else:
# #         try:
# #             event = json.loads(payload)
# #         except Exception as e:
# #             return jsonify({"error": "Invalid payload and no webhook secret configured."}), 400
# #     evt_type = event.get("type")
# #     data_obj = event.get("data", {}).get("object", {})
# #     if evt_type in ("checkout.session.completed", "customer.subscription.created", "customer.subscription.updated"):
# #         user_id = data_obj.get("metadata", {}).get("user_id")
# #         if user_id:
# #             plan = None
# #             for p, (nickname, _) in PLANS.items():
# #                 if f"SQL Playground - {nickname} Plan" in str(data_obj):
# #                     plan = p
# #                     break
# #             if plan:
# #                 with sqlite3.connect(USER_DB) as conn:
# #                     conn.execute("UPDATE users SET subscription_tier = ? WHERE id = ?", (plan, user_id))
# #                     conn.commit()
# #     try:
# #         db_path = get_db_path("stripe_events.db")
# #         conn = sqlite3.connect(db_path, timeout=10)
# #         conn.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, type TEXT, payload TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
# #         evt_id = event.get("id", "")
# #         conn.execute("INSERT OR REPLACE INTO events (id, type, payload) VALUES (?, ?, ?)",
# #                      (evt_id, evt_type, json.dumps(event)))
# #         conn.commit()
# #         conn.close()
# #     except Exception as e:
# #         print("Failed to log stripe event:", e)
# #     return jsonify({"status": "success"})

# # # ---------- Start server ----------
# # if __name__ == "__main__":
# #     threading.Timer(
# #         1.5,
# #         lambda: webbrowser.open("http://127.0.0.1:5000/")
# #     ).start()
# #     app.run(host="0.0.0.0", port=5000, debug=True)

# import os
# import sqlite3
# import threading
# import webbrowser
# import json
# import re
# from flask import Flask, request, render_template, jsonify, url_for, session, redirect
# from groq import Groq
# import pymysql
# import psycopg2
# from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
# import bcrypt
# import stripe
# from authlib.integrations.flask_client import OAuth
# # ---------- Config & Keys ----------
# GROQ_API_KEY = os.environ.get(
#     "GROQ_API_KEY",
#     "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"
# )
# if GROQ_API_KEY == "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":
#     print("Warning: Set your GROQ_API_KEY environment variable!")

# groq_client = Groq(api_key=GROQ_API_KEY)

# STRIPE_SECRET_KEY = "sk_test_51SCZrEBHO8g2Q8ZQjcKLrhyyvXwjPHfjANMf2ppwxrkZTMrroWLWxI6s6KfWV3tGQZzz9VqG0nA8pySzJK1njZSr002baWcZmf"
# STRIPE_PUBLISHABLE_KEY = "pk_test_51SCZrEBHO8g2Q8ZQ0P7oN581Q1Fq3l0VzzpLv8yroTjAV1DIFnhV64bMLjyfDh0Kp6Snf2oKHNi2xUC3TEu4zJxl00yE3q5phJ"
# STRIPE_WEBHOOK_SECRET = "whsec_d089c53f00ae2edbea1e23f8fc82d24c2d5b821940b28be5e43fdb6aa52f42f7"

# if not STRIPE_SECRET_KEY:
#     print("Warning: STRIPE_SECRET_KEY not set. Stripe endpoints will raise errors until set.")
# else:
#     stripe.api_key = STRIPE_SECRET_KEY
# # OAuth Configuration
# GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-google-client-id")
# GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
# GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "your-github-client-id")
# GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "your-github-client-secret")
# DB_FOLDER = "databases"
# os.makedirs(DB_FOLDER, exist_ok=True)
# app = Flask(__name__, static_folder=".", template_folder=".")
# app.secret_key = os.urandom(24)  # Required for sessions

# # OAuth Setup
# oauth = OAuth(app)
# google = oauth.register(
#     name='google',
#     client_id=GOOGLE_CLIENT_ID,
#     client_secret=GOOGLE_CLIENT_SECRET,
#     authorize_url='https://accounts.google.com/o/oauth2/auth',
#     access_token_url='https://accounts.google.com/o/oauth2/token',
#     api_base_url='https://www.googleapis.com/oauth2/v1/',
#     client_kwargs={'scope': 'email profile'},
# )
# github = oauth.register(
#     name='github',
#     client_id=GITHUB_CLIENT_ID,
#     client_secret=GITHUB_CLIENT_SECRET,
#     authorize_url='https://github.com/login/oauth/authorize',
#     access_token_url='https://github.com/login/oauth/access_token',
#     api_base_url='https://api.github.com/',
#     client_kwargs={'scope': 'user:email'},
# )

# # ---------- User Database Setup ----------
# USER_DB = "users.db"

# def init_user_db():
#     with sqlite3.connect(USER_DB) as conn:
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS users (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 email TEXT UNIQUE NOT NULL,
#                 password TEXT NOT NULL,
#                 subscription_tier TEXT DEFAULT 'free'
#             )
#         """)
#         conn.execute("""
#             CREATE TABLE IF NOT EXISTS user_dbs (
#                 user_id INTEGER,
#                 db_name TEXT,
#                 db_type TEXT,
#                 db_path TEXT,
#                 FOREIGN KEY (user_id) REFERENCES users(id)
#             )
#         """)
#         conn.commit()

# init_user_db()

# # ---------- Flask-Login Setup ----------
# login_manager = LoginManager()
# login_manager.init_app(app)
# login_manager.login_view = "login_page"

# class User(UserMixin):
#     def __init__(self, id, email, subscription_tier):
#         self.id = id
#         self.email = email
#         self.subscription_tier = subscription_tier

# @login_manager.user_loader
# def load_user(user_id):
#     with sqlite3.connect(USER_DB) as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT id, email, subscription_tier FROM users WHERE id = ?", (user_id,))
#         user = cursor.fetchone()
#         if user:
#             return User(user[0], user[1], user[2])
#         return None
# @app.route("/signup", methods=["POST"])
# def signup():
#     data = request.json
#     email = data.get("email")
#     password = data.get("password")

#     if not email or not password:
#         return jsonify({"error": "Email and password are required"}), 400

#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()

#             # Check if email already exists
#             cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
#             if cursor.fetchone():
#                 return jsonify({"error": "Email already registered"}), 400

#             # Hash password
#             hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

#             # ✅ Make user premium by default
#             subscription_tier = "premium"

#             # Insert new user
#             cursor.execute("""
#                 INSERT INTO users (email, password, subscription_tier)
#                 VALUES (?, ?, ?)
#             """, (email, hashed_pw, subscription_tier))
#             conn.commit()

#             # Get user id and log in
#             user_id = cursor.lastrowid
#             user = User(user_id, email, subscription_tier)
#             login_user(user)

#             # ✅ Return success message + redirect
#             return jsonify({
#                 "status": "success",
#                 "message": "You are signed up successfully!",
#                 "tier": subscription_tier,
#                 "redirect": "/app"
#             })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/login", methods=["POST"])
# def login():
#     data = request.json
#     email = data.get("email")
#     password = data.get("password")

#     if not email or not password:
#         return jsonify({"error": "Email and password are required"}), 400

#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT id, email, password, subscription_tier FROM users WHERE email = ?", (email,))
#             user = cursor.fetchone()

#             if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
#                 login_user(User(user[0], user[1], user[3]))
                
#                 # ✅ Redirect path added here
#                 return jsonify({
#                     "status": "Logged in",
#                     "tier": user[3],
#                     "redirect": "/app"
#                 })

#             return jsonify({"error": "Invalid credentials"}), 401

#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/public_databases", methods=["GET"])
# def public_databases():
#     """List ALL databases including public ones like demo.db"""
#     # Always include demo.db for everyone
#     public_dbs = ["demo.db"]
    
#     # Get user's personal databases
#     try:
#         if current_user.is_authenticated:
#             with sqlite3.connect(USER_DB) as conn:
#                 cursor = conn.cursor()
#                 cursor.execute("SELECT db_name FROM user_dbs WHERE user_id = ?", (current_user.id,))
#                 personal_dbs = [row[0] for row in cursor.fetchall()]
#         else:
#             personal_dbs = []
#     except:
#         personal_dbs = []
    
#     # Combine and remove duplicates
#     all_dbs = list(set(public_dbs + personal_dbs))
#     return jsonify({"databases": all_dbs})

# @app.route("/logout", methods=["POST"])
# @login_required
# def logout():
#     logout_user()
#     return jsonify({"status": "Logged out"})

# @app.route("/user_info", methods=["GET"])
# def user_info():
#     if current_user.is_authenticated:
#         return jsonify({"email": current_user.email, "tier": current_user.subscription_tier})
#     return jsonify({"error": "Not logged in"}), 401

# # ---------- DB & Groq Utilities ----------
# def get_db_path(db_name):
#     return os.path.join(DB_FOLDER, db_name)

# def connect_db(db_name):
#     """Connect to SQLite database (case-insensitive for text)."""
#     path = get_db_path(db_name)
#     if not os.path.exists(path):
#         raise ValueError(f"Database {db_name} not found!")
#     conn = sqlite3.connect(path, timeout=10)
#     conn.execute("PRAGMA journal_mode=WAL;")
#     conn.execute("PRAGMA case_sensitive_like = OFF;")
#     conn.row_factory = sqlite3.Row
#     return conn

# def get_schema_info(conn):
#     """Return schema with lowercase table and column names."""
#     cursor = conn.cursor()
#     tables = cursor.execute(
#         "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
#     ).fetchall()
#     schema = {}
#     for (table_name,) in tables:
#         cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
#         schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
#     return schema

# def generate_sql_with_groq(user_prompt, schema_info):
#     system_message = {
#         "role": "system",
#         "content": (
#             "You are a SQL assistant. Your job is to translate natural language questions into SQL queries.\n"
#             "STRICT RULES:\n"
#             "1. Only return a valid SQL query — do NOT include explanations, formatting, markdown, or backticks.\n"
#             "2. Always wrap string comparisons in LOWER() for case-insensitive matching. Example: "
#             "WHERE LOWER(students.name) = 'john'.\n"
#             "3. If multiple tables have a 'name' column (e.g., students, courses, departments), "
#             "always prefix with the table name and alias it properly. Example: "
#             "students.name AS student_name, courses.name AS course_name.\n"
#             "4. Avoid SELECT * — explicitly list columns with clear aliases.\n"
#             "Your output must ONLY be pure SQL that can be executed directly"
#         )
#     }
#     user_message = {
#         "role": "user",
#         "content": f"Schema:\n{schema_info}\n\nQuestion: {user_prompt}"
#     }
#     resp = groq_client.chat.completions.create(
#         model="llama-3.3-70b-versatile",
#         messages=[system_message, user_message]
#     )
#     sql_query = resp.choices[0].message.content.strip()
#     if sql_query.startswith("```sql"):
#         sql_query = sql_query.strip("```sql").strip("```").strip()
#     return sql_query

# def fix_sql_string_literals(sql):
#     pattern = r"(LOWER\([^)]+\)\s*=\s*)([^\s'\"()]+)"
#     def replacer(match):
#         return f"{match.group(1)}'{match.group(2)}'"
#     return re.sub(pattern, replacer, sql, flags=re.IGNORECASE)

# def run_sql(conn, query):
#     try:
#         cursor = conn.cursor()
#         cursor.execute(query)
#         rows = cursor.fetchall()
#         cols = [desc[0] for desc in cursor.description] if cursor.description else []
#         results = [dict(row) for row in rows]
#         return {"columns": cols, "rows": results}
#     except Exception as e:
#         return {"error": str(e)}

# def get_connection(db_type, **kwargs):
#     """Return DB connection (SQLite, MySQL, PostgreSQL)"""
#     if db_type.lower() == "sqlite":
#         path = kwargs.get("path")
#         if not os.path.exists(path):
#             raise ValueError("SQLite DB file not found!")
#         conn = sqlite3.connect(path, timeout=10)
#         conn.row_factory = sqlite3.Row
#         conn.execute("PRAGMA journal_mode=WAL;")
#         conn.execute("PRAGMA case_sensitive_like = OFF;")
#         return conn
#     elif db_type.lower() == "mysql":
#         conn = pymysql.connect(
#             host=kwargs.get("host"),
#             port=int(kwargs.get("port", 3306)),
#             user=kwargs.get("user"),
#             password=kwargs.get("password"),
#             database=kwargs.get("database"),
#             charset='utf8mb4',
#             cursorclass=pymysql.cursors.DictCursor
#         )
#         return conn
#     elif db_type.lower() == "postgresql":
#         conn = psycopg2.connect(
#             host=kwargs.get("host"),
#             port=int(kwargs.get("port", 5432)),
#             user=kwargs.get("user"),
#             password=kwargs.get("password"),
#             dbname=kwargs.get("database")
#         )
#         return conn
#     else:
#         raise ValueError(f"Unsupported DB type: {db_type}")

# def get_schema(conn, db_type):
#     """Return schema for any DB with lowercase table/column names"""
#     schema = {}
#     cursor = conn.cursor()
#     if db_type.lower() == "sqlite":
#         tables = cursor.execute(
#             "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
#         ).fetchall()
#         for (table_name,) in tables:
#             cols = cursor.execute(f"PRAGMA table_info({table_name});").fetchall()
#             schema[table_name.lower()] = [{"name": c[1].lower(), "type": c[2]} for c in cols]
#     elif db_type.lower() == "mysql":
#         cursor.execute("SHOW TABLES;")
#         tables = [list(row.values())[0] for row in cursor.fetchall()]
#         for table in tables:
#             cursor.execute(f"DESCRIBE {table};")
#             cols = cursor.fetchall()
#             schema[table.lower()] = [{"name": c['Field'].lower(), "type": c['Type']} for c in cols]
#     elif db_type.lower() == "postgresql":
#         cursor.execute(
#             "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"
#         )
#         tables = [row[0] for row in cursor.fetchall()]
#         for table in tables:
#             cursor.execute(
#                 f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name='{table}';"
#             )
#             cols = cursor.fetchall()
#             schema[table.lower()] = [{"name": c[0].lower(), "type": c[1]} for c in cols]
#     return schema

# # ---------- Routes (REPLACE THIS SECTION ONLY) ----------
# @app.route("/")
# def index():
#     if current_user.is_authenticated:
#         return redirect("/app")
#     return redirect("/auth")

# @app.route("/auth")
# def auth_page():
#     return render_template("auth.html")
#     return redirect("/app")

# @app.route("/app")
# @login_required
# def app_page():
#     return render_template("index.html")

# # ... rest of your routes remain the same ...

# @app.route("/databases", methods=["GET"])
# @login_required
# def list_databases():
#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT db_name FROM user_dbs WHERE user_id = ?", (current_user.id,))
#             dbs = [row[0] for row in cursor.fetchall()]
#         return jsonify({"databases": dbs})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/schema", methods=["POST"])
# @login_required
# def schema():
#     data = request.json
#     db_name = data.get("db_name")
#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
#             db_info = cursor.fetchone()
#             if not db_info:
#                 return jsonify({"error": "Database not found or not owned by user"}), 403
#         db_type, db_path = db_info
#         if db_type == "sqlite":
#             with connect_db(db_name) as conn:
#                 schema_info = get_schema_info(conn)
#         else:
#             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
#             schema_info = get_schema(conn, db_type)
#             conn.close()
#         return jsonify({"schema": schema_info})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/visualize", methods=["POST"])
# @login_required
# def visualize():
#     if current_user.subscription_tier != "premium":
#         return jsonify({"error": "Premium subscription required for visualization"}), 403
#     data = request.json
#     db_name = data.get("db_name")
#     prompt = data.get("prompt")

#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
#             db_info = cursor.fetchone()
#             if not db_info:
#                 return jsonify({"error": "Database not found or not owned by user"}), 403
#         db_type, db_path = db_info
#         if db_type == "sqlite":
#             conn = connect_db(db_name)
#         else:
#             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
#         schema_info = get_schema(conn, db_type)
#         sql_query = generate_sql_with_groq(prompt, schema_info)
#         result = run_sql(conn, sql_query)
#         conn.close()
#         if result.get("error"):
#             return jsonify({"error": result["error"]}), 400
#         user_msg = {
#             "role": "user",
#             "content": (
#                 f"Here is the data returned by SQL:\n"
#                 f"Columns: {result['columns']}\nRows: {result['rows'][:5]}...\n\n"
#                 "Write 2-3 concise sentences summarizing the key insights "
#                 "for a professional data visualization caption."
#             )
#         }
#         resp = groq_client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "system", "content": "You are a data analyst."}, user_msg]
#         )
#         summary = resp.choices[0].message.content.strip()
#         return jsonify({
#             "sql": sql_query,
#             "columns": result["columns"],
#             "rows": result["rows"],
#             "summary": summary
#         })
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/db_description", methods=["POST"])
# @login_required
# def db_description():
#     data = request.json
#     db_name = data.get("db_name")
#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
#             db_info = cursor.fetchone()
#             if not db_info:
#                 return jsonify({"error": "Database not found or not owned by user"}), 403
#         db_type, db_path = db_info
#         if db_type == "sqlite":
#             conn = connect_db(db_name)
#         else:
#             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
#         schema_info = get_schema(conn, db_type)
#         conn.close()
#         schema_lower = {
#             k.lower(): [{'name': c['name'].lower(), 'type': c['type']} for c in v]
#             for k, v in schema_info.items()
#         }
#         system_message = {
#             "role": "system",
#             "content": (
#                 "You are a helpful assistant that summarizes database schemas "
#                 "in simple English for laymen. Keep it short and clear."
#             )
#         }
#         user_message = {
#             "role": "user",
#             "content": (
#                 f"Schema:\n{schema_lower}\n\n"
#                 "Provide a 2–3 line description of what this database is about "
#                 "and what kind of information it stores."
#             )
#         }

#         resp = groq_client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[system_message, user_message]
#         )

#         description = resp.choices[0].message.content.strip()
#         return jsonify({"description": description})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/ask", methods=["POST"])
# @login_required
# def ask():
#     if current_user.subscription_tier not in ["standard", "premium"]:
#         return jsonify({"error": "Standard or Premium subscription required for querying"}), 403
#     data = request.json
#     db_name = data.get("db_name")
#     question = data.get("question")
#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
#             db_info = cursor.fetchone()
#             if not db_info:
#                 return jsonify({"error": "Database not found or not owned by user"}), 403
#         db_type, db_path = db_info
#         if db_type == "sqlite":
#             conn = connect_db(db_name)
#         else:
#             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
#         schema_info = get_schema(conn, db_type)
#         sql_query = generate_sql_with_groq(question, schema_info)
#         sql_query = fix_sql_string_literals(sql_query)
#         result = run_sql(conn, sql_query)
#         conn.close()
#         return jsonify({"sql": sql_query, "result": result})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/create_db", methods=["POST"])
# @login_required
# def create_db():
#     if current_user.subscription_tier not in ["free" ,"basic", "standard", "premium"]:
#         return jsonify({"error": "free, Basic, Standard, or Premium subscription required for creating databases"}), 403
#     data = request.json
#     db_name = data.get("db_name")
#     prompt = data.get("prompt")
#     if not db_name.endswith(".db"):
#         db_name += ".db"
#     db_path = get_db_path(db_name)
#     if os.path.exists(db_path):
#         return jsonify({"error": "Database already exists!"}), 400
#     try:
#         system_message = {
#             "role": "system",
#             "content": "You are a SQL assistant. Generate only SQL CREATE TABLE statements based on the user's description. Do not add data, comments or explanation."
#         }
#         user_message = {"role": "user", "content": prompt}
#         resp = groq_client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[system_message, user_message]
#         )
#         sql_schema = resp.choices[0].message.content.strip()
#         if sql_schema.startswith("```sql"):
#             sql_schema = sql_schema.strip("```sql").strip("```").strip()
#         with sqlite3.connect(db_path, timeout=10) as conn:
#             conn.execute("PRAGMA journal_mode=WAL;")
#             conn.executescript(sql_schema)
#             conn.commit()
#         with sqlite3.connect(USER_DB) as conn:
#             conn.execute("INSERT INTO user_dbs (user_id, db_name, db_type, db_path) VALUES (?, ?, ?, ?)",
#                          (current_user.id, db_name, "sqlite", db_path))
#             conn.commit()
#         return jsonify({"status": "Database created", "sql_schema": sql_schema})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/add_row", methods=["POST"])
# @login_required
# def add_row():
#     if current_user.subscription_tier not in ["basic", "standard", "premium"]:
#         return jsonify({"error": "Basic, Standard, or Premium subscription required for managing rows"}), 403
#     data = request.json
#     db_name = data.get("db_name")
#     table_name = data.get("table")
#     values_text = data.get("values")
#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
#             db_info = cursor.fetchone()
#             if not db_info:
#                 return jsonify({"error": "Database not found or not owned by user"}), 403
#         db_type, db_path = db_info
#         if db_type == "sqlite":
#             conn = connect_db(db_name)
#         else:
#             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
#         cursor = conn.cursor()
#         schema = get_schema_info(conn) if db_type == "sqlite" else get_schema(conn, db_type)
#         table_key = table_name.lower()
#         if table_key not in schema:
#             conn.close()
#             return jsonify({"error": f"Table {table_name} not found!"}), 400
#         columns = [c["name"] for c in schema[table_key]]
#         raw_values = values_text.strip()
#         values = [v.strip() for v in raw_values.split(",")]
#         if len(values) != len(columns):
#             conn.close()
#             return jsonify({"error": f"Expected {len(columns)} values, got {len(values)}"}), 400
#         placeholders = ",".join("?" * len(values))
#         sql = f'INSERT INTO "{table_key}" ({",".join(columns)}) VALUES ({placeholders})'
#         cursor.execute(sql, values)
#         conn.commit()
#         conn.close()
#         return jsonify({"status": "Row added"})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/delete_row", methods=["POST"])
# @login_required
# def delete_row():
#     if current_user.subscription_tier not in ["basic", "standard", "premium"]:
#         return jsonify({"error": "Basic, Standard, or Premium subscription required for managing rows"}), 403
#     data = request.json
#     db_name = data.get("db_name")
#     table = data.get("table")
#     condition = data.get("condition")
#     if not all([db_name, table, condition]):
#         return jsonify({"error": "db_name, table and condition are required"}), 400
#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
#             db_info = cursor.fetchone()
#             if not db_info:
#                 return jsonify({"error": "Database not found or not owned by user"}), 403
#         db_type, db_path = db_info
#         if db_type == "sqlite":
#             conn = connect_db(db_name)
#         else:
#             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
#         cur = conn.cursor()
#         cur.execute(f'PRAGMA table_info("{table}")')
#         cols_info = cur.fetchall()
#         valid_cols = {row[1] for row in cols_info}
#         pk_cols = [row[1] for row in cols_info if row[5] == 1]
#         left_side = condition.split('=')[0].strip().strip('"')
#         if left_side not in valid_cols and len(pk_cols) == 1:
#             pk = pk_cols[0]
#             condition = condition.replace(left_side, pk, 1)
#         left_side_final = condition.split('=')[0].strip().strip('"')
#         if left_side_final not in valid_cols:
#             conn.close()
#             return jsonify({"error": f"Invalid column name: {left_side_final}"}), 400
#         sql = f'DELETE FROM "{table}" WHERE {condition}'
#         cur.execute(sql)
#         conn.commit()
#         conn.close()
#         return jsonify({"status": "Row deleted", "rows_affected": cur.rowcount})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/connect_db", methods=["POST"])
# @login_required
# def connect_db_route():
#     data = request.json
#     db_type = data.get("db_type")
#     db_name = data.get("db_name", data.get("database", "remote_db"))
#     conn_info = data.copy()
#     conn_info.pop("db_type", None)
#     try:
#         conn = get_connection(db_type, **conn_info)
#         schema = get_schema(conn, db_type)
#         conn.close()
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("INSERT INTO user_dbs (user_id, db_name, db_type, db_path) VALUES (?, ?, ?, ?)",
#                           (current_user.id, db_name, db_type, conn_info.get("path", "")))
#             conn.commit()
#         return jsonify({"schema": schema})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# # ---------- Stripe Integration ----------
# PLANS = {
#     "basic": ("Basic", 1000),
#     "standard": ("Standard", 1500),
#     "premium": ("Premium", 2500)
# }

# @app.route("/stripe_config", methods=["GET"])
# def stripe_config():
#     return jsonify({
#         "publishableKey": STRIPE_PUBLISHABLE_KEY or "",
#         "plans": {k: {"nickname": v[0], "amount_cents": v[1]} for k, v in PLANS.items()}
#     })

# @app.route("/create-checkout-session", methods=["POST"])
# @login_required
# def create_checkout_session():
#     if not STRIPE_SECRET_KEY:
#         return jsonify({"error": "Stripe secret key not configured on server."}), 500
#     data = request.json or {}
#     plan = data.get("plan")
#     email = data.get("email") or current_user.email
#     if plan not in PLANS:
#         return jsonify({"error": "Invalid plan"}), 400
#     nickname, amount_cents = PLANS[plan]
#     domain_url = request.host_url.rstrip("/")
#     try:
#         session = stripe.checkout.Session.create(
#             payment_method_types=["card"],
#             mode="subscription",
#             line_items=[{
#                 "price_data": {
#                     "currency": "usd",
#                     "product_data": {"name": f"SQL Playground - {nickname} Plan"},
#                     "recurring": {"interval": "month"},
#                     "unit_amount": amount_cents
#                 },
#                 "quantity": 1
#             }],
#             success_url=domain_url + "/app?checkout=success&session_id={CHECKOUT_SESSION_ID}",
#             cancel_url=domain_url + "/app?checkout=cancelled",
#             customer_email=email,
#             allow_promotion_codes=True,
#             metadata={"user_id": str(current_user.id)}
#         )
#         return jsonify({"url": session.url, "id": session.id})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# @app.route("/stripe_webhook", methods=["POST"])
# def stripe_webhook():
#     payload = request.data
#     sig_header = request.headers.get("Stripe-Signature", None)
#     event = None
#     if STRIPE_WEBHOOK_SECRET and sig_header:
#         try:
#             event = stripe.Webhook.construct_event(
#                 payload=payload, sig_header=sig_header, secret=STRIPE_WEBHOOK_SECRET
#             )
#         except ValueError as e:
#             return jsonify({"error": "Invalid payload"}), 400
#         except stripe.error.SignatureVerificationError as e:
#             return jsonify({"error": "Invalid signature"}), 400
#     else:
#         try:
#             event = json.loads(payload)
#         except Exception as e:
#             return jsonify({"error": "Invalid payload and no webhook secret configured."}), 400
#     evt_type = event.get("type")
#     data_obj = event.get("data", {}).get("object", {})
#     if evt_type in ("checkout.session.completed", "customer.subscription.created", "customer.subscription.updated"):
#         user_id = data_obj.get("metadata", {}).get("user_id")
#         if user_id:
#             plan = None
#             for p, (nickname, _) in PLANS.items():
#                 if f"SQL Playground - {nickname} Plan" in str(data_obj):
#                     plan = p
#                     break
#             if plan:
#                 with sqlite3.connect(USER_DB) as conn:
#                     conn.execute("UPDATE users SET subscription_tier = ? WHERE id = ?", (plan, user_id))
#                     conn.commit()
#     try:
#         db_path = get_db_path("stripe_events.db")
#         conn = sqlite3.connect(db_path, timeout=10)
#         conn.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, type TEXT, payload TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
#         evt_id = event.get("id", "")
#         conn.execute("INSERT OR REPLACE INTO events (id, type, payload) VALUES (?, ?, ?)",
#                      (evt_id, evt_type, json.dumps(event)))
#         conn.commit()
#         conn.close()
#     except Exception as e:
#         print("Failed to log stripe event:", e)
#     return jsonify({"status": "success"})

# @app.route("/suggested_queries", methods=["POST"])
# @login_required
# def suggested_queries():
#     if current_user.subscription_tier not in ["standard", "premium"]:
#         return jsonify({"error": "Standard or Premium subscription required for suggested queries"}), 403
    
#     data = request.json
#     db_name = data.get("db_name")
#     try:
#         with sqlite3.connect(USER_DB) as conn:
#             cursor = conn.cursor()
#             cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
#             db_info = cursor.fetchone()
#             if not db_info:
#                 return jsonify({"error": "You do not made the database from our platform therefore due to confidentiality you cant add remove rows but you can enjoy all other features."}), 403
#         db_type, db_path = db_info
        
#         if db_type == "sqlite":
#             conn = connect_db(db_name)
#         else:
#             conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
        
#         schema_info = get_schema(conn, db_type)
#         conn.close()
        
#         system_message = {
#             "role": "system",
#             "content": (
#                 "You are a SQL assistant. Generate exactly 6 useful, practical NATURAL LANGUAGE QUESTIONS (not SQL queries) "
#                 "that a business user would ask about this database.\n"
#                 "Format: Number each question 1-6, followed by the question only. No SQL, no explanations.\n"
#                 "Example:\n"
#                 "1. Total number of employees department wise\n"
#                 "2. Average salary by department\n"
#                 "3. Top 5 highest paid employees\n"
#                 "4. Employees hired in the last year\n"
#                 "5. Department wise gender distribution\n"
#                 "6. Total projects per department\n"
#             )
#         }
#         user_message = {
#             "role": "user",
#             "content": f"Schema:\n{json.dumps(schema_info, indent=2)}\n\nGenerate 6 natural language questions:"
#         }
        
#         resp = groq_client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[system_message, user_message]
#         )
        
#         suggestions_text = resp.choices[0].message.content.strip()
#         # Parse the numbered questions
#         queries = []
#         lines = suggestions_text.split('\n')
#         for line in lines:
#             if line.strip().startswith(tuple('123456')) and '.' in line:
#                 question = line.split('.', 1)[1].strip()
#                 queries.append(question.strip())
        
#         return jsonify({"queries": queries[:6]})
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400

# # ---------- Start server ----------
# if __name__ == "__main__":
#     # Open browser after a short delay
#     threading.Timer(
#         1.5,
#         lambda: webbrowser.open("http://127.0.0.1:5000/")
#     ).start()

#     app.run(host="0.0.0.0", port=5000, debug=True)


import os
import sqlite3
import threading
import webbrowser
import json
import re
from flask import Flask, request, render_template, jsonify, url_for, session, redirect
from groq import Groq
import pymysql
import psycopg2
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import bcrypt
import stripe
from authlib.integrations.flask_client import OAuth

# ---------- Config & Keys ----------
GROQ_API_KEY = os.environ.get(
    "GROQ_API_KEY",
    "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"
)
if GROQ_API_KEY == "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":
    print("Warning: Set your GROQ_API_KEY environment variable!")
groq_client = Groq(api_key=GROQ_API_KEY)

STRIPE_SECRET_KEY = "sk_test_51SCZrEBHO8g2Q8ZQjcKLrhyyvXwjPHfjANMf2ppwxrkZTMrroWLWxI6s6KfWV3tGQZzz9VqG0nA8pySzJK1njZSr002baWcZmf"
STRIPE_PUBLISHABLE_KEY = "pk_test_51SCZrEBHO8g2Q8ZQ0P7oN581Q1Fq3l0VzzpLv8yroTjAV1DIFnhV64bMLjyfDh0Kp6Snf2oKHNi2xUC3TEu4zJxl00yE3q5phJ"
STRIPE_WEBHOOK_SECRET = "whsec_d089c53f00ae2edbea1e23f8fc82d24c2d5b821940b28be5e43fdb6aa52f42f7"
if not STRIPE_SECRET_KEY:
    print("Warning: STRIPE_SECRET_KEY not set. Stripe endpoints will raise errors until set.")
else:
    stripe.api_key = STRIPE_SECRET_KEY

# OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "your-google-client-id")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "your-google-client-secret")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "your-github-client-id")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "your-github-client-secret")

DB_FOLDER = "databases"
os.makedirs(DB_FOLDER, exist_ok=True)
app = Flask(__name__, static_folder=".", template_folder=".")
app.secret_key = os.urandom(24)  # Required for sessions

# OAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    client_kwargs={'scope': 'email profile'},
)
github = oauth.register(
    name='github',
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    api_base_url='https://api.github.com/',
    client_kwargs={'scope': 'user:email'},
)

# ---------- User Database Setup ----------
USER_DB = "users.db"

def init_user_db():
    with sqlite3.connect(USER_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                subscription_tier TEXT DEFAULT 'free'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_dbs (
                user_id INTEGER,
                db_name TEXT,
                db_type TEXT,
                db_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()

init_user_db()

# ---------- Create demo.db ----------
def create_demo_db():
    db_path = os.path.join(DB_FOLDER, "demo.db")
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA case_sensitive_like = OFF;")
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS departments (
                department_id INTEGER PRIMARY KEY,
                department_name TEXT NOT NULL,
                location TEXT
            );

            CREATE TABLE IF NOT EXISTS instructors (
                instructor_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                department_id INTEGER,
                email TEXT,
                FOREIGN KEY (department_id) REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                major_id INTEGER,
                year INTEGER,
                email TEXT,
                FOREIGN KEY (major_id) REFERENCES departments(department_id)
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY,
                course_name TEXT NOT NULL,
                department_id INTEGER,
                credits INTEGER,
                instructor_id INTEGER,
                FOREIGN KEY (department_id) REFERENCES departments(department_id),
                FOREIGN KEY (instructor_id) REFERENCES instructors(instructor_id)
            );

            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY,
                student_id INTEGER,
                course_id INTEGER,
                semester TEXT,
                grade TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            );

            -- Insert data into departments (5 rows)
            INSERT OR IGNORE INTO departments (department_id, department_name, location) VALUES
            (1, 'Computer Science', 'Building A'),
            (2, 'Mathematics', 'Building B'),
            (3, 'Physics', 'Building C'),
            (4, 'History', 'Building D'),
            (5, 'Biology', 'Building E');

            -- Insert data into instructors (10 rows)
            INSERT OR IGNORE INTO instructors (instructor_id, name, department_id, email) VALUES
            (1, 'Dr. Alice Smith', 1, 'alice.smith@university.edu'),
            (2, 'Dr. Bob Johnson', 1, 'bob.johnson@university.edu'),
            (3, 'Dr. Carol White', 2, 'carol.white@university.edu'),
            (4, 'Dr. David Brown', 2, 'david.brown@university.edu'),
            (5, 'Dr. Emma Davis', 3, 'emma.davis@university.edu'),
            (6, 'Dr. Frank Wilson', 3, 'frank.wilson@university.edu'),
            (7, 'Dr. Grace Lee', 4, 'grace.lee@university.edu'),
            (8, 'Dr. Henry Martin', 4, 'henry.martin@university.edu'),
            (9, 'Dr. Isabella Clark', 5, 'isabella.clark@university.edu'),
            (10, 'Dr. James Taylor', 5, 'james.taylor@university.edu');

            -- Insert data into students (20 rows)
            INSERT OR IGNORE INTO students (student_id, name, major_id, year, email) VALUES
            (1, 'John Doe', 1, 1, 'john.doe@university.edu'),
            (2, 'Jane Roe', 1, 2, 'jane.roe@university.edu'),
            (3, 'Michael Chen', 1, 3, 'michael.chen@university.edu'),
            (4, 'Sarah Kim', 1, 4, 'sarah.kim@university.edu'),
            (5, 'Emily Zhang', 2, 1, 'emily.zhang@university.edu'),
            (6, 'David Patel', 2, 2, 'david.patel@university.edu'),
            (7, 'Laura Nguyen', 2, 3, 'laura.nguyen@university.edu'),
            (8, 'James Lee', 2, 4, 'james.lee@university.edu'),
            (9, 'Anna Brown', 3, 1, 'anna.brown@university.edu'),
            (10, 'Robert Wilson', 3, 2, 'robert.wilson@university.edu'),
            (11, 'Lisa Davis', 3, 3, 'lisa.davis@university.edu'),
            (12, 'Mark Taylor', 3, 4, 'mark.taylor@university.edu'),
            (13, 'Sophie Adams', 4, 1, 'sophie.adams@university.edu'),
            (14, 'Thomas Clark', 4, 2, 'thomas.clark@university.edu'),
            (15, 'Olivia Lewis', 4, 3, 'olivia.lewis@university.edu'),
            (16, 'William Walker', 4, 4, 'william.walker@university.edu'),
            (17, 'Mia Harris', 5, 1, 'mia.harris@university.edu'),
            (18, 'Ethan Martinez', 5, 2, 'ethan.martinez@university.edu'),
            (19, 'Ava Thompson', 5, 3, 'ava.thompson@university.edu'),
            (20, 'Noah White', 5, 4, 'noah.white@university.edu');

            -- Insert data into courses (15 rows)
            INSERT OR IGNORE INTO courses (course_id, course_name, department_id, credits, instructor_id) VALUES
            (1, 'Introduction to Programming', 1, 3, 1),
            (2, 'Data Structures', 1, 4, 2),
            (3, 'Algorithms', 1, 4, 1),
            (4, 'Calculus I', 2, 4, 3),
            (5, 'Linear Algebra', 2, 3, 4),
            (6, 'Differential Equations', 2, 4, 3),
            (7, 'Mechanics', 3, 4, 5),
            (8, 'Quantum Physics', 3, 3, 6),
            (9, 'Electromagnetism', 3, 4, 5),
            (10, 'World History', 4, 3, 7),
            (11, 'Modern History', 4, 3, 8),
            (12, 'Ancient Civilizations', 4, 3, 7),
            (13, 'Genetics', 5, 4, 9),
            (14, 'Ecology', 5, 3, 10),
            (15, 'Cell Biology', 5, 4, 9);

            -- Insert data into enrollments (30 rows)
            INSERT OR IGNORE INTO enrollments (enrollment_id, student_id, course_id, semester, grade) VALUES
            (1, 1, 1, 'Fall 2024', 'A'),
            (2, 1, 2, 'Spring 2025', 'B+'),
            (3, 2, 1, 'Fall 2024', 'A-'),
            (4, 2, 3, 'Spring 2025', 'B'),
            (5, 3, 2, 'Fall 2024', 'A'),
            (6, 3, 3, 'Spring 2025', 'A-'),
            (7, 4, 1, 'Fall 2024', 'B+'),
            (8, 4, 2, 'Spring 2025', 'A'),
            (9, 5, 4, 'Fall 2024', 'A'),
            (10, 5, 5, 'Spring 2025', 'B'),
            (11, 6, 4, 'Fall 2024', 'A-'),
            (12, 6, 6, 'Spring 2025', 'B+'),
            (13, 7, 5, 'Fall 2024', 'A'),
            (14, 7, 6, 'Spring 2025', 'A-'),
            (15, 8, 4, 'Fall 2024', 'B'),
            (16, 8, 5, 'Spring 2025', 'A'),
            (17, 9, 7, 'Fall 2024', 'A'),
            (18, 9, 8, 'Spring 2025', 'B+'),
            (19, 10, 7, 'Fall 2024', 'A-'),
            (20, 10, 9, 'Spring 2025', 'B'),
            (21, 11, 8, 'Fall 2024', 'A'),
            (22, 11, 9, 'Spring 2025', 'A-'),
            (23, 12, 7, 'Fall 2024', 'B+'),
            (24, 12, 8, 'Spring 2025', 'A'),
            (25, 13, 10, 'Fall 2024', 'A'),
            (26, 13, 11, 'Spring 2025', 'B+'),
            (27, 14, 10, 'Fall 2024', 'A-'),
            (28, 14, 12, 'Spring 2025', 'B'),
            (29, 15, 11, 'Fall 2024', 'A'),
            (30, 15, 12, 'Spring 2025', 'A-');
        """)
        conn.commit()

# ---------- Flask-Login Setup ----------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

class User(UserMixin):
    def __init__(self, id, email, subscription_tier):
        self.id = id
        self.email = email
        self.subscription_tier = subscription_tier

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect(USER_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, subscription_tier FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if user:
            return User(user[0], user[1], user[2])
        return None

# ---------- Routes ----------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect("/app")
    return redirect("/auth")

@app.route("/auth")
def auth_page():
    return render_template("auth.html")

@app.route("/app")
@login_required
def app_page():
    return render_template("index.html")

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    try:
        with sqlite3.connect(USER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                return jsonify({"error": "Email already registered"}), 400
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            subscription_tier = "premium"
            cursor.execute(
                "INSERT INTO users (email, password, subscription_tier) VALUES (?, ?, ?)",
                (email, hashed_pw, subscription_tier)
            )
            conn.commit()
            user_id = cursor.lastrowid
            user = User(user_id, email, subscription_tier)
            login_user(user)
            return jsonify({
                "status": "success",
                "message": "You are signed up successfully!",
                "tier": subscription_tier,
                "redirect": "/app"
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    try:
        with sqlite3.connect(USER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, password, subscription_tier FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
                login_user(User(user[0], user[1], user[3]))
                return jsonify({
                    "status": "Logged in",
                    "tier": user[3],
                    "redirect": "/app"
                })
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"status": "Logged out"})

@app.route("/user_info", methods=["GET"])
def user_info():
    if current_user.is_authenticated:
        return jsonify({"email": current_user.email, "tier": current_user.subscription_tier})
    return jsonify({"error": "Not logged in"}), 401

@app.route("/public_databases", methods=["GET"])
def public_databases():
    """List ALL databases including public ones like demo.db"""
    public_dbs = ["demo.db"]
    try:
        if current_user.is_authenticated:
            with sqlite3.connect(USER_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT db_name FROM user_dbs WHERE user_id = ?", (current_user.id,))
                personal_dbs = [row[0] for row in cursor.fetchall()]
        else:
            personal_dbs = []
    except:
        personal_dbs = []
    all_dbs = list(set(public_dbs + personal_dbs))
    return jsonify({"databases": all_dbs})

@app.route("/databases", methods=["GET"])
@login_required
def list_databases():
    try:
        with sqlite3.connect(USER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT db_name FROM user_dbs WHERE user_id = ?", (current_user.id,))
            dbs = [row[0] for row in cursor.fetchall()]
        return jsonify({"databases": dbs})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------- DB & Groq Utilities ----------
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
            "Your output must ONLY be pure SQL that can be executed directly"
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

@app.route("/schema", methods=["POST"])
def schema():
    data = request.json
    db_name = data.get("db_name")
    try:
        is_public = db_name == "demo.db"
        if not is_public:
            if not current_user.is_authenticated:
                return jsonify({"error": "Login required for this database"}), 401
            with sqlite3.connect(USER_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
                db_info = cursor.fetchone()
                if not db_info:
                    return jsonify({"error": "Database not found or not owned by user"}), 403
                db_type, db_path = db_info
        else:
            db_type = "sqlite"
            db_path = get_db_path(db_name)
        if db_type == "sqlite":
            with connect_db(db_name) as conn:
                schema_info = get_schema_info(conn)
        else:
            conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
            schema_info = get_schema(conn, db_type)
            conn.close()
        return jsonify({"schema": schema_info})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/db_description", methods=["POST"])
def db_description():
    data = request.json
    db_name = data.get("db_name")
    try:
        is_public = db_name == "demo.db"
        if not is_public:
            if not current_user.is_authenticated:
                return jsonify({"error": "Login required for this database"}), 401
            with sqlite3.connect(USER_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
                db_info = cursor.fetchone()
                if not db_info:
                    return jsonify({"error": "Database not found or not owned by user"}), 403
                db_type, db_path = db_info
        else:
            db_type = "sqlite"
            db_path = get_db_path(db_name)
        if db_type == "sqlite":
            conn = connect_db(db_name)
        else:
            conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
        schema_info = get_schema(conn, db_type)
        conn.close()
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
        is_public = db_name == "demo.db"
        tier = "free" if not current_user.is_authenticated else current_user.subscription_tier
        if not is_public and tier not in ["standard", "premium"]:
            return jsonify({"error": "Standard or Premium subscription required for querying private databases"}), 403
        if not is_public:
            if not current_user.is_authenticated:
                return jsonify({"error": "Login required for this database"}), 401
            with sqlite3.connect(USER_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
                db_info = cursor.fetchone()
                if not db_info:
                    return jsonify({"error": "Database not found or not owned by user"}), 403
                db_type, db_path = db_info
        else:
            db_type = "sqlite"
            db_path = get_db_path(db_name)
        if db_type == "sqlite":
            conn = connect_db(db_name)
        else:
            conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
        schema_info = get_schema(conn, db_type)
        sql_query = generate_sql_with_groq(question, schema_info)
        sql_query = fix_sql_string_literals(sql_query)
        result = run_sql(conn, sql_query)
        conn.close()
        return jsonify({"sql": sql_query, "result": result})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/visualize", methods=["POST"])
def visualize():
    data = request.json
    db_name = data.get("db_name")
    prompt = data.get("prompt")
    try:
        is_public = db_name == "demo.db"
        if not current_user.is_authenticated:
            return jsonify({"error": "Login required for visualization"}), 401
        if current_user.subscription_tier != "premium":
            return jsonify({"error": "Premium subscription required for visualization"}), 403
        if not is_public:
            with sqlite3.connect(USER_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
                db_info = cursor.fetchone()
                if not db_info:
                    return jsonify({"error": "Database not found or not owned by user"}), 403
                db_type, db_path = db_info
        else:
            db_type = "sqlite"
            db_path = get_db_path(db_name)
        if db_type == "sqlite":
            conn = connect_db(db_name)
        else:
            conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
        schema_info = get_schema(conn, db_type)
        sql_query = generate_sql_with_groq(prompt, schema_info)
        result = run_sql(conn, sql_query)
        conn.close()
        if result.get("error"):
            return jsonify({"error": result["error"]}), 400
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

@app.route("/create_db", methods=["POST"])
@login_required
def create_db():
    if current_user.subscription_tier not in ["free", "basic", "standard", "premium"]:
        return jsonify({"error": "Free, Basic, Standard, or Premium subscription required for creating databases"}), 403
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
        with sqlite3.connect(USER_DB) as conn:
            conn.execute("INSERT INTO user_dbs (user_id, db_name, db_type, db_path) VALUES (?, ?, ?, ?)",
                         (current_user.id, db_name, "sqlite", db_path))
            conn.commit()
        return jsonify({"status": "Database created", "sql_schema": sql_schema})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/add_row", methods=["POST"])
@login_required
def add_row():
    if current_user.subscription_tier not in ["basic", "standard", "premium"]:
        return jsonify({"error": "Basic, Standard, or Premium subscription required for managing rows"}), 403
    data = request.json
    db_name = data.get("db_name")
    table_name = data.get("table")
    values_text = data.get("values")
    try:
        if db_name == "demo.db":
            return jsonify({"error": "Cannot modify demo.db rows"}), 403
        with sqlite3.connect(USER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
            db_info = cursor.fetchone()
            if not db_info:
                return jsonify({"error": "Database not found or not owned by user"}), 403
            db_type, db_path = db_info
        if db_type == "sqlite":
            conn = connect_db(db_name)
        else:
            conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
        cursor = conn.cursor()
        schema = get_schema_info(conn) if db_type == "sqlite" else get_schema(conn, db_type)
        table_key = table_name.lower()
        if table_key not in schema:
            conn.close()
            return jsonify({"error": f"Table {table_name} not found!"}), 400
        columns = [c["name"] for c in schema[table_key]]
        raw_values = values_text.strip()
        values = [v.strip() for v in raw_values.split(",")]
        if len(values) != len(columns):
            conn.close()
            return jsonify({"error": f"Expected {len(columns)} values, got {len(values)}"}), 400
        placeholders = ",".join("?" * len(values))
        sql = f'INSERT INTO "{table_key}" ({",".join(columns)}) VALUES ({placeholders})'
        cursor.execute(sql, values)
        conn.commit()
        conn.close()
        return jsonify({"status": "Row added"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/delete_row", methods=["POST"])
@login_required
def delete_row():
    if current_user.subscription_tier not in ["basic", "standard", "premium"]:
        return jsonify({"error": "Basic, Standard, or Premium subscription required for managing rows"}), 403
    data = request.json
    db_name = data.get("db_name")
    table = data.get("table")
    condition = data.get("condition")
    if not all([db_name, table, condition]):
        return jsonify({"error": "db_name, table and condition are required"}), 400
    try:
        if db_name == "demo.db":
            return jsonify({"error": "Cannot modify demo.db rows"}), 403
        with sqlite3.connect(USER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
            db_info = cursor.fetchone()
            if not db_info:
                return jsonify({"error": "Database not found or not owned by user"}), 403
            db_type, db_path = db_info
        if db_type == "sqlite":
            conn = connect_db(db_name)
        else:
            conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
        cur = conn.cursor()
        cur.execute(f'PRAGMA table_info("{table}")')
        cols_info = cur.fetchall()
        valid_cols = {row[1] for row in cols_info}
        pk_cols = [row[1] for row in cols_info if row[5] == 1]
        left_side = condition.split('=')[0].strip().strip('"')
        if left_side not in valid_cols and len(pk_cols) == 1:
            pk = pk_cols[0]
            condition = condition.replace(left_side, pk, 1)
        left_side_final = condition.split('=')[0].strip().strip('"')
        if left_side_final not in valid_cols:
            conn.close()
            return jsonify({"error": f"Invalid column name: {left_side_final}"}), 400
        sql = f'DELETE FROM "{table}" WHERE {condition}'
        cur.execute(sql)
        conn.commit()
        conn.close()
        return jsonify({"status": "Row deleted", "rows_affected": cur.rowcount})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/connect_db", methods=["POST"])
@login_required
def connect_db_route():
    data = request.json
    db_type = data.get("db_type")
    db_name = data.get("db_name", data.get("database", "remote_db"))
    conn_info = data.copy()
    conn_info.pop("db_type", None)
    try:
        conn = get_connection(db_type, **conn_info)
        schema = get_schema(conn, db_type)
        conn.close()
        with sqlite3.connect(USER_DB) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO user_dbs (user_id, db_name, db_type, db_path) VALUES (?, ?, ?, ?)",
                          (current_user.id, db_name, db_type, conn_info.get("path", "")))
            conn.commit()
        return jsonify({"schema": schema})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/suggested_queries", methods=["POST"])
def suggested_queries():
    data = request.json
    db_name = data.get("db_name")
    try:
        is_public = db_name == "demo.db"
        tier = "free" if not current_user.is_authenticated else current_user.subscription_tier
        if not is_public and tier not in ["standard", "premium"]:
            return jsonify({"error": "Standard or Premium subscription required for suggested queries on private databases"}), 403
        if not is_public:
            if not current_user.is_authenticated:
                return jsonify({"error": "Login required for this database"}), 401
            with sqlite3.connect(USER_DB) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT db_type, db_path FROM user_dbs WHERE user_id = ? AND db_name = ?", (current_user.id, db_name))
                db_info = cursor.fetchone()
                if not db_info:
                    return jsonify({"error": "Database not found or not owned by user"}), 403
                db_type, db_path = db_info
        else:
            db_type = "sqlite"
            db_path = get_db_path(db_name)
        if db_type == "sqlite":
            conn = connect_db(db_name)
        else:
            conn = get_connection(db_type, path=db_path, host=data.get("host"), port=data.get("port"), database=data.get("database"), user=data.get("user"), password=data.get("password"))
        schema_info = get_schema(conn, db_type)
        conn.close()
        system_message = {
            "role": "system",
            "content": (
                "You are a SQL assistant. Generate exactly 6 useful, practical NATURAL LANGUAGE QUESTIONS (not SQL queries) "
                "that a business user would ask about this database.\n"
                "Format: Number each question 1-6, followed by the question only. No SQL, no explanations.\n"
                "Example:\n"
                "1. Total number of employees department wise\n"
                "2. Average salary by department\n"
                "3. Top 5 highest paid employees\n"
                "4. Employees hired in the last year\n"
                "5. Department wise gender distribution\n"
                "6. Total projects per department\n"
            )
        }
        user_message = {
            "role": "user",
            "content": f"Schema:\n{json.dumps(schema_info, indent=2)}\n\nGenerate 6 natural language questions:"
        }
        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[system_message, user_message]
        )
        suggestions_text = resp.choices[0].message.content.strip()
        queries = []
        lines = suggestions_text.split('\n')
        for line in lines:
            if line.strip().startswith(tuple('123456')) and '.' in line:
                question = line.split('.', 1)[1].strip()
                queries.append(question.strip())
        return jsonify({"queries": queries[:6]})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ---------- Stripe Integration ----------
PLANS = {
    "basic": ("Basic", 1000),
    "standard": ("Standard", 1500),
    "premium": ("Premium", 2500)
}

@app.route("/stripe_config", methods=["GET"])
def stripe_config():
    return jsonify({
        "publishableKey": STRIPE_PUBLISHABLE_KEY or "",
        "plans": {k: {"nickname": v[0], "amount_cents": v[1]} for k, v in PLANS.items()}
    })

@app.route("/create-checkout-session", methods=["POST"])
@login_required
def create_checkout_session():
    if not STRIPE_SECRET_KEY:
        return jsonify({"error": "Stripe secret key not configured on server."}), 500
    data = request.json or {}
    plan = data.get("plan")
    email = data.get("email") or current_user.email
    if plan not in PLANS:
        return jsonify({"error": "Invalid plan"}), 400
    nickname, amount_cents = PLANS[plan]
    domain_url = request.host_url.rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"SQL Playground - {nickname} Plan"},
                    "recurring": {"interval": "month"},
                    "unit_amount": amount_cents
                },
                "quantity": 1
            }],
            success_url=domain_url + "/app?checkout=success&session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "/app?checkout=cancelled",
            customer_email=email,
            allow_promotion_codes=True,
            metadata={"user_id": str(current_user.id)}
        )
        return jsonify({"url": session.url, "id": session.id})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/stripe_webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", None)
    event = None
    if STRIPE_WEBHOOK_SECRET and sig_header:
        try:
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            return jsonify({"error": "Invalid payload"}), 400
        except stripe.error.SignatureVerificationError as e:
            return jsonify({"error": "Invalid signature"}), 400
    else:
        try:
            event = json.loads(payload)
        except Exception as e:
            return jsonify({"error": "Invalid payload and no webhook secret configured."}), 400
    evt_type = event.get("type")
    data_obj = event.get("data", {}).get("object", {})
    if evt_type in ("checkout.session.completed", "customer.subscription.created", "customer.subscription.updated"):
        user_id = data_obj.get("metadata", {}).get("user_id")
        if user_id:
            plan = None
            for p, (nickname, _) in PLANS.items():
                if f"SQL Playground - {nickname} Plan" in str(data_obj):
                    plan = p
                    break
            if plan:
                with sqlite3.connect(USER_DB) as conn:
                    conn.execute("UPDATE users SET subscription_tier = ? WHERE id = ?", (plan, user_id))
                    conn.commit()
    try:
        db_path = get_db_path("stripe_events.db")
        conn = sqlite3.connect(db_path, timeout=10)
        conn.execute("CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, type TEXT, payload TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
        evt_id = event.get("id", "")
        conn.execute("INSERT OR REPLACE INTO events (id, type, payload) VALUES (?, ?, ?)",
                     (evt_id, evt_type, json.dumps(event)))
        conn.commit()
        conn.close()
    except Exception as e:
        print("Failed to log stripe event:", e)
    return jsonify({"status": "success"})

# ---------- Start server ----------
if __name__ == "__main__":
    create_demo_db()
    threading.Timer(
        1.5,
        lambda: webbrowser.open("http://127.0.0.1:5000/")
    ).start()
    app.run(host="0.0.0.0", port=5000, debug=True)
