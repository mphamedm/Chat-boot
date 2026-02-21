import os
from flask import Flask, request, jsonify, render_template
import psycopg2
from psycopg2.extras import RealDictCursor
from difflib import SequenceMatcher
import google.generativeai as genai

# -----------------------------
# إعداد التطبيق
# -----------------------------
app = Flask(__name__)

BOT_NAME = "ChatBot"
API_KEY = os.environ.get("GEMINI_API_KEY")
DATABASE_URL = os.environ.get("DATABASE_URL")

# -----------------------------
# التحقق من API Key
# -----------------------------
if not API_KEY:
    print("⚠️ GEMINI_API_KEY غير موجود! أضفه في Environment Variables")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# -----------------------------
# إنشاء جدول الذاكرة
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
# البحث في الذاكرة
# -----------------------------
def search_memory(question, threshold=0.75):
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        cur.execute("SELECT question, answer FROM memory")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        best_score = 0
        best_answer = None
        for row in rows:
            q = row['question']
            a = row['answer']
            score = SequenceMatcher(None, question.lower(), q.lower()).ratio()
            if score > best_score:
                best_score = score
                best_answer = a
        if best_score >= threshold:
            return best_answer
    except Exception as e:
        print("❌ Search Memory Error:", e)
    return None

# -----------------------------
# حفظ سؤال وجواب
# -----------------------------
def save_memory(question, answer):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO memory (question, answer) VALUES (%s, %s)",
            (question, answer)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("❌ Save Memory Error:", e)

# -----------------------------
# الصفحة الرئيسية
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -----------------------------
# API الشات
# -----------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "").strip()
    user_answer = data.get("answer", "").strip()

    if not user_message:
        return jsonify({"reply": "اكتب سؤالاً أولاً"})

    # 1️⃣ البحث في الذاكرة أولاً
    memory_answer = search_memory(user_message)
    if memory_answer:
        return jsonify({"reply": memory_answer})

    # 2️⃣ استخدام Gemini API
    if API_KEY:
        try:
            response = model.generate_content(user_message)
            bot_reply = response.text
            # حفظ السؤال والجواب تلقائياً
            save_memory(user_message, bot_reply)
            return jsonify({"reply": bot_reply})
        except Exception as e:
            print("❌ Gemini API Error:", e)

    # 3️⃣ طلب إجابة من المستخدم إذا لم يرد API
    if user_answer:
        save_memory(user_message, user_answer)
        return jsonify({"reply": "شكراً! لقد تعلمت الإجابة ✅"})

    return jsonify({
        "reply": "لم أتمكن من الإجابة 🤔 هل يمكنك إعطائي الإجابة؟",
        "learn": True
    })

# -----------------------------
# تشغيل التطبيق
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
