import os
import sqlite3
from flask import Flask, jsonify, request, send_from_directory, url_for
import uuid

app = Flask(__name__)
app.json.ensure_ascii = False

DB_NAME = "tasks.db"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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


def make_image_url(filename):
    if not filename:
        return None
    return url_for("get_image", filename=filename, _external=True)


def task_to_dict(row):
    task = dict(row)
    task["done"] = bool(task["done"])
    task["image_url"] = make_image_url(task["image_filename"])
    return task


@app.route("/")
def home():
    return "سرور روشنه!"


@app.route("/uploads/<filename>")
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


@app.route("/tasks")
def get_tasks():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    finally:
        conn.close()
    return jsonify([task_to_dict(row) for row in rows])


@app.route("/tasks/<int:task_id>")
def get_task(task_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    finally:
        conn.close()

    if row is None:
        return jsonify({"error": "همچین کاری پیدا نشد"}), 404

    return jsonify(task_to_dict(row))


@app.route("/tasks", methods=["POST"])
def create_task():
    title = request.form.get("title", "").strip()

    if not title:
        return jsonify({"error": "عنوان کار الزامی است"}), 400

    if len(title) > 100:
        return jsonify({"error": "عنوان نباید بیشتر از ۱۰۰ کاراکتر باشد"}), 400

    image_filename = None

    if "image" in request.files:
        image = request.files["image"]
        if image.filename != "":
            if not allowed_file(image.filename):
                return jsonify({"error": "فقط فایل png و jpg و jpeg و gif مجاز است"}), 400
            extension = image.filename.rsplit(".", 1)[1].lower()
            image_filename = f"{uuid.uuid4().hex}.{extension}"
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
        "image_filename": image_filename,
        "image_url": make_image_url(image_filename)
    }), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "بدنه‌ی درخواست باید JSON معتبر باشد"}), 400

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return jsonify({"error": "عنوان باید یک متن غیرخالی باشد"}), 400
        if len(data["title"].strip()) > 100:
            return jsonify({"error": "عنوان نباید بیشتر از ۱۰۰ کاراکتر باشد"}), 400

    if "done" in data and not isinstance(data["done"], bool):
        return jsonify({"error": "مقدار done باید true یا false باشد"}), 400

    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()

        if row is None:
            return jsonify({"error": "همچین کاری پیدا نشد"}), 404

        new_title = data.get("title", row["title"]).strip()
        new_done = data.get("done", bool(row["done"]))

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, int(new_done), task_id)
        )
        conn.commit()

        updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    finally:
        conn.close()

    return jsonify(task_to_dict(updated))


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


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "آدرس پیدا نشد"}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "این متد برای این آدرس مجاز نیست"}), 405


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "خطای داخلی سرور"}), 500


if __name__ == "__main__":
    init_db()
    app.run(debug=True)