from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json, os, datetime

app = Flask(__name__)
CORS(app)

BOT_NAME = "محسن"
brain_file = "brain.json"

# -------------------------
# تحميل وحفظ البيانات
# -------------------------
def load_memory():
    if not os.path.exists(brain_file):
        return []
    with open(brain_file, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------
# تنظيف وتحويل النص لكلمات
# -------------------------
def clean_words(text):
    return text.replace("؟","").replace(".","").replace(",","").strip().lower().split()

# -------------------------
# البحث عن إجابة بطريقة ذكية
# -------------------------
def smart_match(user_input, memory):
    user_words = set(clean_words(user_input))
    best_score = 0
    best_answer = None

    for item in memory:
        item_words = set(clean_words(item["question"]))
        common_words = user_words & item_words
        score = len(common_words) / max(len(user_words), 1)
        if score > best_score:
            best_score = score
            best_answer = item["answer"]

    if best_score > 0.3:  # نسبة 30% تعتبر تطابق
        return best_answer
    return None

# -------------------------
# الصفحة الرئيسية
# -------------------------
@app.route("/")
def home():
    return render_template("index.html")

# -------------------------
# API الدردشة
# -------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    memory = load_memory()

    # سؤال عن الوقت
    if "الوقت" in user_input:
        now = datetime.datetime.now().strftime("%H:%M")
        return jsonify({"reply": f"{BOT_NAME}: الوقت الآن هو {now}"})

    # البحث عن إجابة ذكية
    answer = smart_match(user_input, memory)
    if answer:
        return jsonify({"reply": f"{BOT_NAME}: {answer}"})
    
    # إذا لم يجد إجابة
    return jsonify({"reply": f"{BOT_NAME}: لا أعرف الإجابة بعد."})

# -------------------------
if __name__ == "__main__":
    app.run()