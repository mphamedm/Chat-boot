from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json, os, math, random, datetime

app = Flask(__name__)
CORS(app)

BOT_NAME = "محسن"
STOP_WORDS = ["ما","هو","هي","في","من","على","عن","الى","هل","كم","ماذا"]

def clean_text(text):
    text = text.replace("؟","").replace(".","").lower()
    words = text.split()
    return [w for w in words if w not in STOP_WORDS]

def text_to_vector(words):
    vec = {}
    for w in words:
        vec[w] = vec.get(w, 0) + 1
    return vec

def cosine_similarity(v1, v2):
    intersection = set(v1.keys()) & set(v2.keys())
    numerator = sum(v1[x] * v2[x] for x in intersection)
    sum1 = sum(v**2 for v in v1.values())
    sum2 = sum(v**2 for v in v2.values())
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if denominator == 0:
        return 0
    return numerator / denominator

def load_memory():
    if not os.path.exists("brain.json"):
        return []
    with open("brain.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    memory = load_memory()

    if "الوقت" in user_input:
        now = datetime.datetime.now().strftime("%H:%M")
        return jsonify({"reply": f"{BOT_NAME}: الوقت الآن هو {now}"})

    question_vec = text_to_vector(clean_text(user_input))
    best_score = 0
    best_answer = None

    for item in memory:
        stored_vec = text_to_vector(clean_text(item["question"]))
        score = cosine_similarity(question_vec, stored_vec)
        if score > best_score:
            best_score = score
            best_answer = item["answer"]

    if best_score > 0.4:
        reply = f"{BOT_NAME}: {best_answer}"
    else:
        reply = f"{BOT_NAME}: لا أعرف الإجابة بعد."

    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run()