from Database.db import users_collection
from Database.db import login_logs_collection
from datetime import datetime
import bcrypt


# ================= REGISTER USER =================
def register_user(username, password, full_name):

    # 🔒 Check if username already exists
    if user_exists(username):
        return False

    # 🔐 Hash password (convert to string before storing)
    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = {
        "username": username,
        "password": hashed_pw,
        "full_name": full_name,
        "balance": 5000,
        "created_at": datetime.now()
    }

    users_collection.insert_one(user)
    return True


# ================= AUTHENTICATE USER =================
def authenticate_user(username, password):

    user = users_collection.find_one({"username": username})

    if user:
        stored_password = user["password"].encode()

        if bcrypt.checkpw(password.encode(), stored_password):

            login_logs_collection.insert_one({
                "username": username,
                "login_time": datetime.now(),
                "status": "SUCCESS"
            })

            return user

    # ❌ Failed login log
    login_logs_collection.insert_one({
        "username": username,
        "login_time": datetime.now(),
        "status": "FAILED"
    })

    return None


# ================= GET USER =================
def get_user(username):
    return users_collection.find_one({"username": username})


# ================= UPDATE BALANCE =================
def update_balance(username, new_balance):
    users_collection.update_one(
        {"username": username},
        {"$set": {"balance": new_balance}}
    )


# ================= CHECK USER EXISTS =================
def user_exists(username):
    return users_collection.find_one({"username": username}) is not None