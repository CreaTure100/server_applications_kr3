from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from secrets import compare_digest

app = FastAPI()
security = HTTPBasic()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

usersDB = {}

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

def get_user_by_username(username: str) -> UserInDB | None:
    if username in usersDB:
        user_data = usersDB[username]
        return UserInDB(username=username, hashed_password=user_data["hashed_password"])
    return None

def create_user(user: User) -> UserInDB:
    hashed = pwd_context.hash(user.password)
    user_in_db = UserInDB(username=user.username, hashed_password=hashed)
    usersDB[user.username] = {"hashed_password": hashed}
    return user_in_db

def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = get_user_by_username(credentials.username)
    
    if (user is None) or (not compare_digest(credentials.username, user.username)) or (not pwd_context.verify(credentials.password, user.hashed_password)):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return user

@app.post("/register")
def register(user: User):
    if get_user_by_username(user.username) is not None:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )
    
    create_user(user)
    return {"message": "User registered successfully"}

@app.get("/login")
def login(user: UserInDB = Depends(auth_user)):
    return {"message": f"Welcome, {user.username}!"}
