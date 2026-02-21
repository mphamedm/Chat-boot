from flask import Flask, request, jsonify, render_template
import requests
import os
import psycopg2
from difflib import SequenceMatcher

app = Flask(__name__)

BOT_NAME = "محسن"
API_KEY = os.environ.get("GEMINI_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

# -----------------------------
# التحقق من وجود API Key
# -----------------------------
if not API_KEY:
    print("⚠️ API KEY غير موجود! أضفه في Environment Variables على Render")

# -----------------------------
# إنشاء جدول المحادثات
# -----------------------------
def init_db():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id SERIAL PRIMARY KEY,
                question TEXT,
                answer TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database Ready")
    except Exception as e:
        print("❌ Database Error:", e)

init_db()

# -----------------------------
# البحث عن سؤال مشابه في الذاكرة
# -----------------------------
def search_memory(question):
    conn = psycopg2.connect(DATABASE_URL)
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

# -----------------------------
# حفظ سؤال وجواب في قاعدة البيانات
# -----------------------------
def save_memory(question, answer):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO memory (question, answer) VALUES (%s, %s)",
        (question, answer)
    )
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------
# الصفحة الرئيسية
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# API الدردشة
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    user_answer = request.json.get("answer", "").strip()  # إذا المستخدم يعطي الإجابة

    if not user_message:
        return jsonify({"reply": "اكتب رسالة أولاً"})

    # 1️⃣ البحث في الذاكرة
    memory_answer = search_memory(user_message)
    if memory_answer:
        return jsonify({"reply": f"{BOT_NAME}: {memory_answer} 🧠 (من الذاكرة)"})

    # 2️⃣ إذا المستخدم أعطى الإجابة → خزنها
    if user_answer:
        save_memory(user_message, user_answer)
        return jsonify({"reply": f"{BOT_NAME}: شكرًا! لقد تعلمت الإجابة ✅"})

    # 3️⃣ لم يعرف → يطلب من المستخدم الإجابة
    return jsonify({
        "reply": f"{BOT_NAME}: لا أعرف الإجابة بعد 🤔\nهل يمكنك إعطائي الإجابة؟",
        "learn": True
    })

# -----------------------------
# عرض آخر المحادثات
# -----------------------------
@app.route("/history")
def history():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT question, answer, created_at FROM memory ORDER BY id DESC LIMIT 20")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        data = [{"question": r[0], "answer": r[1], "time": str(r[2])} for r in rows]
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)})

# -----------------------------
# تشغيل التطبيق
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
