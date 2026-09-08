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
            "manufacturing_date",
            ""
        ).strip()

        expiry_date = request.form.get(
            "expiry_date",
            ""
        ).strip()

        min_stock = request.form.get(
            "min_stock",
            "10"
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

                cursor.execute(
                    query,
                    values
                )

                connection.commit()

                cursor.close()
                connection.close()

                return redirect(
                    url_for("dashboard")
                )

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
# MEDICINES INVENTORY
# ==========================================

@app.route("/medicines")
def medicines():

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

    medicine_list = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "medicines.html",
        medicines=medicine_list
    )

# ==========================================
# SALES PAGE
# ==========================================

@app.route("/sales", methods=["GET", "POST"])
def sales():

    connection = get_db_connection()
    cursor = connection.cursor()

    message = None
    error = None

    if request.method == "POST":

        medicine_id = request.form.get("medicine_id", "").strip()
        sold_quantity = request.form.get("quantity", "").strip()

        # -----------------------------
        # Validate medicine
        # -----------------------------

        if not medicine_id:
            error = "Please select a medicine."

        elif not sold_quantity:
            error = "Please enter quantity."

        # -----------------------------
        # Convert quantity
        # -----------------------------

        if not error:

            try:
                sold_quantity = int(sold_quantity)

                if sold_quantity <= 0:
                    error = "Quantity must be greater than 0."

            except ValueError:
                error = "Quantity must be a whole number."

        # -----------------------------
        # Get medicine
        # -----------------------------

        if not error:

            cursor.execute("""
                SELECT
                    id,
                    name,
                    quantity,
                    price
                FROM medicines
                WHERE id = %s
            """, (medicine_id,))

            medicine = cursor.fetchone()

            if not medicine:
                error = "Medicine not found."

        # -----------------------------
        # Check stock
        # -----------------------------

        if not error:

            current_stock = medicine[2]

            if sold_quantity > current_stock:

                error = (
                    f"Only {current_stock} units "
                    "are available in stock."
                )

        # -----------------------------
        # Complete sale
        # -----------------------------

        if not error:

            new_stock = current_stock - sold_quantity

            cursor.execute("""
                UPDATE medicines
                SET quantity = %s
                WHERE id = %s
            """, (new_stock, medicine_id))

            connection.commit()

            total = sold_quantity * float(medicine[3])

            message = (
                f"Sale completed successfully! "
                f"Total: ₹{total:.2f}. "
                f"Remaining stock: {new_stock}"
            )

    # -----------------------------
    # Get all medicines
    # -----------------------------

    cursor.execute("""
        SELECT
            id,
            name,
            quantity,
            price
        FROM medicines
        ORDER BY name ASC
    """)

    medicines = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "sales.html",
        medicines=medicines,
        message=message,
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


    # ======================================
    # ADD EXPIRY AND STOCK STATUS
    # ======================================

    medicine_list = []

    today = date.today()

    for medicine in medicines:

        expiry_date = medicine[7]

        quantity = medicine[4]

        min_stock = medicine[8]


        # -----------------------------
        # Calculate days remaining
        # -----------------------------

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


        # -----------------------------
        # Create medicine dictionary
        # -----------------------------

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


    # ======================================
    # DASHBOARD SUMMARY
    # ======================================

    summary = {

        "total": len(medicine_list),

        "expired": sum(
            1
            for m in medicine_list
            if m["expiry_status"] == "Expired"
        ),

        "expiring": sum(
            1
            for m in medicine_list
            if m["expiry_status"] == "Expiring Soon"
        ),

        "low_stock": sum(
            1
            for m in medicine_list
            if m["stock_status"] == "Low Stock"
        )

    }


    # ======================================
    # SEND DATA TO DASHBOARD
    # ======================================

    return render_template(

        "dashboard.html",

        medicines=medicine_list,

        summary=summary

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
        AND expiry_date <= DATE_ADD(CURDATE(), INTERVAL 7 DAY)
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
# DELETE MEDICINE
# ==========================================

@app.route("/delete/<int:medicine_id>", methods=["POST"])
def delete_medicine(medicine_id):

    connection = get_db_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            "DELETE FROM medicines WHERE id = %s",
            (medicine_id,)
        )

        connection.commit()

    except mysql.connector.Error as e:

        connection.rollback()

        print("Database error:", e)

    finally:

        cursor.close()
        connection.close()

    return redirect(url_for("dashboard"))


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)