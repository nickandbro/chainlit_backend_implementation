# app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.dialects.postgresql import JSONB  # If you're using PostgreSQL
from sqlalchemy import desc 
import time
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = 'app_user'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    createdAt = Column(DateTime(timezone=True), default=func.now())  # Already in the desired format
    role = Column(String(50), nullable=False, default='USER')
    image = Column(String(255), nullable=True)
    provider = Column(String(50), nullable=True)
    tags = Column(JSONB, default=list, nullable=False)
    conversations = relationship("Conversation", back_populates="appUser")




class Message(Base):
    __tablename__ = 'message'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)  # Changed to UUID
    content = Column(String, nullable=False)
    createdAt = Column(DateTime(timezone=True), default=func.now())  # Already in the desired format
    isError = Column(Boolean, default=False)
    author = Column(String, nullable=True)  # Assuming author is a string
    language = Column(String, nullable=True)  # Assuming language is a string
    prompt = Column(JSONB, nullable=True)  # Assuming prompt is a JSON structure
    parentId = Column(UUID(as_uuid=True), ForeignKey('message.id'), nullable=True)
    indent = Column(Integer, default=0)
    authorIsUser = Column(Boolean, default=False)
    disableHumanFeedback = Column(Boolean, default=False)
    waitForAnswer = Column(Boolean, default=False)
    conversation_id = Column(Integer, ForeignKey('conversation.id'))  # Add this line
    conversation = relationship("Conversation", back_populates="messages")  # Add this line
    humanFeedback = Column(Integer, nullable=True)  # Assuming feedback is an integer score
    humanFeedbackComment = Column(String, nullable=True)  # Feedback comment as a string
    disableHumanFeedback = Column(Boolean, default=False)

class Conversation(Base):
    __tablename__ = 'conversation'
    messages = relationship("Message", back_populates="conversation")
    id = Column(Integer, primary_key=True)
    createdAt = Column(DateTime(timezone=True), default=func.now())  # Store as DateTime
    isError = Column(Boolean, default=False)
    appUserId = Column(Integer, ForeignKey('app_user.id'))
    tags = Column(JSONB, default=list, nullable=False)
    # Relationship with User
    appUser = relationship("User", back_populates="conversations")
    # Add a back_populates in User model for conversation