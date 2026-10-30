# app.py - Aplicación Flask con fallos de seguridad A PROPÓSITO (solo para fines educativos).
# No uses este código en producción.
import os
import sqlite3

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


# FALLO 1: XSS reflejado, el parámetro se inserta en la plantilla sin escapar
@app.route("/hello")
def hello():
    name = request.args.get("name", "Mundo")
    return render_template_string(f"<h1>Hola, {name}!</h1>")


# FALLO 2: SQL Injection, la consulta se arma concatenando texto
@app.route("/user")
def get_user():
    user_id = request.args.get("id", "1")
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(f"SELECT * FROM users WHERE id = {user_id}").fetchall()
    conn.close()
    return str(rows)


# FALLO 3: inyección de comandos, el parámetro llega a una shell
@app.route("/ping")
def ping():
    host = request.args.get("host", "127.0.0.1")
    return os.popen(f"echo pong a {host}").read()


if __name__ == "__main__":
    init_db()
    # FALLO 4: debug=True expone la consola de Werkzeug y permite ejecutar código
    app.run(host="0.0.0.0", port=5000, debug=True)
