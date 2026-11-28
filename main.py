from fastapi import FastAPI
from database.init_db import supabase
from catalog.Classes import router as course_route
from graph.router import router as graph_route
from userData.user_endpoint_supa import router as users_route
from userData.user_courses_endpoint_supa import router as usersHistory_route
from userData.terms import router as terms_route
from auth.authenticate import router as auth_route

app = FastAPI()

app.include_router(course_route)
app.include_router(graph_route)
app.include_router(users_route)
app.include_router(usersHistory_route)
app.include_router(terms_route)
app.include_router(auth_route)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


# tests db connection
@app.get("/db-health")
def check_db():
    try:
        response = supabase.table("courses").select("*").limit(1).execute()
        if response:
            return {"status": "OK", "response": "recieved"}
        # if there is no exception we should always recieve a response
        return {"status": "OK", "response": "not recieved"}
    except Exception as e:
        return {"message": f"Supabase health check failed: {e}"}
