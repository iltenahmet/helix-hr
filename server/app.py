from typing import List
from flask import Flask, request, jsonify
from flask_cors import CORS
from agent import ask_agent, set_sequence, get_sequence
from socketio_instance import socketio


app = Flask(__name__)
CORS(app, supports_credentials=True)
socketio.init_app(app, cors_allowed_origins="*")


@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    ai_response = ask_agent(user_message)

    # Send this if updated or generated sequence
    socketio.emit("update_sequence", get_sequence())
    print("Updated sequence: ", get_sequence())
    return jsonify({"message": ai_response})


@app.route("/api/sequence", methods=["GET"])
def fetch_sequence():
    return jsonify(get_sequence())

@app.route("/api/sequence", methods=["POST"])
def update_sequence():
    data = request.get_json()

    if isinstance(data, list):
        set_sequence(data)
        return jsonify({"message": "Sequence updated successfully"}), 200
    else:
        return jsonify({"error": "Invalid data format. Expected a list."}), 400 

if __name__ == "__main__":
    socketio.run(app, port=8080, debug=True)
