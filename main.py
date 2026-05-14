from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session, select
from typing import List, Optional
from pydantic import EmailStr
import datetime as dt
from fastapi.middleware.cors import CORSMiddleware
import json

# tables de données

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True)
    email: EmailStr = Field(unique=True)
    sent_messages: List["Message"] = Relationship( back_populates="sender",sa_relationship_kwargs={"foreign_keys": "Message.sender_id"})
    received_messages: List["Message"] = Relationship(back_populates="receiver",sa_relationship_kwargs={"foreign_keys": "Message.receiver_id"})

class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    subject: str | None = Field(default="Chat")
    content: str
    is_read: bool = Field(default=False)
    created_at: dt.datetime = Field(default_factory=dt.datetime.now)    
    sender_id: int = Field(foreign_key="user.id")
    sender: User = Relationship(back_populates="sent_messages",sa_relationship_kwargs={"foreign_keys": "[Message.sender_id]"})
    receiver_id: int | None = Field(default=None, foreign_key="user.id")
    receiver: User | None = Relationship(back_populates="received_messages",sa_relationship_kwargs={"foreign_keys": "[Message.receiver_id]"})

# Pydantic models

class UserCreate(SQLModel):
    username: str
    email: str

class UserRead(SQLModel):
    id: int
    username: str
    email: str

class MessageCreate(SQLModel):
    receiver_id: int
    sender_id: int
    subject: str
    content: str

class MessageRead(SQLModel):
    id: int
    subject: str
    content: str
    is_read: bool
    sender_id: int
    receiver_id: Optional[int]

# configuration

database_url = "sqlite:///./messenger.db"
engine = create_engine(database_url, echo=True, connect_args={"check_same_thread": False})
SQLModel.metadata.create_all(engine) # initialisation auto de la base au démarrage

app = FastAPI(title="Messenger API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        await self.broadcast_user_list()

    async def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
            await self.broadcast_user_list()

    async def broadcast_user_list(self):
        user_list = list(self.active_connections.keys())
        payload = {
            "action": "userlist",
            "users": user_list,
            "time": dt.datetime.now().strftime("%H:%M")
        }
        for connection in self.active_connections.values():
            try:
                await connection.send_json(payload)
            except:
                pass

    async def send_personal_message(self, message: dict, recipient: str):
        if recipient in self.active_connections:
            await self.active_connections[recipient].send_json(message)

manager = ConnectionManager()

# routes user et message

@app.post("/users", response_model=UserRead)
def create_user(user_in: UserCreate):
    with Session(engine) as session:
        db_user = User.from_orm(user_in)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

@app.get("/users", response_model=List[UserRead])
def list_users():
    with Session(engine) as session:
        return session.exec(select(User)).all()

@app.get("/users/{user_id}", response_model=UserRead)
def get_user_by_id(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

@app.post("/messages", response_model=MessageRead)
def send_message(msg_in: MessageCreate):
    with Session(engine) as session:
        # on vérifie si l'expéditeur et le destinataire existent
        sender = session.get(User, msg_in.sender_id)
        receiver = session.get(User, msg_in.receiver_id)
        if not sender or not receiver:
            raise HTTPException(status_code=404, detail="Sender or Receiver not found")
        # on vérifie qu'on ne s'envoie pas un message à soi-même
        if msg_in.sender_id == msg_in.receiver_id:
            raise HTTPException(status_code=400, detail="You cannot send a message to yourself")
        # on vérifie que le sujet et le corps ne sont pas vides
        if not msg_in.subject.strip() or not msg_in.content.strip():
            raise HTTPException(status_code=400, detail="Subject and content cannot be empty")
        new_msg = Message.from_orm(msg_in)
        session.add(new_msg)
        session.commit()
        session.refresh(new_msg)
        return new_msg

# consulter la boîte de réception 
@app.get("/users/{user_id}/inbox", response_model=List[MessageRead])
def get_inbox(
    user_id: int, 
    unread_only: bool = Query(False), # Filtrer les non lus
    search: str | None = Query(None)  # Recherche par mot-clé
    ):
    with Session(engine) as session:
        statement = select(Message).where(Message.receiver_id == user_id)
        if unread_only:
            statement = statement.where(Message.is_read == False)
        if search:
            statement = statement.where(Message.subject.contains(search))  
        return session.exec(statement).all()

#  consulter les messages envoyés
@app.get("/users/{user_id}/sent", response_model=List[MessageRead])
def get_sent(user_id: int):
    with Session(engine) as session:
        statement = select(Message).where(Message.sender_id == user_id)
        return session.exec(statement).all()

# consulter le détail d’un message
@app.get("/messages/{message_id}", response_model=MessageRead)
def get_message_detail(message_id: int):
    with Session(engine) as session:
        message = session.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        return message

# marquer un message comme lu
@app.patch("/messages/{message_id}/read", response_model=MessageRead)
def mark_as_read(message_id: int):
    with Session(engine) as session:
        message = session.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        message.is_read = True
        session.add(message)
        session.commit()
        session.refresh(message)
        return message

# websocket
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_json()
            if data["action"] == "sendmessage":
                payload = {
                    "action": "message",
                    "sender": username,
                    "subject": data.get("subject", "Chat"),
                    "message": data["message"],
                    "time": dt.datetime.now().strftime("%H:%M")
                }
                await manager.send_personal_message(payload, data["recipient"])
    except WebSocketDisconnect:
        await manager.disconnect(username)
    except Exception:
        await manager.disconnect(username)