from fastapi import HTTPException, APIRouter
from database.init_db import supabase
from database.types import course_history, external_credits

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
@router.get("/historys")
def get_planner():


    try:
    
        data = load_data()
        all_history = data.get("course_history", [])
        all_external = data.get("external_credits", [])
        valid_history = []

        for history in all_history:

            history = history.copy()

            if history.get("status") is None:

                history["status"] = "unknown"

            if history.get("credits_earned") is None:

                history["credits_earned"] = 0.0

            try:

                valid_history.append(course_history(**history))

            except Exception as e:

                print(f"Course history entry has invalid data: {e}")


        valid_external = []

        for external in all_external:

            external = external.copy()

            if external.get("approval_status") is None:

                external["approval_status"] = "pending"

            if external.get("credits_awarded") is None:

                external["credits_awarded"] = 0.0


            try:

                valid_external.append(external_credits(**external))

            except Exception as e:

                print(f"External credit {external.get("external_credit_id")} still has invalid data: {e}")



        return {"course_history": valid_history,"external_credits": valid_external}

    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e



@router.get("/historys/{student_id}")
def get_planners(student_id: int):


    try:
    
        data = load_data()
        all_history = data.get("course_history", [])
        all_external = data.get("external_credits", [])
        valid_history = []

        for history in all_history:

            if history.get("student_id") == student_id:

                history = history.copy()

                if history.get("status") is None:

                    history["status"] = "unknown"

                if history.get("credits_earned") is None:

                    history["credits_earned"] = 0.0

                try:

                    valid_history.append(course_history(**history))

                except Exception as e:

                    print(f"Course history entry has invalid data: {e}")


        valid_external = []

        for external in all_external:

            if external.get("student_id") == student_id:

                external = external.copy()

                if external.get("approval_status") is None:

                    external["approval_status"] = "pending"

                if external.get("credits_awarded") is None:

                    external["credits_awarded"] = 0.0


                try:

                    valid_external.append(external_credits(**external))

                except Exception as e:

                    print(f"External credit {external.get("external_credit_id")} still has invalid data: {e}")

        if not valid_history and not valid_external:

            raise HTTPException(status_code=404, detail=f"No course planner data found for student ID {student_id}")

        return {"student_id": student_id,"course_history": valid_history,"external_credits": valid_external}

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e




