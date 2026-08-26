from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime, date

app = Flask(__name__)

# ---------------------------------------------------------------------------
# TEMPORARY DATA LAYER
# This is a stand-in for the database. Everything in this section is meant
# to be replaced later by your friend's actual DB code (sqlite3 / SQLAlchemy).
#
# IMPORTANT FOR HANDOFF:
# Keep the function names and return shapes (add_medicine, get_medicines)
# the same when swapping in the real DB. As long as get_medicines() keeps
# returning a list of dicts with these exact keys, none of the routes or
# templates below need to change.
# ---------------------------------------------------------------------------

_medicines = []
_next_id = 1


def add_medicine(name, brand, description, mfg_date, exp_date, quantity):
    global _next_id
    medicine = {
        "id": _next_id,
        "name": name,
        "brand": brand,
        "description": description,
        "mfg_date": mfg_date,   # stored as string "YYYY-MM-DD"
        "exp_date": exp_date,   # stored as string "YYYY-MM-DD"
        "quantity": quantity,
    }
    _medicines.append(medicine)
    _next_id += 1
    return medicine


def get_medicines():
    return _medicines


# ---------------------------------------------------------------------------
# EXPIRY CLASSIFICATION LOGIC
# Pure logic, no DB writes. Computes status at request time instead of
# physically moving records between tables. This avoids the bug class where
# a corrected expiry date would need the record moved back.
# ---------------------------------------------------------------------------

def classify_medicine(medicine):
    """Returns 'expired', 'expiring_soon', or 'safe' based on exp_date."""
    exp = datetime.strptime(medicine["exp_date"], "%Y-%m-%d").date()
    today = date.today()
    days_left = (exp - today).days

    if days_left < 0:
        return "expired"
    elif days_left <= 7:
        return "expiring_soon"
    else:
        return "safe"


def get_medicines_by_status(status):
    return [m for m in get_medicines() if classify_medicine(m) == status]


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
def add():
    error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        brand = request.form.get("brand", "").strip()
        description = request.form.get("description", "").strip()
        mfg_date = request.form.get("mfg_date", "").strip()
        exp_date = request.form.get("exp_date", "").strip()
        quantity = request.form.get("quantity", "").strip()

        # --- basic validation (Flask does not validate for you) ---
        if not name or not mfg_date or not exp_date or not quantity:
            error = "Name, manufacture date, expiry date, and quantity are required."
        else:
            try:
                quantity = int(quantity)
                if quantity < 0:
                    raise ValueError
            except ValueError:
                error = "Quantity must be a non-negative whole number."

            if not error:
                mfg = datetime.strptime(mfg_date, "%Y-%m-%d").date()
                exp = datetime.strptime(exp_date, "%Y-%m-%d").date()
                if exp <= mfg:
                    error = "Expiry date must be after manufacture date."

        if not error:
            add_medicine(name, brand, description, mfg_date, exp_date, quantity)
            return redirect(url_for("dashboard"))

    return render_template("add_medicine.html", error=error)


@app.route("/dashboard")
def dashboard():
    medicines = []
    for m in get_medicines():
        entry = dict(m)
        entry["status"] = classify_medicine(m)
        medicines.append(entry)
    return render_template("dashboard.html", medicines=medicines)


@app.route("/expiring-soon")
def expiring_soon():
    medicines = get_medicines_by_status("expiring_soon")
    return render_template("expiring_soon.html", medicines=medicines)


@app.route("/expired")
def expired():
    medicines = get_medicines_by_status("expired")
    return render_template("expired.html", medicines=medicines)


if __name__ == "__main__":
    app.run(debug=True)