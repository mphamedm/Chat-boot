from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json, os, datetime, re
import ast
import operator as op

app = Flask(__name__)
CORS(app)

BOT_NAME = "محسن"
brain_file = "brain.json"

# =============================
# تحميل وحفظ البيانات
# =============================
def load_memory():
    if not os.path.exists(brain_file):
        return []
    with open(brain_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(data):
    with open(brain_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =============================
# آلة حاسبة آمنة بدون eval
# =============================

operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
}

def safe_calculate(expr):
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](
                eval_node(node.left),
                eval_node(node.right)
            )
        else:
            raise TypeError("عملية غير مسموحة")

    node = ast.parse(expr, mode='eval').body
    return eval_node(node)

# =============================
# حل جميع العمليات
# =============================
def solve_math(text):
    text = text.strip()

    # تحويل × ÷ إلى رموز
    text = text.replace("×", "*")
    text = text.replace("÷", "/")

    # لو كتب أرقام بمسافات فقط → جمع
    if text.replace(" ", "").isdigit():
        numbers = list(map(int, text.split()))
        if len(numbers) >= 2:
            return str(sum(numbers))

    # لو كتب عملية رياضية
    if re.fullmatch(r"[0-9+\-*/. ]+", text):
        try:
            result = safe_calculate(text)
            return str(result)
        except:
            return None

    return None

# =============================
# تنظيف الكلمات
# =============================
def clean_words(text):
    return text.replace("؟","").replace(".","").replace(",","").strip().lower().split()

# =============================
# مطابقة ذكية
# =============================
def smart_match(user_input, memory):
    user_words = set(clean_words(user_input))
    best_score = 0
    best_answer = None

    for item in memory:
        item_words = set(clean_words(item["question"]))
        common = user_words & item_words
        score = len(common) / max(len(user_words), 1)

        if score > best_score:
            best_score = score
            best_answer = item["answer"]

    if best_score > 0.3:
        return best_answer
    return None

# =============================
# الصفحة الرئيسية
# =============================
@app.route("/")
def home():
    return render_template("index.html")

# =============================
# API الدردشة
# =============================
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    memory = load_memory()

    # ===== حل الرياضيات أولاً =====
    math_result = solve_math(user_input)
    if math_result:
        return jsonify({
            "reply": f"{BOT_NAME}: الناتج هو {math_result} 🧮"
        })

    # ===== التعلم اليدوي =====
    if user_input.startswith("تعلم:"):
        try:
            content = user_input.replace("تعلم:", "").strip()
            question, answer = content.split("=")

            memory.append({
                "question": question.strip(),
                "answer": answer.strip()
            })

            save_memory(memory)

            return jsonify({"reply": "🤖 تم التعلم بنجاح ✅"})
        except:
            return jsonify({"reply": "⚠️ الصيغة خاطئة.\nاستخدم:\nتعلم: السؤال = الإجابة"})

    # ===== سؤال الوقت =====
    if "الوقت" in user_input:
        now = datetime.datetime.now().strftime("%H:%M")
        return jsonify({"reply": f"{BOT_NAME}: الوقت الآن هو {now}"})

    # ===== البحث في الذاكرة =====
    answer = smart_match(user_input, memory)

    if answer:
        return jsonify({"reply": f"{BOT_NAME}: {answer}"})

    return jsonify({
        "reply": f"{BOT_NAME}: لا أعرف الإجابة بعد 🤔\nيمكنك تعليمي هكذا:\nتعلم: سؤالك = الإجابة"
    })

# =============================
if __name__ == "__main__":
    app.run(debug=True)
