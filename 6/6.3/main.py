from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from passlib.context import CryptContext
from secrets import compare_digest
from dotenv import load_dotenv
import os

load_dotenv()

MODE = os.getenv("MODE", "DEV")
DOCS_USER = os.getenv("DOCS_USER", "user")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "123")

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

def verify_docs_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if MODE != "DEV":
        raise HTTPException(status_code=404, detail="Not Found")
    
    username_valid = compare_digest(credentials.username, DOCS_USER)
    password_valid = compare_digest(credentials.password, DOCS_PASSWORD)
    
    if not (username_valid and password_valid):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

if MODE == "PROD":
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        title="My API",
        version="1.0.0"
    )
else:
    app = FastAPI(
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
        title="My API",
        version="1.0.0"
    )
    
    @app.get("/docs", include_in_schema=False)
    async def get_docs(auth: str = Depends(verify_docs_auth)):
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title="API Documentation",
        )
    
    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi_json(auth: str = Depends(verify_docs_auth)):
        return get_openapi(
            title="My API",
            version="1.0.0",
            routes=app.routes,
        )

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

@app.get("/")
def root():
    return {"mode": MODE, "docs_available": MODE == "DEV"}
