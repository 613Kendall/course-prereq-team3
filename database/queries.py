from typing import Any, cast
#query from supabase through init() 
from database.init_db import init

#supabase returns max of 1000 rows. using range() to get all the course/prereq group/prereq data
def get_all_rows(table_name):
    #initiate communication to supabase named client through init()
    client = init()

    all_rows = []
    start = 0
    page_size = 1000

    #loop to get all data past 1000th row
    #range(0, 999) -> range(1000, 1999) so on.
    while True:
        response= (
            #get data in table_name from supabase
            client.table(table_name)
            #all columns
            .select("*")
            .range(start, start + page_size -1)
            #send query
            .execute()
        )
        rows = response.data
        all_rows.extend(rows)
        #stop once we received less than 1000 rows
        if len(rows) < page_size:
            break
        
        start += page_size

    return all_rows
#query courses
def get_courses():
    return get_all_rows("courses")

#query prerequisite_groups
def get_prereq_groups():
    return get_all_rows("prerequisite_groups")

#query prerequisites
def get_prereqs():
    return get_all_rows("prerequisites")

#return all of them
def get_graph_data():
    return{
        "courses": get_courses(),
        "prerequisite_groups": get_prereq_groups(),
        "prerequisites": get_prereqs()
    }
def get_user_data(student_id):
    client = init()

    response = (
        client.table("course_history")
        .select("*")
        .eq("student_id", student_id)
        .execute()
    )
    return response.data
def get_course_offerings(course_id, term_id):
    client = init()

    response = (
        client.table("offerings")
        .select("*")
        .eq("course_id", course_id)
        .eq("term_id", term_id)
        .execute()
    )
    return cast(list[dict[str,Any]], response.data or[])
def get_external_credits(student_id):
    client = init()

    response = (
        client.table("external_credits")
        .select("*")
        .eq("student_id", student_id)
        .eq("approval_status", "approved")
        .execute()
    )
    return cast(list[dict[str,Any]], response.data or[])
'''
if __name__ == "__main__":
    print("courses:", len(get_courses()))
    print("groups:", len(get_prereq_groups()))
    print("prereqs:", len(get_prereqs()))
'''