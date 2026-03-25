from Database.db import chat_collection
from datetime import datetime

def save_chat(username, role, message):
    chat_collection.insert_one({
        "username": username,
        "role": role,
        "message": message,
        "timestamp": datetime.now()
    })


def get_chat_history(username):
    return list(chat_collection.find({"username": username}))


def clear_chat(username):
    chat_collection.delete_many({"username": username})

def delete_chat_session(username):
    chat_collection.delete_many({"username": username})