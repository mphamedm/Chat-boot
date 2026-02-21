from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import google.generativeai as genai
import os

app = Flask(__name__)
CORS(app)

BOT_NAME = "محسن"

# ضع مفتاح Gemini هنا
genai.configure(api_key="PUT_YOUR_GEMINI_API_KEY_HERE")

model = genai.GenerativeModel("gemini-1.5-flash")

def ask_ai(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "حدث خطأ في الاتصال بالذكاء الاصطناعي"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "اكتب رسالة أولاً"})

    ai_response = ask_ai(user_input)
    return jsonify({"reply": f"{BOT_NAME}: {ai_response}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
