from Database.db import cards_collection


def create_cards(username):
    cards_collection.insert_one({
        "username": username,
        "debit": {
            "active": True,
            "number": "4532 •••• •••• 8892",
            "expiry": "12/28"
        },
        "credit": {
            "active": True,
            "number": "5241 •••• •••• 1104",
            "expiry": "05/29"
        }
    })


def get_cards(username):
    return cards_collection.find_one({"username": username})


def toggle_card(username, card_type):
    user_cards = cards_collection.find_one({"username": username})
    current_status = user_cards[card_type]["active"]

    cards_collection.update_one(
        {"username": username},
        {"$set": {f"{card_type}.active": not current_status}}
    )