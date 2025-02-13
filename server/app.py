from flask import Flask, request, jsonify, session
from flask_cors import CORS
from agent import ask_agent, set_sequence, get_sequence
from socketio_instance import socketio
from sqlalchemy.orm import sessionmaker
from model import get_db_engine, Base, User, Session, ChatHistory
from dotenv import load_dotenv
from os import getenv
import uuid

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


# Socket.IO event handler for connection
@socketio.on("connect")
def handle_connect():
    # Store the client's session ID in the Flask session
    session["sid"] = request.sid
    print("Client connected:", request.sid)


# Socket.IO event handler for disconnection
@socketio.on("disconnect")
def handle_disconnect():
    print("Client disconnected:", request.sid)


@app.route("/api/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    user_id = session.get("user_id")
    is_guest = session.get("is_guest", False)

    if not user_id and not is_guest:
        session["is_guest"] = True
        is_guest = True
        session["user_id"] = "guest_" + str(uuid.uuid4())  # Temporary guest ID
        user_id = session["user_id"]
    else:
        db = get_db_session()
        user_session = db.query(Session).filter_by(user_id=user_id).first()
        if not user_session:
            user_session = Session(user_id=user_id)
            db.add(user_session)
            db.commit()

    ai_response = ask_agent(user_message, user_id)

    if not is_guest:
        chat_history_user = ChatHistory(session_id=user_session.id, message=user_message)
        chat_history_ai = ChatHistory(session_id=user_session.id, message=ai_response)
        db.add(chat_history_user)
        db.add(chat_history_ai)
        db.commit()
        db.close()

    # Emit the update_sequence event only to the relevant client
    socketio.emit("update_sequence", get_sequence(), room=session.get("sid"))
    return jsonify({"message": ai_response})


@app.route("/api/sequence", methods=["GET"])
def fetch_sequence():
    return jsonify(get_sequence())


@app.route("/api/sequence", methods=["POST"])
def update_sequence():
    data = request.get_json()

    if isinstance(data, list):
        set_sequence(data)
        # Emit the update_sequence event only to the relevant client
        socketio.emit("update_sequence", get_sequence(), room=session.get("sid"))
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

    user = db.query(User).filter_by(username=data["username"]).first()
    session["user_id"] = user.id

    db.close()

    return jsonify({"message": "Sign up successful", "username": user.username}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    db = get_db_session()
    user = db.query(User).filter_by(username=data["username"]).first()

    if user and user.check_password(data["password"]):
        session["user_id"] = user.id
        user_session = db.query(Session).filter_by(user_id=user.id).first()
        if user_session:
            set_sequence(user_session.get_sequence())
        db.close()
        return jsonify({"message": "Login successful", "username": user.username}), 200
    else:
        db.close()
        return jsonify({"error": "Invalid credentials"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    socketio.emit("logout", room=session.get("sid"))
    session.pop("user_id", None)
    session.pop("is_guest", None)
    session.pop("sid", None) 
    return jsonify({"message": "Logout successful"}), 200


@app.route("/check-session", methods=["GET"])
def check_session():
    user_id = session.get("user_id")
    db = get_db_session()
    user = db.query(User).filter_by(id=user_id).first()
    db.close()

    if user:
        return jsonify({"message": "User is logged in", "username": user.username}), 200
    else:
        return jsonify({"error": "User is not logged in"}), 401


if __name__ == "__main__":
    socketio.run(app, port=8080, debug=True)