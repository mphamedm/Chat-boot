from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json, os, re, ast, operator as op
from difflib import SequenceMatcher
from duckduckgo_search import DDGS

app = Flask(__name__)
CORS(app)

BOT_NAME = "محسن"
brain_file = "brain.json"

# ============================
# تحميل وحفظ البيانات
# ============================
def load_memory():
    if not os.path.exists(brain_file):
        return []
    with open(brain_file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory(data):
    with open(brain_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ============================
# آلة حاسبة آمنة
# ============================
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv}

def safe_calculate(expr):
    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return operators[type(node.op)](eval_node(node.left), eval_node(node.right))
        else:
            raise TypeError("عملية غير مسموحة")
    node = ast.parse(expr, mode='eval').body
    return eval_node(node)

def solve_math(text):
    text = text.strip().replace("×", "*").replace("÷", "/")
    if re.fullmatch(r"[0-9+\-*/. ]+", text):
        try:
            result = safe_calculate(text)
            return str(result)
        except:
            return None
    return None

# ============================
# تحسين فهم نص السؤال
# ============================
def normalize_text(text):
    text = text.lower()
    text = text.replace("؟", "").replace(".", "").replace(",", "")
    text = text.replace("ما هو", "").replace("من هو", "").replace("ما", "").strip()
    return text

def text_similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def smart_match(user_input, memory):
    user_norm = normalize_text(user_input)
    best_score = 0
    best_answer = None
    for item in memory:
        question_norm = normalize_text(item["question"])
        score = text_similarity(user_norm, question_norm)
        if score > best_score:
            best_score = score
            best_answer = item["answer"]
    if best_score > 0.6:
        return best_answer
    return None

# ============================
# البحث في الإنترنت
# ============================
def search_web(query):
    try:
        with DDGS() as ddgs:
            results = ddgs.text(query, max_results=1)
            for r in results:
                # تنظيف وتقصير النتيجة
                answer = r["body"]
                answer = re.sub(r'\s+', ' ', answer)
                return answer[:500]  # حفظ أول 500 حرف فقط
    except:
        return None
    return None

# ============================
# الصفحة الرئيسية
# ============================
@app.route("/")
def home():
    return render_template("index.html")

# ============================
# API الدردشة
# ============================
@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    memory = load_memory()

    # ===== حل المسائل الحسابية =====
    math_result = solve_math(user_input)
    if math_result:
        return jsonify({"reply": f"{BOT_NAME}: الناتج هو {math_result} 🧮"})

    # ===== البحث في الذاكرة =====
    answer = smart_match(user_input, memory)
    if answer:
        return jsonify({"reply": f"{BOT_NAME}: {answer}"})

    # ===== البحث في الإنترنت =====
    web_result = search_web(user_input)

    if web_result:
        # منع التكرار
        exists = any(normalize_text(user_input) == normalize_text(item["question"]) for item in memory)
        if not exists:
            memory.append({
                "question": user_input,
                "answer": web_result
            })
            save_memory(memory)

        return jsonify({
            "reply": f"{BOT_NAME}: 🌐 وجدت هذه المعلومات:\n\n{web_result}"
        })

    # ===== لو لم يجد =====
    return jsonify({
        "reply": f"{BOT_NAME}: لا أعرف الإجابة بعد 🤔\nما هي الإجابة الصحيحة؟",
        "learn": True
    })

# ============================
# API التعلم اليدوي
# ============================
@app.route("/learn", methods=["POST"])
def learn():
    question = request.json.get("question", "").strip()
    answer = request.json.get("answer", "").strip()
    memory = load_memory()

    if question and answer:
        memory.append({"question": question, "answer": answer})
        save_memory(memory)
        return jsonify({"reply": "🤖 تم التعلم بنجاح ✅"})
    else:
        return jsonify({"reply": "⚠️ يجب كتابة السؤال والإجابة"})

if __name__ == "__main__":
    app.run(debug=True)
