from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path
from datetime import date, timedelta

app = Flask(__name__)
app.secret_key = "change-this-demo-secret"
DB_PATH = Path(__file__).with_name("meditrack.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity >= 0),
                expiry_date TEXT NOT NULL,
                person TEXT NOT NULL,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        count = db.execute("SELECT COUNT(*) FROM medicines").fetchone()[0]
        if count == 0:
            today = date.today()
            samples = [
                ("Paracetamol", "Tablet", 20, (today + timedelta(days=120)).isoformat(), "Aarav", "Demo record"),
                ("Vitamin C", "Supplement", 5, (today + timedelta(days=12)).isoformat(), "Riya", "Demo record"),
                ("Cough Syrup", "Syrup", 2, (today + timedelta(days=7)).isoformat(), "Aarav", "Demo record"),
                ("Antacid", "Tablet", 3, (today + timedelta(days=210)).isoformat(), "Family", "Demo record"),
                ("Old first-aid item", "Other", 1, (today - timedelta(days=4)).isoformat(), "Family", "Demo expired record"),
            ]
            db.executemany("""
                INSERT INTO medicines (name, category, quantity, expiry_date, person, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, samples)

def medicine_status(expiry_date):
    days_left = (date.fromisoformat(expiry_date) - date.today()).days
    if days_left < 0:
        return "Expired", days_left
    if days_left <= 30:
        return "Expiring soon", days_left
    return "Safe", days_left

@app.route("/")
def dashboard():
    with get_db() as db:
        rows = db.execute("SELECT * FROM medicines ORDER BY expiry_date ASC").fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["status"], item["days_left"] = medicine_status(item["expiry_date"])
        items.append(item)

    stats = {
        "total": len(items),
        "expired": sum(x["status"] == "Expired" for x in items),
        "soon": sum(x["status"] == "Expiring soon" for x in items),
        "low": sum(x["quantity"] <= 5 for x in items),
    }
    attention = [x for x in items if x["status"] != "Safe" or x["quantity"] <= 5][:5]
    return render_template("dashboard.html", stats=stats, medicines=items[:6], attention=attention)

@app.route("/medicines")
def medicines():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    query = "SELECT * FROM medicines WHERE 1=1"
    params = []
    if q:
        query += " AND (name LIKE ? OR person LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY expiry_date ASC"
    with get_db() as db:
        rows = db.execute(query, params).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["status"], item["days_left"] = medicine_status(item["expiry_date"])
        items.append(item)
    return render_template("medicines.html", medicines=items, q=q, category=category)

def validate_form(form):
    name = form.get("name", "").strip()
    category = form.get("category", "").strip()
    person = form.get("person", "").strip()
    expiry = form.get("expiry_date", "").strip()
    notes = form.get("notes", "").strip()
    try:
        quantity = int(form.get("quantity", ""))
        date.fromisoformat(expiry)
    except (ValueError, TypeError):
        return None, "Please enter a valid quantity and expiry date."
    if not name or not category or not person:
        return None, "Please fill in all required fields."
    if quantity < 0:
        return None, "Quantity cannot be negative."
    return (name, category, quantity, expiry, person, notes), None

@app.route("/add", methods=["GET", "POST"])
def add_medicine():
    if request.method == "POST":
        values, error = validate_form(request.form)
        if error:
            flash(error, "error")
            return render_template("medicine_form.html", medicine=request.form, page_title="Add medicine")
        with get_db() as db:
            db.execute("""
                INSERT INTO medicines (name, category, quantity, expiry_date, person, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, values)
        flash("Medicine added successfully.", "success")
        return redirect(url_for("medicines"))
    return render_template("medicine_form.html", medicine={}, page_title="Add medicine")

@app.route("/edit/<int:medicine_id>", methods=["GET", "POST"])
def edit_medicine(medicine_id):
    with get_db() as db:
        row = db.execute("SELECT * FROM medicines WHERE id = ?", (medicine_id,)).fetchone()
    if row is None:
        flash("Medicine record not found.", "error")
        return redirect(url_for("medicines"))
    if request.method == "POST":
        values, error = validate_form(request.form)
        if error:
            flash(error, "error")
            return render_template("medicine_form.html", medicine=request.form, page_title="Edit medicine")
        with get_db() as db:
            db.execute("""
                UPDATE medicines
                SET name=?, category=?, quantity=?, expiry_date=?, person=?, notes=?
                WHERE id=?
            """, (*values, medicine_id))
        flash("Medicine updated successfully.", "success")
        return redirect(url_for("medicines"))
    return render_template("medicine_form.html", medicine=dict(row), page_title="Edit medicine")

@app.route("/delete/<int:medicine_id>", methods=["POST"])
def delete_medicine(medicine_id):
    with get_db() as db:
        db.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
    flash("Medicine record deleted.", "success")
    return redirect(url_for("medicines"))

@app.route("/alerts")
def alerts():
    with get_db() as db:
        rows = db.execute("SELECT * FROM medicines ORDER BY expiry_date ASC").fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["status"], item["days_left"] = medicine_status(item["expiry_date"])
        if item["status"] != "Safe" or item["quantity"] <= 5:
            items.append(item)
    return render_template("alerts.html", medicines=items)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
