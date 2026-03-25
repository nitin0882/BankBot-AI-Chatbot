from pymongo import MongoClient

# Local MongoDB connection (NO cluster)
client = MongoClient("mongodb://localhost:27017")

db = client["neobank"]

# Collections
users_collection = db["users"]
transactions_collection = db["transactions"]
chat_collection = db["chat_history"]
cards_collection = db["cards"]
login_logs_collection = db["login_logs"]