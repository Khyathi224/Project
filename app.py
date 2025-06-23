from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import sqlite3
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret-key"
UPLOAD_FOLDER = "static/uploaded_images"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DB = 'database.db'

# --------------------- DATABASE SETUP ---------------------

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        phone TEXT,
        password TEXT,
        role TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        department TEXT,
        description TEXT,
        image TEXT,
        status TEXT DEFAULT 'Unsolved'
    )''')
    conn.commit()
    conn.close()

init_db()

# --------------------- ROUTES ---------------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        role = request.form["role"]
        phone = request.form["phone"]
        password = request.form["password"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE phone=? AND password=? AND role=?", (phone, password, role))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = role
            if role == "user":
                return redirect("/user")
            elif role == "admin":
                return redirect("/admin")
            else:
                return redirect("/worker")
        else:
            flash("Invalid login details.")
            return redirect("/")
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    phone = request.form["phone"]
    password = request.form["password"]
    role = request.form["role"]

    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO users (name, phone, password, role) VALUES (?, ?, ?, ?)", (name, phone, password, role))
    conn.commit()
    conn.close()
    flash("Registration successful. Please log in.")
    return redirect("/")

@app.route("/user", methods=["GET", "POST"])
def user():
    if "user_id" not in session:
        return redirect("/")
    
    if request.method == "POST":
        department = request.form["department"]
        description = request.form["description"]
        image = request.files["image"]

        filename = secure_filename(image.filename)
        image_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        image.save(image_path)

        conn = sqlite3.connect(DB)
        c = conn.cursor()
        c.execute("INSERT INTO queries (user_id, department, description, image) VALUES (?, ?, ?, ?)",
                  (session["user_id"], department, description, filename))
        conn.commit()
        conn.close()
        flash("Issue submitted successfully.")
        return redirect("/user")

    return render_template("user.html")

@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM queries")
    queries = c.fetchall()

    c.execute("SELECT COUNT(*) FROM users WHERE role='user'")
    user_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE role='worker'")
    worker_count = c.fetchone()[0]
    conn.close()
    return render_template("admin.html", queries=queries, user_count=user_count, worker_count=worker_count)

@app.route("/worker")
def worker():
    if session.get("role") != "worker":
        return redirect("/")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT * FROM queries WHERE status='Unsolved'")
    queries = c.fetchall()
    conn.close()
    return render_template("worker.html", queries=queries)

@app.route("/mark_solved/<int:query_id>")
def mark_solved(query_id):
    if session.get("role") != "admin":
        return redirect("/")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("UPDATE queries SET status='Solved' WHERE id=?", (query_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
