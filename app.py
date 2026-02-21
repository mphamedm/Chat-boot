from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import psycopg2
import os
from difflib import SequenceMatcher

app = Flask(__name__)
CORS(app)

BOT_NAME = "محسن"

# ===============================
# إعداد Gemini API
# ===============================
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

def ask_ai(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return None

# ===============================
# إعداد قاعدة البيانات
# ===============================
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id SERIAL PRIMARY KEY,
            question TEXT,
            answer TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

# ===============================
# البحث في الذاكرة
# ===============================
def search_memory(question):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT question, answer FROM memory")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    best_score = 0
    best_answer = None

    for q, a in rows:
        score = SequenceMatcher(None, question.lower(), q.lower()).ratio()
        if score > best_score:
            best_score = score
            best_answer = a

    if best_score > 0.75:
        return best_answer
    return None

def save_memory(question, answer):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO memory (question, answer) VALUES (%s, %s)",
        (question, answer)
    )
    conn.commit()
    cur.close()
    conn.close()

# ===============================
# الصفحات
# ===============================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()

    if not user_input:
        return jsonify({"reply": "اكتب رسالة أولاً"})

    # 1️⃣ البحث في الذاكرة
    memory_answer = search_memory(user_input)
    if memory_answer:
        return jsonify({"reply": f"{BOT_NAME}: {memory_answer} 🧠"})

    # 2️⃣ سؤال الذكاء الاصطناعي
    ai_response = ask_ai(user_input)

    if ai_response:
        save_memory(user_input, ai_response)
        return jsonify({"reply": f"{BOT_NAME}: {ai_response} 🤖"})

    return jsonify({"reply": "حدث خطأ، حاول مرة أخرى"})

# ===============================
# اختبار قاعدة البيانات
# ===============================
@app.route("/test-db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return "✅ Database Connected Successfully!"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ===============================
# تشغيل التطبيق
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
