from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.security import generate_password_hash, check_password_hash
import json

Base = declarative_base()

def get_db_engine():
    return create_engine("sqlite:///database.db", echo=True)

class BaseModel(Base):
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

class User(BaseModel):
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    company = Column(String)
    phone_number = Column(String)

    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Session(BaseModel):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    sequence = Column(Text)  # Stored as JSON string

    user = relationship("User", back_populates="sessions")
    chat_history = relationship("ChatHistory", back_populates="session", cascade="all, delete-orphan")

    def set_sequence(self, sequence_list):
        self.sequence = json.dumps(sequence_list)

    def get_sequence(self):
        if self.sequence is None:
            return []
        return json.loads(self.sequence)

class ChatHistory(BaseModel):
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('session.id'), nullable=False)
    message = Column(Text, nullable=False)

    session = relationship("Session", back_populates="chat_history")

if __name__ == "__main__":
    engine = get_db_engine()
    Base.metadata.create_all(engine)
