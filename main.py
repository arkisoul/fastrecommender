from fastapi import FastAPI, Header, HTTPException
from typing import Annotated, Optional
from sqlmodel import SQLModel, Field, create_engine, Session, update

app = FastAPI()

DATABASE_URL = 'postgresql://appuser:appuser@localhost/fastapi'

engine = create_engine(DATABASE_URL)

class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    city: str
    email: str

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/hello") # http://localhost:8000/hello GET
def index():
    return { "message": "Hello World" }

@app.get("/test") # http://localhost:8000/test GET
def test():
    a = 10
    b = 20
    c = a + b
    return { "message": "Test API", "total": c }

@app.get("/users", status_code=200)
def get_users(x_api_key: Annotated[str | None, Header()] = None, city: str = None):
    with Session(engine) as session:
        users = session.query(Users).all()
        print(f'users list {users}')
        return { "message": "Users list", "data": users, "header": x_api_key }

@app.get("/users/{user_id}") # GET baseUrl/users/1
def get_user_by_id(user_id: int):
    with Session(engine) as session:
        user = session.query(Users).filter(Users.id == user_id).one_or_none()
        return { "message": "User detail", "data": user }

@app.post("/users", status_code=201)
def create_user(user: Users):
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return { "message": "New user", "data": user }

@app.put("/users/{user_id}")
def update_user(user_id: int, user: Users):
    with Session(engine) as session:
        user_exist = session.query(Users).filter(Users.id == user_id).one_or_none()
        if not user_exist:
            raise HTTPException(404, 'Invalid user id')
        
        user_exist.name = user.name
        user_exist.city = user.city
        user_exist.email = user.email
        session.add(user_exist)
        session.commit()
        session.refresh(user_exist)
        return { "message": "User updated successfully", "data": user_exist }

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    with Session(engine) as session:
        user_exist = session.query(Users).filter(Users.id == user_id).one_or_none()
        if not user_exist:
            raise HTTPException(404, 'Invalid user id')
        
        session.delete(user_exist)
        session.commit()
        return { "message": "User deleted successfully", "data": user_exist }