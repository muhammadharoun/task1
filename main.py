from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import List, Dict
import random
import string
import jwt
from datetime import datetime, timedelta

app = FastAPI()

# In-memory database to store posts
database = []
users = {}


class User(BaseModel):
    email: str
    password: str


class Post(BaseModel):
    text: str


class Token(BaseModel):
    access_token: str
    token_type: str


SECRET_KEY = "your_secret_key"  # Replace this with a long, random string in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@app.post("/signup", response_model=Token)
async def signup(user: User):
    if user.email in users:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    token_data = {"sub": user.email}
    access_token = create_access_token(token_data)
    users[user.email] = {"password": user.password, "token": access_token}
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/login", response_model=Token)
async def login(user: User):
    if user.email not in users or users[user.email]["password"] != user.password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token_data = {"sub": user.email}
    access_token = create_access_token(token_data)
    users[user.email]["token"] = access_token  # Update the token for existing users
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/addPost", response_model=Dict[str, str])
async def add_post(post: Post, token: str = Depends(decode_token)):
    post_id = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    database.append({"post_id": post_id, "text": post.text, "user": token["sub"]})
    return {"postID": post_id}


@app.get("/getPosts", response_model=List[Dict[str, str]])
async def get_posts(token: str = Depends(decode_token)):
    user_posts = [{"post_id": post["post_id"], "text": post["text"]} for post in database if post["user"] == token["sub"]]
    return user_posts