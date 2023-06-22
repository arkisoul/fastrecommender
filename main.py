from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

users = {
    1: {
        "id": 1,
        "name": "John Doe",
        "city": "Ahmedabad",
        "email": "john.doe@mailinator.com"
    },
    2: {
        "id": 2,
        "name": "Jane Doe",
        "city": "Gandhinagar",
        "email": "jane.doe@mailinator.com"
    },
    3: {
        "id": 3,
        "name": "Jack Doe",
        "city": "Baroda",
        "email": "jack.doe@mailinator.com"
    }
}

class User(BaseModel):
    id: int
    name: str
    city: str
    email: str

@app.get("/hello") # http://localhost:8000/hello GET
def index():
    return { "message": "Hello World" }

@app.get("/test") # http://localhost:8000/test GET
def test():
    a = 10
    b = 20
    c = a + b
    return { "message": "Test API", "total": c }

@app.get("/users")
def get_users(city: str = None):
    if city is None:
        return { "message": "Users list", "data": list(users.values()) }
    
    filtered_users = [user for user in users.values() if user.get('city').lower() == city.lower()]
    return { "message": "Users list", "data": filtered_users }

@app.get("/users/{user_id}") # GET baseUrl/users/1
def get_user_by_id(user_id: int):
    return { "message": "User detail", "data": users[user_id] }

@app.post("/users")
def create_user(user: User):
    return { "message": "New user", "data": user }
