
import csv
import os
import hashlib
import uuid

class AuthSystem:
    def __init__(self, user_file="data/users.csv"):
        self.user_file = user_file
        os.makedirs(os.path.dirname(user_file) if os.path.dirname(user_file) else ".", exist_ok=True)

        if not os.path.exists(self.user_file):
            with open(self.user_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["username", "password_hash", "session_token"])

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def signup(self, username, password):
        users = self._load_users()

        if username in users:
            return "❌ Username already exists!"

        password_hash = self.hash_password(password)
        session_token = str(uuid.uuid4())

        with open(self.user_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([username, password_hash, session_token])

        return f"✅ User '{username}' created successfully!"

    def login(self, username, password):
        users = self._load_users()
        if username not in users:
            return None, "❌ User not found."

        password_hash = self.hash_password(password)
        if users[username]["password_hash"] != password_hash:
            return None, "❌ Incorrect password."

        new_token = str(uuid.uuid4())
        self._update_session(username, new_token)
        return new_token, "✅ Login successful!"

    def verify_session(self, token):
        users = self._load_users()
        for user, data in users.items():
            if data["session_token"] == token:
                return user
        return None

    def _load_users(self):
        users = {}
        if not os.path.exists(self.user_file):
            return users

        with open(self.user_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                users[row["username"]] = {
                    "password_hash": row["password_hash"],
                    "session_token": row["session_token"],
                }
        return users

    def _update_session(self, username, new_token):
        rows = []
        with open(self.user_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                if row[0] == username:
                    row[2] = new_token
                rows.append(row)

        with open(self.user_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
