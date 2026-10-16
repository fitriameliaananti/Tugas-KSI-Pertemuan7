"""
Portal Kampus FIKTIF - proyek latihan keamanan aplikasi web.
SEMUA akun dan data bersifat sintetis. Aplikasi ini SENGAJA memiliki kerentanan
(lihat VULNERABILITIES.md). Jangan dipakai untuk data nyata / jangan di-deploy
sebagai sistem sungguhan.
"""
import os
import sqlite3
import uuid
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   send_from_directory, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "campus.db")
UPLOAD_DIR = os.path.join(BASE, "uploads")
ALLOWED_EXT = {"pdf", "txt", "docx", "zip"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "kunci-latihan-fiktif")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


# ---------------------------------------------------------------- database
def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    conn = g.pop("db", None)
    if conn:
        conn.close()


SCHEMA = """
CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT,
  role TEXT, full_name TEXT, ident TEXT, active INTEGER DEFAULT 1);
CREATE TABLE courses(id INTEGER PRIMARY KEY, code TEXT, name TEXT, lecturer_id INTEGER);
CREATE TABLE enrollments(student_id INTEGER, course_id INTEGER, PRIMARY KEY(student_id, course_id));
CREATE TABLE grades(id INTEGER PRIMARY KEY, student_id INTEGER, course_id INTEGER, score REAL, note TEXT,
  UNIQUE(student_id, course_id));
CREATE TABLE assignments(id INTEGER PRIMARY KEY, course_id INTEGER, title TEXT, due TEXT);
CREATE TABLE submissions(id INTEGER PRIMARY KEY, assignment_id INTEGER, student_id INTEGER,
  stored_name TEXT, original_name TEXT, created TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE posts(id INTEGER PRIMARY KEY, course_id INTEGER, user_id INTEGER, body TEXT,
  created TEXT DEFAULT CURRENT_TIMESTAMP);
"""


def init_db():
    if os.path.exists(DB_PATH) and os.path.getsize(DB_PATH) > 0:
        return  # database sudah terisi
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    users = [  # (username, password, role, nama, nip/npm)
        ("admin.kampus", "Adm1n#Fiktif", "admin", "Admin Sistem Fiktif", "ADM-0001"),
        ("laras.dosen", "Dosen#Laras1", "dosen", "Dr. Laras Utami (fiktif)", "NIP-7001"),
        ("bayu.dosen", "Dosen#Bayu2", "dosen", "Dr. Bayu Setiawan (fiktif)", "NIP-7002"),
        ("mhs.Fitri", "Mhs#Fitri24", "mahasiswa", "Fitri Amelia (fiktif)", "NPM-26001"),
        ("mhs.nadia", "Mhs#Nadia25", "mahasiswa", "Nadia putri (fiktif)", "NPM-26002"),
        ("mhs.dimas", "Mhs#Dimas26", "mahasiswa", "Dimas Anggara (fiktif)", "NPM-26003"),
        ("mhs.salsa", "Mhs#Salsa27", "mahasiswa", "Salsa Kirana sari (fiktif)", "NPM-26004"),
    ]
    for u, p, r, n, i in users:
        conn.execute("INSERT INTO users(username,password_hash,role,full_name,ident) VALUES(?,?,?,?,?)",
                     (u, generate_password_hash(p), r, n, i))
    conn.executemany("INSERT INTO courses(code,name,lecturer_id) VALUES(?,?,?)", [
        ("IF101", "Pemrograman Web Dasar", 2),
        ("IF102", "Pemrograman Basis Data", 2),
        ("IF201", "Keamanan Sistem Informasi", 3),
    ])
    for s in (4, 5, 6, 7):
        for c in (1, 2, 3):
            if (s + c) % 5 == 0:
                continue
            conn.execute("INSERT INTO enrollments VALUES(?,?)", (s, c))
            conn.execute("INSERT INTO grades(student_id,course_id,score,note) VALUES(?,?,?,?)",
                         (s, c, 60 + (s * 7 + c * 5) % 38, "Nilai sintetis"))
    conn.executemany("INSERT INTO assignments(course_id,title,due) VALUES(?,?,?)", [
        (1, "Tugas 1 - Halaman HTML statis", "2026-11-05"),
        (2, "Tugas 1 - Desain ERD", "2026-11-12"),
        (3, "Tugas 1 - Ringkasan CIA Triad", "2026-11-19"),
    ])
    conn.execute("INSERT INTO posts(course_id,user_id,body) VALUES(1,2,'Selamat datang di forum Pemrograman Web Dasar (data fiktif).')")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------- auth
def current_user():
    uid = session.get("uid")
    if not uid:
        return None
    return db().execute("SELECT * FROM users WHERE id=? AND active=1", (uid,)).fetchone()


