#imports t access 
from fastapi import HTTPException, APIRouter
from database.init_db import supabase
from database.types import course_history, external_credits



#uses fast api
router = APIRouter()


#should only need to be used by admin to see all users, gets all users history and external credits in the database
@router.get("/historys")
def get_history():

#tries to get all courses at once, 10 at a time
    try:
    
        all_history = []
        all_external = []
        size = 10
        start = 0

        #while true get the data of courses and credits
        while True:

            response = (

                supabase
                .table("course_history")
                .select("*")
                .order("history_id")
                .range(start, start + size -1)
                .execute()
            )

            response2 = (

                supabase
                .table("external_credits")
                .select("*")
                .order("external_credit_id")
                .range(start, start + size -1)
                .execute()
            )

            #places data in batches and into list
            batch = response.data
            all_history.extend(batch)

            batch2 = response2.data
            all_external.extend(batch2)

            #if the length of a batch is bigger then the other, set that as the max, then break if below size
            if len(batch) < len(batch2):

                max = len(batch2)

            else:

                max = len(batch)

            if max < size:

                break

            start += size

        

        #valid history  thaat if spacific data is empty then replace with default
        valid_history = []
        for history in all_history:

            history = history.copy()

            if history.get("status") is None:

                history["status"] = "unknown"

            if history.get("credits_earned") is None:

                history["credits_earned"] = 0.0

            try:

                #sends data to list
                valid_history.append(course_history(**history))

            except Exception as e:

                print(f"Course history entry has invalid data: {e}")


        #valid credits that if specific data is empty then replace with default
        valid_external = []

        for external in all_external:

            external = external.copy()

            if external.get("approval_status") is None:

                external["approval_status"] = "pending"

            if external.get("credits_awarded") is None:

                external["credits_awarded"] = 0.0


            try:

                #sends to list
                valid_external.append(external_credits(**external))

            except Exception as e:

                print(f"External credit {external.get("external_credit_id")} still has invalid data: {e}")



        #returns course history nand external credits
        return {"course_history": valid_history,"external_credits": valid_external}

    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e


#gets the history and external credits of a specifdied user based on student id
@router.get("/historys/{student_id}")
def get_history(student_id: int):


    #creates the students credits and course history from there student id
    try:
    
        response = (
            supabase
            .table("course_history")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        response2 = (
            supabase
            .table("external_credits")
            .select("*")
            .eq("student_id", student_id)
            .execute()
        )

        #if no data in either then the history doesnt exist
        if not response.data and not response2.data:
            raise HTTPException(status_code  = 404, detail =f"students with student ID {student_id} does not have cousres history or external credits")

        
        #valid history  thaat if spacific data is empty then replace with default
        valid_history = []

        for history in response.data:

            historys = history.copy()

            if historys.get("status") is None:

                historys["status"] = "unknown"

            if historys.get("credits_earned") is None:

                historys["credits_earned"] = 0.0

            try:

                valid_history.append(course_history(**historys))

            except Exception as e:

                print(f"Course history entry has invalid data: {e}")


         #valid credits that if specific data is empty then replace with default
        valid_external = []

        for external in response2.data:

            externals = external.copy()

            if externals.get("approval_status") is None:

                externals["approval_status"] = "pending"

            if externals.get("credits_awarded") is None:

                externals["credits_awarded"] = 0.0


            try:

                valid_external.append(external_credits(**externals))

            except Exception as e:

                print(f"External credit {external.get("external_credit_id")} still has invalid data: {e}")


        #returns the student id, there history of credits and classes
        return {"student_id": student_id,"course_history": valid_history,"external_credits": valid_external}

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e




