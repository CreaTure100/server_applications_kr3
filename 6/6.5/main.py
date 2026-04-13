from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from secrets import compare_digest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import jwt

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

SECRET_KEY = "secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

usersDB = {}

class UserRegister(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDB(BaseModel):
    username: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def get_user_by_username(username: str) -> UserInDB | None:
    if username in usersDB:
        return UserInDB(username=username, hashed_password=usersDB[username]["hashed_password"])
    return None

def create_user(username: str, password: str) -> UserInDB:
    hashed = pwd_context.hash(password)
    usersDB[username] = {"hashed_password": hashed}
    return UserInDB(username=username, hashed_password=hashed)

def create_access_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_access_token(token)
    username = payload.get("sub")
    
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@app.post("/register", status_code=201)
@limiter.limit("1/minute")
def register(request: Request, user: UserRegister):
    if get_user_by_username(user.username) is not None:
        raise HTTPException(status_code=409, detail="User already exists")
    create_user(user.username, user.password)
    return {"message": "New user created"}

@app.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin):
    db_user = get_user_by_username(user.username)
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not compare_digest(user.username, db_user.username):
        raise HTTPException(status_code=401, detail="Authorization failed")
    
    if not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Authorization failed")
    
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected_resource")
def protected_resource(current_user: UserInDB = Depends(get_current_user)):
    return {"message": "Access granted", "user": current_user.username}

@app.get("/")
def root():
    return {"message": "JWT"}
