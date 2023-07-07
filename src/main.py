from fastapi import FastAPI, Header, HTTPException
from typing import Annotated, Optional
from sqlmodel import SQLModel, Field, create_engine, Session, update
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import warnings
warnings.filterwarnings('ignore')

app = FastAPI()

# postgresql://<username>:<password>@localhost/<databasename>
# create user username with encrypted password 'password'
DATABASE_URL = 'postgresql://fastdev:fastdev@pgsql/fastapi'

engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    city: str
    email: str

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/hello") # http://localhost:8000/hello GET
def index():
    return { "message": "Hello World from Docker Container" }

@app.get("/test") # http://localhost:8000/test GET
def test():
    a = 10
    b = 20
    c = a + b
    return { "message": "Test API", "total": c }

@app.get("/users", status_code=200)
def get_users(x_api_key: Annotated[str | None, Header()] = None, city: str = None):
    with Session(engine) as session:
        users = session.query(Users).all() # select * from users
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

movie=pd.read_csv(r"./src/ratings.csv")
movie.head()
movie=movie.drop('timestamp',axis=1)

movie_ratings=pd.DataFrame()
movie_ratings['movieId']=movie['movieId']
movie_ratings['rating']=movie['rating']

user_ratings=pd.DataFrame()
user_ratings['userId']=movie['userId']
user_ratings['rating']=movie['rating']

count_ratings_users=pd.DataFrame(user_ratings.groupby('userId',as_index=False).count())
count_ratings_users=count_ratings_users.sort_values(by='rating',ascending=False)
count_ratings_users.rename(columns = {'rating':'Count'}, inplace = True)
count_ratings_users=count_ratings_users[count_ratings_users['Count']>=5]

df0=count_ratings_users.merge(movie,on='userId',how='inner')

count_ratings_movie=pd.DataFrame(movie_ratings.groupby('movieId',as_index=False).count())
count_ratings_movie=count_ratings_movie.sort_values(by='rating',ascending=False)
count_ratings_movie.rename(columns = {'rating':'Count'}, inplace = True)
count_ratings_movie=count_ratings_movie[count_ratings_movie['Count']>=75]
movie=count_ratings_movie.merge(df0,on='movieId', how='inner')
movie=movie.drop(columns=['Count_x','Count_y'],axis=1)

movie['movieId']=movie['movieId'].rank(method='dense').astype(int)
movie['userId']=movie['userId'].rank(method='dense').astype(int)

user_item_matrix=movie.pivot_table(index='movieId',columns='userId',values='rating')
user_item_matrix.dropna(axis=1,how='all',inplace=True)
user_item_matrix_norm=user_item_matrix.apply(lambda x: x - np.nanmean(x),axis=1)
user_item_matrix_norm.fillna(0,inplace=True)
item_similarity=user_item_matrix_norm.T.corr()
def predict_rating(userId, movieId, max_neighbor=2): 
    movies = item_similarity.sort_values(by=movieId, ascending=False).index[1:]
    scores = item_similarity.sort_values(by=movieId, ascending=False).loc[:, movieId].tolist()[1:]
    movies_arr = np.array([x for x in movies])
    sim_arr = np.array([x for x in scores])
    # select only the movie that has already rated by given user
    filtering = user_item_matrix_norm[userId].loc[movies_arr] != 0
    # calculate the predicted score
    s = np.dot(sim_arr[filtering][:max_neighbor], user_item_matrix_norm[userId].loc[movies_arr[filtering][:max_neighbor]])/ np.sum(sim_arr[filtering][:max_neighbor])
    return s

# Define a route for prediction
@app.get('/predict/{userId}')
def get_recommendation(userId: int, n: int = 5):
    predicted_rating = np.array([])
    for movie_ in user_item_matrix_norm.index:
        predicted_rating = np.append(predicted_rating, predict_rating(userId, movie_))
    # don't recommend something that user has already rated
    temp = pd.DataFrame({'predicted_rating':predicted_rating, 'movie':user_item_matrix_norm.index})
    filtering = (user_item_matrix_norm[userId] == 0.0)
    temp = temp.loc[filtering.values].sort_values(by='predicted_rating', ascending=False)
    # recommend n movies to user
    return temp.movie[:n].tolist()