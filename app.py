from flask import Flask, request, jsonify, render_template
import psycopg2
import os

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def simple_similarity(a, b):
    a_words = set(a.split())
    b_words = set(b.split())
    return len(a_words & b_words) / max(len(a_words), 1)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_question = data["question"]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT question, answer FROM memory")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    best_score = 0
    best_answer = "لا أعرف الإجابة 🤖"

    for q, a in rows:
        score = simple_similarity(user_question, q)
        if score > best_score:
            best_score = score
            best_answer = a

    if best_score > 0.3:
        return jsonify({"answer": best_answer})
    else:
        return jsonify({"answer": "لا أعرف الإجابة 🤖"})
