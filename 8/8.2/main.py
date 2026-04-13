import sqlite3
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from database import get_db_connection, init_db

app = FastAPI()

init_db()

class TodoCreate(BaseModel):
    title: str
    description: str

class TodoUpdate(BaseModel):
    title: str
    description: str
    completed: bool

class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

@app.post("/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(todo: TodoCreate):
    with get_db_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO todos (title, description, completed) VALUES (?, ?, 0)",
            (todo.title, todo.description)
        )
        todo_id = cursor.lastrowid
        
        new_todo = conn.execute(
            "SELECT id, title, description, completed FROM todos WHERE id = ?",
            (todo_id,)
        ).fetchone()
        
    return dict(new_todo)

@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int):
    with get_db_connection() as conn:
        todo = conn.execute(
            "SELECT id, title, description, completed FROM todos WHERE id = ?",
            (todo_id,)
        ).fetchone()
        
    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    
    return dict(todo)

@app.get("/todos", response_model=List[TodoResponse])
def get_all_todos():
    with get_db_connection() as conn:
        todos = conn.execute(
            "SELECT id, title, description, completed FROM todos ORDER BY id"
        ).fetchall()
    
    return [dict(todo) for todo in todos]

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo: TodoUpdate):
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM todos WHERE id = ?",
            (todo_id,)
        ).fetchone()
        
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo with id {todo_id} not found"
            )
        
        conn.execute(
            "UPDATE todos SET title = ?, description = ?, completed = ? WHERE id = ?",
            (todo.title, todo.description, todo.completed, todo_id)
        )
        
        updated_todo = conn.execute(
            "SELECT id, title, description, completed FROM todos WHERE id = ?",
            (todo_id,)
        ).fetchone()
        
    return dict(updated_todo)

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM todos WHERE id = ?",
            (todo_id,)
        ).fetchone()
        
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Todo with id {todo_id} not found"
            )
        
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        
    return {"message": f"Todo with id {todo_id} deleted successfully"}

@app.get("/")
def root():
    return {"message": "Todo CRUD API is running"}
