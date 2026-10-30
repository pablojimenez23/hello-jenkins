# app.py - Aplicación Flask corregida
import ipaddress
import os
import sqlite3
import subprocess

from flask import Flask, request, render_template_string

app = Flask(__name__)
DB_PATH = os.environ.get("DB_PATH", "users.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.executemany("INSERT INTO users (name) VALUES (?)", [("ana",), ("luis",)])
    conn.commit()
    conn.close()


@app.route("/")
def index():
    return (
        "<h1>Mini app DevSecOps</h1><ul>"
        '<li><a href="/hello?name=Mundo">/hello</a></li>'
        '<li><a href="/user?id=1">/user</a></li>'
        '<li><a href="/ping?host=127.0.0.1">/ping</a></li>'
        "</ul>"
    )


@app.route("/health")
def health():
    return {"status": "ok"}


# CORREGIDO: XSS, el valor se pasa como variable y Jinja lo escapa
@app.route("/hello")
def hello():
    name = request.args.get("name", "Mundo")
    return render_template_string("<h1>Hola, {{ name }}!</h1>", name=name)


# CORREGIDO: SQL Injection, consulta parametrizada
@app.route("/user")
def get_user():
    user_id = request.args.get("id", "1")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchall()
    conn.close()
    return str(rows)


# CORREGIDO: inyección de comandos, sin shell y validando que sea una IP
@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return "host inválido", 400
    out = subprocess.run(["echo", "pong a", host], capture_output=True, text=True, check=False)
    return out.stdout


if __name__ == "__main__":
    init_db()
    # CORREGIDO: sin debug=True
    app.run(host="0.0.0.0", port=5000)