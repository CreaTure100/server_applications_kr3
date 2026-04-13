from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from secrets import compare_digest

app = FastAPI()
security = HTTPBasic()

users = {
    "user": "123"
}

def auth_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_password = users.get(credentials.username)
    
    if (correct_password is None) or (not compare_digest(credentials.password, correct_password)):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    
    return credentials.username

@app.get("/secret")
def get_secret(username: str = Depends(auth_user)):
    return {"message": "You got my secret, welcome"}
