from flask import Flask, jsonify
import psycopg2
import os

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "claimiq"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=os.getenv("DB_PORT", "5432")
    )


@app.route("/")
def home():
    return jsonify({
        "message": "Backend is running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })


@app.route("/users")
def users():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, name FROM users ORDER BY id")

    rows = cursor.fetchall()

    cursor.close()
    connection.close()

    users = []

    for row in rows:
        users.append({
            "id": row[0],
            "name": row[1]
        })

    return jsonify(users)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)