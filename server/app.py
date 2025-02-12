from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from agent import ask_agent


app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")


# Sample structured sequence data (now directly an array)
sequence_data = [
    {"id": 1, "text": "Hi {{first_name}}"},
    {"id": 2, "text": "this is seconds part"},
    {"id": 3, "text": "this is third part"},
]

@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    ai_response = ask_agent(user_message)

    # Send this if updated or generated sequence
    sequence_data.append({"id": len(sequence_data) + 1, "text": ai_response})
    socketio.emit("update_sequence", sequence_data)  # Send sequence update to frontend
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
    socketio.run(app, port=8080, debug=True)
