import os
import re
import sqlite3
import json

def clean_sql(sql_text):
    if not sql_text:
        return ""

    s = sql_text.replace('\r\n', '\n').replace('\r', '\n')
    s = s.replace('"', '').replace('[', '').replace(']', '')
    s = re.sub(r'(CREATE\s+(?:TABLE|VIEW)\s+[^\(]+)\(\s*', r'\1(\n', s, flags=re.IGNORECASE)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r',\s*', ',\n', s)
    lines = [ln.strip() for ln in s.split('\n') if ln.strip()]

    out_lines = []
    indent_level = 0
    for line in lines:
        if line.startswith(')'):
            indent_level = max(indent_level - 1, 0)

        prefix = '    ' * indent_level
        out_lines.append(prefix + line)

        if line.endswith('(') or ('(' in line and not ')' in line):
            indent_level += 1

    cleaned = '\n'.join(out_lines)
    cleaned = re.sub(r'\n{2,}', '\n\n', cleaned).strip()
    cleaned = cleaned.replace('\\n', '')
    cleaned = re.sub(r'\n\s*', '', cleaned)
    cleaned = re.sub(r',', ', ', cleaned)

    return cleaned

def list_tables(db_path, show_sql=False):
    tables_json = []
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return {}
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT name, type, sql
            FROM sqlite_master
            WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'
            ORDER BY type, name
        """)
        rows = cur.fetchall()
        if not rows:
            print("No tables or views found.")
            return {}
        for name, typ, sql in rows:
            sql_text = sql or ""
            cleaned = clean_sql(sql_text)
            tables_json.append({
                "table_name": name,
                "table_sql": cleaned
            })
            if show_sql:
                print(f"{typ.upper()}: {name}\n{cleaned}\n")
            else:
                print(f"{typ.upper():4} {name}")
        return tables_json
    finally:
        conn.close()

def run_sql(db_path, sql_query):
    """
    Run arbitrary SQL on the sqlite database at db_path.
    Returns a dict with status and result:
      - For SELECT: {"status":"ok", "columns": [...], "rows": [ {col:val,...}, ... ]}
      - For non-SELECT: {"status":"ok", "rows_affected": n, "lastrowid": id}
      - On error: {"status":"error", "error": "message"}
    """
    if not os.path.exists(db_path):
        return {"status": "error", "error": f"Database not found: {db_path}"}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        sql = (sql_query or "").strip()
        if not sql:
            return {"status": "error", "error": "Empty SQL query"}

        # SELECT -> fetch rows, other statements -> execute and commit
        first_word = sql.split(None, 1)[0].lower()
        if first_word == "select":
            cur.execute(sql)
            rows = [dict(r) for r in cur.fetchall()]
            cols = [c[0] for c in cur.description] if cur.description else []
            return {"status": "ok", "columns": cols, "rows": rows}
        else:
            if ";" in sql and sql.count(";") > 0:
                cur.executescript(sql)
                conn.commit()
                return {"status": "ok", "rows_affected": cur.rowcount}
            else:
                cur.execute(sql)
                conn.commit()
                return {"status": "ok", "rows_affected": cur.rowcount, "lastrowid": cur.lastrowid}
    except sqlite3.Error as e:
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()

if __name__ == "__main__":
    db_path = input("Enter path: ")
    tables = json.dumps(list_tables(db_path=db_path, show_sql=True), indent=4)
    print(tables)
    sql = input("Enter SQL: ")
    result = run_sql(db_path=db_path, sql_query=sql)
    print(json.dumps(result, indent=4))
