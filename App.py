from flask import Flask, render_template
import mysql.connector

app = Flask(__name__)


def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="YOUR_MYSQL_PASSWORD",
        database="pharmacy_db"
    )

    return connection


@app.route("/")
def home():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute("SELECT * FROM medicines")

    medicines = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "index.html",
        medicines=medicines
    )


if __name__ == "__main__":
    app.run(debug=True)