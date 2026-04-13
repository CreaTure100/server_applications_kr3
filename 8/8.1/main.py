import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import get_db_connection, init_db

app = FastAPI()

init_db()

class User(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: User):
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (user.username, user.password)
            )
        return {"message": "User registered successfully!"}
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="Username already exists"
        )

@app.get("/")
def root():
    return {"message": "API"}

@app.get("/users")
def get_all_users():
    with get_db_connection() as conn:
        users = conn.execute("SELECT id, username FROM users").fetchall()
        return [dict(user) for user in users]
