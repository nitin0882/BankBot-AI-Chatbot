from Database.db import login_logs_collection


def get_login_logs(username):
    return list(login_logs_collection.find({"username": username}))


def get_all_logs():
    return list(login_logs_collection.find({}))