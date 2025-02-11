from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Placeholder data
sequence_data = {"sequence": "Sample AI-generated outreach sequence."}

@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    # Mock AI response (replace with LLM call)
    ai_response = f"AI: You said '{user_message}'."
    return jsonify({"message": ai_response})

@app.route("/api/sequence", methods=["GET", "POST"])
def sequence():
    global sequence_data
    if request.method == "POST":
        sequence_data["sequence"] = request.json.get("sequence", "")
    return jsonify(sequence_data)

if __name__ == "__main__":
    app.run(debug=True)
