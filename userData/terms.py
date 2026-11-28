from fastapi import HTTPException, APIRouter
from database.init_db import supabase
from database.types import Term

#uses fast api
router = APIRouter()


@router.get("/terms")
def get_terms():

    try:

        all_terms = []
        size = 10
        start = 0


        while True:

            response = (

                supabase
                .table("terms")
                .select("*")
                .order("term_id")
                .range(start, start + size -1)
                .execute()
            )

            batch = response.data
            all_terms.extend(batch)

            if len(batch) < size:

                break


            start += size


        valid = []
        for term in all_terms:

            term = term.copy()

            if term.get("term_name") is None:

                term["term_name"] = "N/A"



            try:

                valid_term = Term(**term)

                valid.append(valid_term)

            except Exception as e:

                print(f"Term id {term.get("term_id")} still has invalid data: {e}")
 
        return valid

    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e

@router.get("/terms/{term_id}")
def get_term(term_id: int):

    try:

        response = (
            supabase
            .table("terms")
            .select("*")
            .eq("term_id", term_id)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code  = 404, detail =f"term id {term_id} does not exist")
    
        term = response.data[0].copy()

        if term.get("term_name") is None:

            term["term_name"] = "N/A"

        try:

            valid_term = Term(**term)
            return valid_term

        except Exception as e:

            print(f"Term id {term.get("term_id")} still has invalid data: {e}")

    except HTTPException:
        raise


    except Exception as e:

        raise HTTPException(status_code = 500, detail = str(e)) from e
 
