from Database.db import transactions_collection
from datetime import datetime
import pandas as pd


# ================= ADD TRANSACTION =================
def add_transaction(username, category, tx_type, amount):

    transaction = {
        "username": username,
        "category": category,
        "type": tx_type,  # Deposit / Withdraw / Transfer
        "amount": float(amount),  # ensure numeric
        "date": datetime.now()
    }

    transactions_collection.insert_one(transaction)


# ================= GET ALL USER TRANSACTIONS =================
def get_transactions(username):

    data = list(
        transactions_collection
        .find({"username": username})
        .sort("date", -1)
    )

    if not data:
        return pd.DataFrame()

    for d in data:
        d["_id"] = str(d["_id"])

    return pd.DataFrame(data)


# ================= GET MONTHLY TRANSACTIONS =================
def get_monthly_transactions(username, month, year):

    # Handle December properly
    if month == 12:
        start = datetime(year, 12, 1)
        end = datetime(year + 1, 1, 1)
    else:
        start = datetime(year, month, 1)
        end = datetime(year, month + 1, 1)

    data = list(
        transactions_collection.find({
            "username": username,
            "date": {"$gte": start, "$lt": end}
        }).sort("date", -1)
    )

    if not data:
        return pd.DataFrame()

    for d in data:
        d["_id"] = str(d["_id"])

    return pd.DataFrame(data)