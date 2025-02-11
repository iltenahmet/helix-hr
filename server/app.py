from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": r"http://localhost:*"}})

# Sample structured sequence data (now directly an array)
sequence_data = [
    {"id": 1, "text": "Hi {{first_name}}"},
    {"id": 2, "text": "this is seconds part"},
    {"id": 3, "text": "this is third part"},
]

@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    # Mock AI response (replace with LLM call)
    ai_response = f"AI: You said '{user_message}'."
    return jsonify({"message": ai_response})

@app.route("/api/sequence", methods=["GET"])
def get_sequence():
    return jsonify(sequence_data)

@app.route("/api/sequence", methods=["POST"])
def update_sequence():
    global sequence_data
    data = request.get_json()

    print("Received data:", data)  # Debugging output

    # Ensure data is a list before replacing the existing sequence
    if isinstance(data, list):
        sequence_data = data  # Store the new sequence directly
        print("Updated sequence:", sequence_data)  # Debugging output
        return jsonify({"message": "Sequence updated successfully"}), 200
    else:
        return jsonify({"error": "Invalid data format. Expected a list."}), 400  # Error handling

if __name__ == "__main__":
    app.run(debug=True)
