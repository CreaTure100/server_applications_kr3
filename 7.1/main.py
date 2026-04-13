from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from secrets import compare_digest
from enum import Enum
import jwt

SECRET_KEY = "secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

usersDB = {}

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserRegister(BaseModel):
    username: str
    password: str
    role: UserRole = UserRole.USER

class UserLogin(BaseModel):
    username: str
    password: str

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    role: UserRole

class Token(BaseModel):
    access_token: str
    token_type: str

def get_user_by_username(username: str) -> UserInDB | None:
    if username in usersDB:
        return UserInDB(
            username=username,
            hashed_password=usersDB[username]["hashed_password"],
            role=usersDB[username]["role"]
        )
    return None

def create_user(username: str, password: str, role: UserRole) -> UserInDB:
    hashed = pwd_context.hash(password)
    usersDB[username] = {
        "hashed_password": hashed,
        "role": role
    }
    return UserInDB(username=username, hashed_password=hashed, role=role)

def create_access_token(username: str, role: UserRole) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": username, "role": role, "exp": expire}
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
    role = payload.get("role")
    
    if username is None or role is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def get_current_user_role(current_user: UserInDB = Depends(get_current_user)):
    return current_user.role

def require_admin(role: UserRole = Depends(get_current_user_role)):
    if role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return role

def require_admin_or_user(role: UserRole = Depends(get_current_user_role)):
    if role not in [UserRole.ADMIN, UserRole.USER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin or User role required"
        )
    return role

@app.post("/register", status_code=201)
def register(user: UserRegister):
    if get_user_by_username(user.username) is not None:
        raise HTTPException(status_code=409, detail="User already exists")
    create_user(user.username, user.password, user.role)
    return {"message": "New user created", "role": user.role}

@app.post("/login", response_model=Token)
def login(user: UserLogin):
    db_user = get_user_by_username(user.username)
    
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not compare_digest(user.username, db_user.username):
        raise HTTPException(status_code=401, detail="Authorization failed")
    
    if not pwd_context.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Authorization failed")
    
    access_token = create_access_token(db_user.username, db_user.role)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected_resource")
def protected_resource(current_user: UserInDB = Depends(get_current_user), _ = Depends(require_admin_or_user)):
    return {"message": "Access granted", "user": current_user.username, "role": current_user.role}

@app.post("/admin_resource")
def create_resource(current_user: UserInDB = Depends(get_current_user), _ = Depends(require_admin)):
    return {"message": f"Resource created by admin: {current_user.username}"}

@app.put("/admin_resource/{resource_id}")
def update_resource(resource_id: int, current_user: UserInDB = Depends(get_current_user), _ = Depends(require_admin)):
    return {"message": f"Resource {resource_id} updated by admin: {current_user.username}"}

@app.delete("/admin_resource/{resource_id}")
def delete_resource(resource_id: int, current_user: UserInDB = Depends(get_current_user), _ = Depends(require_admin)):
    return {"message": f"Resource {resource_id} deleted by admin: {current_user.username}"}

@app.get("/user_resource")
def read_user_resource(current_user: UserInDB = Depends(get_current_user), _ = Depends(require_admin_or_user)):
    return {"message": f"Resource read by {current_user.username} (role: {current_user.role})"}

@app.put("/user_resource")
def update_user_resource(current_user: UserInDB = Depends(get_current_user), _ = Depends(require_admin_or_user)):
    return {"message": f"Resource updated by {current_user.username} (role: {current_user.role})"}

@app.get("/guest_resource")
def guest_resource(current_user: UserInDB = Depends(get_current_user)):
    return {
        "message": "Read-only access granted",
        "user": current_user.username,
        "role": current_user.role,
        "data": ["public_info_1", "public_info_2"]
    }

@app.get("/me")
def get_me(current_user: UserInDB = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}

@app.get("/")
def root():
    return {"message": "RBAC API"}
