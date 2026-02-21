from flask import Flask, request, jsonify, render_template
import psycopg2
import os
from sentence_transformers import SentenceTransformer

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

# تحميل نموذج الذكاء (يفهم عربي)
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def get_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def get_embedding(text):
    return model.encode(text).tolist()

# إنشاء الجدول
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id SERIAL PRIMARY KEY,
            question TEXT,
            answer TEXT,
            embedding vector(384)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

@app.route("/")
def home():
    return render_template("index.html")

# إضافة سؤال
@app.route("/add", methods=["POST"])
def add():
    data = request.json
    question = data["question"]
    answer = data["answer"]

    embedding = get_embedding(question)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO memory (question, answer, embedding)
        VALUES (%s, %s, %s)
    """, (question, answer, embedding))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "تمت الإضافة"})

# سؤال البوت
@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    user_question = data["question"]

    embedding = get_embedding(user_question)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT answer
        FROM memory
        ORDER BY embedding <-> %s
        LIMIT 1
    """, (embedding,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if result:
        return jsonify({"answer": result[0]})
    else:
        return jsonify({"answer": "لا أعرف الإجابة 🤖"})
        
if __name__ == "__main__":
    app.run()