def login_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            user = current_user()
            if not user:
                return redirect(url_for("login"))
            if roles and user["role"] not in roles:
                abort(403)
            g.user = user
            return fn(*a, **kw)
        return wrapper
    return deco


@app.context_processor
def inject_user():
    return {"me": current_user()}


@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("uid") else url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = db().execute("SELECT * FROM users WHERE username=? AND active=1",
                         (request.form.get("username", ""),)).fetchone()
        if u and check_password_hash(u["password_hash"], request.form.get("password", "")):
            session.clear()
            session["uid"] = u["id"]
            return redirect(url_for("dashboard"))
        flash("Username atau sandi salah.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required()
def dashboard():
    u = g.user
    if u["role"] == "mahasiswa":
        courses = db().execute("""SELECT c.* FROM courses c JOIN enrollments e ON e.course_id=c.id
                                  WHERE e.student_id=?""", (u["id"],)).fetchall()
    elif u["role"] == "dosen":
        courses = db().execute("SELECT * FROM courses WHERE lecturer_id=?", (u["id"],)).fetchall()
    else:
        courses = db().execute("SELECT * FROM courses").fetchall()
    return render_template("dashboard.html", courses=courses)


# ---------------------------------------------------------------- mahasiswa: nilai
@app.route("/nilai")
@login_required("mahasiswa")
def nilai():
    rows = db().execute("""SELECT g.id, g.score, g.note, c.code, c.name FROM grades g
                           JOIN courses c ON c.id=g.course_id WHERE g.student_id=?""",
                        (g.user["id"],)).fetchall()
    return render_template("nilai.html", rows=rows)


@app.route("/nilai/<int:grade_id>")
@login_required("mahasiswa", "dosen", "admin")
def nilai_detail(grade_id):
    # [KERENTANAN SENGAJA #1 - IDOR] tidak ada pengecekan kepemilikan nilai.
    row = db().execute("""SELECT g.*, c.code, c.name AS course, u.full_name, u.ident
                          FROM grades g JOIN courses c ON c.id=g.course_id
                          JOIN users u ON u.id=g.student_id WHERE g.id=?""", (grade_id,)).fetchone()
    if not row:
        abort(404)
    return render_template("nilai_detail.html", r=row)


# ---------------------------------------------------------------- mahasiswa: tugas
@app.route("/tugas", methods=["GET", "POST"])
@login_required("mahasiswa")
def tugas():
    if request.method == "POST":
        aid = request.form.get("assignment_id", type=int)
        f = request.files.get("berkas")
        ok = db().execute("""SELECT 1 FROM assignments a JOIN enrollments e ON e.course_id=a.course_id
                             WHERE a.id=? AND e.student_id=?""", (aid, g.user["id"])).fetchone()
        if not ok or not f or not f.filename:
            flash("Tugas atau berkas tidak valid.")
        else:
            name = secure_filename(f.filename)
            if name.rsplit(".", 1)[-1].lower() not in ALLOWED_EXT or "." not in name:
                flash("Ekstensi tidak diizinkan (pdf, txt, docx, zip).")
            else:
                stored = uuid.uuid4().hex + "_" + name
                f.save(os.path.join(UPLOAD_DIR, stored))
                db().execute("INSERT INTO submissions(assignment_id,student_id,stored_name,original_name) VALUES(?,?,?,?)",
                             (aid, g.user["id"], stored, name))
                db().commit()
                flash("Tugas berhasil diunggah.")
        return redirect(url_for("tugas"))
    assignments = db().execute("""SELECT a.*, c.name AS course FROM assignments a
                                  JOIN courses c ON c.id=a.course_id
                                  JOIN enrollments e ON e.course_id=c.id WHERE e.student_id=?""",
                               (g.user["id"],)).fetchall()
    subs = db().execute("""SELECT s.*, a.title FROM submissions s JOIN assignments a ON a.id=s.assignment_id
                           WHERE s.student_id=? ORDER BY s.id DESC""", (g.user["id"],)).fetchall()
    return render_template("tugas.html", assignments=assignments, subs=subs)


@app.route("/berkas/<int:sub_id>")
@login_required()
def berkas(sub_id):
    s = db().execute("SELECT * FROM submissions WHERE id=?", (sub_id,)).fetchone()
    if not s:
        abort(404)
    if g.user["role"] == "mahasiswa" and s["student_id"] != g.user["id"]:
        abort(403)
    return send_from_directory(UPLOAD_DIR, s["stored_name"], as_attachment=True,
                               download_name=s["original_name"])


# ---------------------------------------------------------------- diskusi
def can_access_course(user, cid):
    if user["role"] == "admin":
        return True
    if user["role"] == "dosen":
        return bool(db().execute("SELECT 1 FROM courses WHERE id=? AND lecturer_id=?", (cid, user["id"])).fetchone())
    return bool(db().execute("SELECT 1 FROM enrollments WHERE course_id=? AND student_id=?", (cid, user["id"])).fetchone())


@app.route("/diskusi/<int:cid>", methods=["GET", "POST"])
@login_required()
def diskusi(cid):
    if not can_access_course(g.user, cid):
        abort(403)
    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if body:
            db().execute("INSERT INTO posts(course_id,user_id,body) VALUES(?,?,?)", (cid, g.user["id"], body))
            db().commit()
        return redirect(url_for("diskusi", cid=cid))
    course = db().execute("SELECT * FROM courses WHERE id=?", (cid,)).fetchone() or abort(404)
    posts = db().execute("""SELECT p.*, u.full_name, u.role FROM posts p JOIN users u ON u.id=p.user_id
                            WHERE p.course_id=? ORDER BY p.id DESC""", (cid,)).fetchall()
    return render_template("diskusi.html", course=course, posts=posts)


# ---------------------------------------------------------------- pencarian
@app.route("/cari")
@login_required()
def cari():
    q = request.args.get("q", "")
    rows, error = [], None
    if q:
        # [KERENTANAN SENGAJA #2 - SQL injection] input digabung langsung ke query.
        sql = f"SELECT id, code, name FROM courses WHERE name LIKE '%{q}%' OR code LIKE '%{q}%'"
        try:
            rows = db().execute(sql).fetchall()
        except sqlite3.Error as e:
            error = f"Kesalahan database: {e}"
    return render_template("cari.html", q=q, rows=rows, error=error)


# ---------------------------------------------------------------- dosen
@app.route("/dosen/nilai/<int:cid>", methods=["GET", "POST"])
@login_required("dosen")
def dosen_nilai(cid):
    c = db().execute("SELECT * FROM courses WHERE id=? AND lecturer_id=?", (cid, g.user["id"])).fetchone() or abort(403)
    if request.method == "POST":
        for key, val in request.form.items():
            if key.startswith("score_") and val != "":
                sid = int(key[6:])
                try:
                    score = max(0.0, min(100.0, float(val)))
                except ValueError:
                    continue
                if db().execute("SELECT 1 FROM enrollments WHERE student_id=? AND course_id=?", (sid, cid)).fetchone():
                    db().execute("""INSERT INTO grades(student_id,course_id,score,note) VALUES(?,?,?,?)
                                    ON CONFLICT(student_id,course_id) DO UPDATE SET score=excluded.score""",
                                 (sid, cid, score, request.form.get("note_" + str(sid), "")))
        db().commit()
        flash("Nilai tersimpan.")
        return redirect(url_for("dosen_nilai", cid=cid))
    students = db().execute("""SELECT u.id, u.full_name, u.ident, g.score FROM enrollments e
                               JOIN users u ON u.id=e.student_id
                               LEFT JOIN grades g ON g.student_id=u.id AND g.course_id=e.course_id
                               WHERE e.course_id=?""", (cid,)).fetchall()
    subs = db().execute("""SELECT s.id, s.original_name, u.full_name, a.title FROM submissions s
                           JOIN assignments a ON a.id=s.assignment_id JOIN users u ON u.id=s.student_id
                           WHERE a.course_id=? ORDER BY s.id DESC""", (cid,)).fetchall()
    return render_template("dosen_nilai.html", course=c, students=students, subs=subs)


# ---------------------------------------------------------------- admin
@app.route("/admin", methods=["GET", "POST"])
@login_required("admin")
def admin():
    if request.method == "POST":
        act = request.form.get("act")
        uid = request.form.get("uid", type=int)
        if act == "create":
            try:
                db().execute("INSERT INTO users(username,password_hash,role,full_name,ident) VALUES(?,?,?,?,?)",
                             (request.form["username"], generate_password_hash(request.form["password"]),
                              request.form["role"] if request.form["role"] in ("mahasiswa", "dosen", "admin") else "mahasiswa",
                              request.form["full_name"], request.form.get("ident", "")))
                flash("Akun dibuat.")
            except sqlite3.IntegrityError:
                flash("Username sudah dipakai.")
        elif act == "toggle" and uid != g.user["id"]:
            db().execute("UPDATE users SET active=1-active WHERE id=?", (uid,))
        elif act == "reset":
            db().execute("UPDATE users SET password_hash=? WHERE id=?",
                         (generate_password_hash(request.form["password"]), uid))
            flash("Sandi direset.")
        elif act == "delete" and uid != g.user["id"]:
            db().execute("DELETE FROM users WHERE id=?", (uid,))
        db().commit()
        return redirect(url_for("admin"))
    users = db().execute("SELECT * FROM users ORDER BY role, id").fetchall()
    return render_template("admin.html", users=users)


init_db()
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
