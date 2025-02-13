from flask import Flask, request, jsonify, session
from flask_cors import CORS
from agent import ask_agent, set_sequence, get_sequence
from socketio_instance import socketio
from sqlalchemy.orm import sessionmaker
from model import get_db_engine, Base, User
from dotenv import load_dotenv
from os import getenv

load_dotenv()
app = Flask(__name__)
app.secret_key = getenv("SECRET_KEY")
CORS(app, supports_credentials=True)
socketio.init_app(app, cors_allowed_origins="*")

engine = get_db_engine()
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def get_db_session():
    return SessionLocal()


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


@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    db = get_db_session()

    if db.query(User).filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400

    user = User(
        username=data["username"],
        company=data.get("company"),
        phone_number=data.get("phone_number"),
    )
    user.set_password(data["password"])

    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    return jsonify({
            "message": "Sign up successful",
            "username": user.username 
        }), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    db = get_db_session()
    user = db.query(User).filter_by(username=data["username"]).first()

    if user and user.check_password(data["password"]):
        session["user_id"] = user.id
        db.close()
        return jsonify({
            "message": "Login successful",
            "username": user.username 
        }), 200
    else:
        db.close()
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logout successful"}), 200


if __name__ == "__main__":
    socketio.run(app, port=8080, debug=True)
