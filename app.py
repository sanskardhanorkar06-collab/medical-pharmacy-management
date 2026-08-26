from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from datetime import date

app = Flask(__name__)


# ==========================================
# DATABASE CONNECTION
# ==========================================

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Prabhansh@2006",
        database="pharmacy_db"
    )


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            batch_no,
            category,
            quantity,
            price,
            manufacturing_date,
            expiry_date,
            min_stock
        FROM medicines
        ORDER BY id DESC
    """)

    medicines = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "index.html",
        medicines=medicines
    )


# ==========================================
# ADD MEDICINE
# ==========================================

@app.route("/add", methods=["GET", "POST"])
def add():

    error = None

    if request.method == "POST":

        # Get form data
        name = request.form.get("name", "").strip()
        batch_no = request.form.get("batch_no", "").strip()
        category = request.form.get("category", "").strip()
        quantity = request.form.get("quantity", "").strip()
        price = request.form.get("price", "").strip()
        manufacturing_date = request.form.get(
            "manufacturing_date", ""
        ).strip()
        expiry_date = request.form.get(
            "expiry_date", ""
        ).strip()
        min_stock = request.form.get(
            "min_stock", "10"
        ).strip()


        # -----------------------------
        # Validation
        # -----------------------------

        if not name:
            error = "Medicine name is required."

        elif not batch_no:
            error = "Batch number is required."

        elif not quantity:
            error = "Quantity is required."

        elif not price:
            error = "Price is required."

        elif not manufacturing_date:
            error = "Manufacturing date is required."

        elif not expiry_date:
            error = "Expiry date is required."


        # -----------------------------
        # Convert numbers
        # -----------------------------

        if not error:

            try:
                quantity = int(quantity)

                if quantity < 0:
                    error = "Quantity cannot be negative."

            except ValueError:
                error = "Quantity must be a whole number."


        if not error:

            try:
                price = float(price)

                if price < 0:
                    error = "Price cannot be negative."

            except ValueError:
                error = "Price must be a valid number."


        if not error:

            try:
                min_stock = int(min_stock)

                if min_stock < 0:
                    error = "Minimum stock cannot be negative."

            except ValueError:
                error = "Minimum stock must be a whole number."


        # -----------------------------
        # Check dates
        # -----------------------------

        if not error:

            try:

                mfg_date = date.fromisoformat(
                    manufacturing_date
                )

                exp_date = date.fromisoformat(
                    expiry_date
                )

                if exp_date <= mfg_date:

                    error = (
                        "Expiry date must be after "
                        "manufacturing date."
                    )

            except ValueError:

                error = "Invalid date format."


        # -----------------------------
        # Insert into MySQL
        # -----------------------------

        if not error:

            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO medicines
                (
                    name,
                    batch_no,
                    category,
                    quantity,
                    price,
                    manufacturing_date,
                    expiry_date,
                    min_stock
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                name,
                batch_no,
                category,
                quantity,
                price,
                manufacturing_date,
                expiry_date,
                min_stock
            )

            try:

                cursor.execute(query, values)

                connection.commit()

                cursor.close()
                connection.close()

                return redirect(url_for("dashboard"))

            except mysql.connector.Error as e:

                connection.rollback()

                cursor.close()
                connection.close()

                error = f"Database error: {e}"


    return render_template(
        "add_medicine.html",
        error=error
    )


# ==========================================
# DASHBOARD
# ==========================================

@app.route("/dashboard")
def dashboard():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            batch_no,
            category,
            quantity,
            price,
            manufacturing_date,
            expiry_date,
            min_stock
        FROM medicines
        ORDER BY id DESC
    """)

    medicines = cursor.fetchall()

    cursor.close()
    connection.close()


    # Add expiry and stock status
    medicine_list = []

    today = date.today()

    for medicine in medicines:

        expiry_date = medicine[7]
        quantity = medicine[4]
        min_stock = medicine[8]

        # Calculate days remaining
        days_left = (
            expiry_date - today
        ).days


        # -----------------------------
        # Expiry Status
        # -----------------------------

        if days_left < 0:

            expiry_status = "Expired"

        elif days_left <= 30:

            expiry_status = "Expiring Soon"

        else:

            expiry_status = "Safe"


        # -----------------------------
        # Stock Status
        # -----------------------------

        if quantity <= min_stock:

            stock_status = "Low Stock"

        else:

            stock_status = "Available"


        medicine_list.append({
            "id": medicine[0],
            "name": medicine[1],
            "batch_no": medicine[2],
            "category": medicine[3],
            "quantity": medicine[4],
            "price": medicine[5],
            "manufacturing_date": medicine[6],
            "expiry_date": medicine[7],
            "min_stock": medicine[8],
            "days_left": days_left,
            "expiry_status": expiry_status,
            "stock_status": stock_status
        })


    return render_template(
        "dashboard.html",
        medicines=medicine_list
    )


# ==========================================
# EXPIRING SOON
# ==========================================

@app.route("/expiring-soon")
def expiring_soon():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            batch_no,
            category,
            quantity,
            price,
            manufacturing_date,
            expiry_date,
            min_stock
        FROM medicines
        WHERE expiry_date >= CURDATE()
        AND expiry_date <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
        ORDER BY expiry_date ASC
    """)

    medicines = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "expiring_soon.html",
        medicines=medicines
    )


# ==========================================
# EXPIRED MEDICINES
# ==========================================

@app.route("/expired")
def expired():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            batch_no,
            category,
            quantity,
            price,
            manufacturing_date,
            expiry_date,
            min_stock
        FROM medicines
        WHERE expiry_date < CURDATE()
        ORDER BY expiry_date ASC
    """)

    medicines = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "expired.html",
        medicines=medicines
    )


# ==========================================
# LOW STOCK
# ==========================================

@app.route("/low-stock")
def low_stock():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            batch_no,
            category,
            quantity,
            price,
            manufacturing_date,
            expiry_date,
            min_stock
        FROM medicines
        WHERE quantity <= min_stock
        ORDER BY quantity ASC
    """)

    medicines = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "low_stock.html",
        medicines=medicines
    )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)