import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.json.ensure_ascii = False

DB_NAME = "tasks.db"
UPLOAD_FOLDER = "uploads"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0,
            image_filename TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return "سرور روشنه!"


@app.route("/tasks")
def get_tasks():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    finally:
        conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/tasks/<int:task_id>")
def get_task(task_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "همچین کاری پیدا نشد"}), 404

    return jsonify(dict(row))

@app.route("/uploads/<filename>")
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/tasks", methods=["POST"])
def create_task():
    title = request.form.get("title")
    image_filename = None

    if "image" in request.files:
        image = request.files["image"]
        if image.filename != "":
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(UPLOAD_FOLDER, image_filename))

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done, image_filename) VALUES (?, ?, ?)",
            (title, 0, image_filename)
        )
        conn.commit()
        new_id = cursor.lastrowid
    finally:
        conn.close()

    return jsonify({
        "id": new_id,
        "title": title,
        "done": False,
        "image_filename": image_filename
    }), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()

    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

        if row is None:
            return jsonify({"error": "همچین کاری پیدا نشد"}), 404

        new_title = data.get("title", row["title"])
        new_done = data.get("done", bool(row["done"]))

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, int(new_done), task_id)
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({"id": task_id, "title": new_title, "done": new_done})


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

        if row is None:
            return jsonify({"error": "همچین کاری پیدا نشد"}), 404

        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({"message": "کار حذف شد"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True)