from fastapi import HTTPException, APIRouter
from database.init_db import supabase
from database.types import User, student_profile

#uses fast api
router = APIRouter()



#should only need to be used by admin to see all users
@router.get("/users")
def get_users():


    try:
    
        all_users =[]
        all_profiles = []
        size = 10
        start = 0


        while True:

            response = (

                supabase
                .table("users")
                .select("*")
                .order("user_id")
                .range(start, start + size -1)
                .execute()
            )

            response2 = (

                supabase
                .table("student_profiles")
                .select("*")
                .order("student_id")
                .range(start, start + size -1)
                .execute()
            )

            batch = response.data
            all_users.extend(batch)


            batch2 = response2.data
            all_profiles.extend(batch2)

            if len(batch) < size:

                break


            start += size


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

                        match["student_type"] = "regular"

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
def get_user(user_id: str):

    try:

        response = (
            supabase
            .table("users")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code  = 404, detail =f"user with user ID {user_id} does not exist")
    
        user = response.data[0].copy()

        if user.get("role") is None:

            user["role"] = "student"


        response2 = (

            supabase
            .table("student_profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        if response2.data:

            profile = response2.data[0].copy()

        else:

            profile = None


        try:

            valid_user = User(**user)

            if profile:

                if profile.get("student_type") is None:

                    match_profile["student_type"] = "regular"

                valid_profile = student_profile(**profile)

            else:

                valid_profile = None

            return {"user": valid_user, "student_profile": valid_profile}

        except Exception as e:

            print(f"Course {user.get("user_id")} still has invalid data: {e}")


    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e













