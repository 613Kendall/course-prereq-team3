from fastapi import HTTPException, APIRouter
from database.init_db import supabase
from database.types import User, student_profile

#moc data
import json

#uses fast api
router = APIRouter()

moc_data = "userData/moc_user.json"

def load_data() -> dict:

    try:

        with open(moc_data, "r", encoding ="utf-8") as file:

            return json.load(file)

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="moc_user.json not found")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Invalid JSON format: {e}")


#should only need to be used by admin to see all users
@router.get("/users")
def get_users():


    try:
    
        data = load_data()
        all_users = data.get("users", [])
        all_profiles = data.get("student_profiles", [])
        valid_users = []

        for user in all_users:

            user = user.copy()

            if user.get("role") is None:

                user["role"] = "student"

            match = None
            for profile in all_profiles:

                if profile.get("user_id") == user.get("user_id"):

                    match = profile.copy()

                    break




            try:

                valid_user = User(**user)

                if match:

                    if match.get("student_type") is None:

                        match["student_type"] = "student"

                    valid_profile = student_profile(**match)

                else:

                    valid_profile = None

                valid_users.append({"user": valid_user, "student_profile": valid_profile})

            except Exception as e:

                print(f"Course {user.get("user_id")} still has invalid data: {e}")



        return valid_users

    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e






@router.get("/users/{user_id}")
def get_user(user_id: int):



    try:
    
        data = load_data()
        all_users = data.get("users", [])
        all_profiles = data.get("student_profiles", [])

        match = None
        for user in all_users:

            if user.get("user_id") == user_id:

                match = user.copy()

                break

        if not match:

            raise HTTPException(status_code=404, detail= f"User with ID {user_id} does not exist")

        if match.get("role") is None:

            match["role"] = "student"


        match_profile = None

        for profile in all_profiles:

            if profile.get("user_id") == user_id:

                match_profile = profile.copy()

                break

        try:

            valid_user = User(**match)

            if match_profile:

                if match_profile.get("student_type") is None:

                    match_profile["student_type"] = "student"

                valid_profile = student_profile(**match_profile)

            else:

                valid_profile = None

            return {"user": valid_user, "student_profile": valid_profile}

        except Exception as e:

            print(f"Course {user.get("user_id")} still has invalid data: {e}")


    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e






