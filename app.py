from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def get_all_questions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT question, answer FROM memory")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_question = data["question"]

    rows = get_all_questions()

    if not rows:
        return jsonify({"answer": "لا توجد بيانات بعد"})

    questions = [row[0] for row in rows]
    answers = [row[1] for row in rows]

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(questions + [user_question])

    similarity = cosine_similarity(
        vectors[-1], vectors[:-1]
    )

    best_match_index = similarity.argmax()

    if similarity[0][best_match_index] > 0.3:
        return jsonify({"answer": answers[best_match_index]})
    else:
        return jsonify({"answer": "لا أعرف الإجابة 🤖"})
