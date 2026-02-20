from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json, os, datetime, re
from sympy import sympify

app = Flask(__name__)
CORS(app)

BOT_NAME = "محسن"
brain_file = "brain.json"
math_file = "math_brain.json"

# =========================
# تحميل وحفظ البيانات
# =========================
def load_memory():
    if not os.path.exists(brain_file):
        return []
    with open(brain_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(data):
    with open(brain_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_math_memory():
    if not os.path.exists(math_file):
        return {}
    with open(math_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_math_memory(data):
    with open(math_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================
# ذكاء بسيط للأسئلة
# =========================
def smart_match(user_input, memory):
    user_input = user_input.strip().lower()
    best_answer = None

    for item in memory:
        if item["question"].lower() in user_input:
            best_answer = item["answer"]

    return best_answer

# =========================
# حل مسائل رياضية (جمع وطرح)
# =========================
def solve_math(expression):
    try:
        memory = load_math_memory()
        expression = expression.replace(" ", "").strip()

        # إذا تعلمها سابقًا
        if expression in memory:
            return f"📘 تعلمت سابقًا:\n{expression} = {memory[expression]}"

        # يسمح فقط بالأرقام والجمع والطرح
        allowed = "0123456789+-."
        for char in expression:
            if char not in allowed:
                return None

        result = sympify(expression)
        return f"📘 الناتج = {result}"

    except:
        return None

# =========================
# الصفحة الرئيسية
# =========================
@app.route("/")
def home():
    return render_template("index.html")

# =========================
# API الدردشة
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()

    # ===== تعليم عام =====
    if user_input.startswith("تعلم:"):
        try:
            content = user_input.replace("تعلم:", "").strip()
            question, answer = content.split("=")

            memory = load_memory()
            memory.append({
                "question": question.strip(),
                "answer": answer.strip()
            })
            save_memory(memory)

            return jsonify({"reply": "🤖 تم التعلم بنجاح ✅"})
        except:
            return jsonify({"reply": "⚠️ استخدم الصيغة:\nتعلم: السؤال = الإجابة"})

    # ===== تعليم رياضيات =====
    if user_input.startswith("تعلم رياضيات:"):
        try:
            content = user_input.replace("تعلم رياضيات:", "").strip()
            question, answer = content.split("=")

            memory = load_math_memory()
            memory[question.replace(" ", "")] = answer.strip()
            save_math_memory(memory)

            return jsonify({"reply": "🤖 تم تعلم المسألة الرياضية ✅"})
        except:
            return jsonify({"reply": "⚠️ استخدم الصيغة:\nتعلم رياضيات: 5+7 = 12"})

    # ===== حل رياضيات =====
    math_result = solve_math(user_input)
    if math_result:
        return jsonify({"reply": f"{BOT_NAME}: {math_result}"})

    # ===== سؤال عن الوقت =====
    if "الوقت" in user_input:
        now = datetime.datetime.now().strftime("%H:%M")
        return jsonify({"reply": f"{BOT_NAME}: الوقت الآن {now}"})

    # ===== بحث في الذاكرة =====
    memory = load_memory()
    answer = smart_match(user_input, memory)
    if answer:
        return jsonify({"reply": f"{BOT_NAME}: {answer}"})

    return jsonify({"reply": f"{BOT_NAME}: لا أعرف الإجابة 🤔"})

# =========================
if __name__ == "__main__":
    app.run(debug=True)
