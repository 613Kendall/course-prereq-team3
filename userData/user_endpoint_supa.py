#allows for access to other libraries and files
from fastapi import HTTPException, APIRouter
from database.init_db import supabase
from database.types import User, student_profile

#uses fast api
router = APIRouter()



#should only need to be used by admin to see all users, printas out all users and there profiles
@router.get("/users")
def get_users():


    #tries to get all users at once with 10 in each batch at a time
    try:
    
        all_users =[]
        all_profiles = []
        size = 10
        start = 0


        #while true get the data of profile and courses
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

            #places data in batches and into list
            batch = response.data
            all_users.extend(batch)


            batch2 = response2.data
            all_profiles.extend(batch2)

            #if batch is less then size break loop
            if len(batch) < size:

                break


            start += size


        #valid user that if spacific data is empty then replace with default values
        valid_users = []

        for user in all_users:

            user = user.copy()

            if user.get("role") is None:

                user["role"] = "student"

            #checks for a matching profile for user
            match = None
            for profile in all_profiles:

                if profile.get("user_id") == user.get("user_id"):

                    match = profile.copy()

                    break




            #if profiles match then  set default type if not already then place as valid profile
            try:

                valid_user = User(**user)

                if match:

                    if match.get("student_type") is None:

                        match["student_type"] = "regular"

                    valid_profile = student_profile(**match)

                else:

                    valid_profile = None

                #put both profile and user in a list
                valid_users.append({"user": valid_user, "student_profile": valid_profile})

            except Exception as e:

                print(f"Course {user.get("user_id")} still has invalid data: {e}")


        #return list
        return valid_users

    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e



#gets an individual user by there user id
@router.get("/users/{user_id}")
def get_user(user_id: str):

    #gets the user information from user table
    try:

        response = (
            supabase
            .table("users")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        #if no data desplay ther is none
        if not response.data:
            raise HTTPException(status_code  = 404, detail =f"user with user ID {user_id} does not exist")

        #if data then make copy as user
        user = response.data[0].copy()

        #default peramitors
        if user.get("role") is None:

            user["role"] = "student"

        #look for student profile
        response2 = (

            supabase
            .table("student_profiles")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        #if there is a profile then copy it as profile, if not set it to none
        if response2.data:

            profile = response2.data[0].copy()

        else:

            profile = None


        #makes a valid user , then makes a valid profile 
        try:

            valid_user = User(**user)

            if profile:

                if profile.get("student_type") is None:

                    profile["student_type"] = "regular"

                valid_profile = student_profile(**profile)

            else:

                valid_profile = None

            #combines profile and user and returns them 
            return {"user": valid_user, "student_profile": valid_profile}

        except Exception as e:

            print(f"Course {user.get("user_id")} still has invalid data: {e}")


    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e













