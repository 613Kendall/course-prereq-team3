import networkx as nx
from database.queries import get_user_data, get_graph_data, get_course_offerings, get_external_credits
from graph.prereq_graph import build_graph


#initialize
graph_data = get_graph_data()
G = build_graph(graph_data)

#get all the completed classes of user
def get_completed_courses(data):
    completed = {}
    for record in data:
        if record["status"]!="completed":
            continue
        course_id = record["course_id"]

        if course_id not in completed:
            completed[course_id] = []

        completed[course_id].append(record)
    return completed
#course offering validation
def course_offer_status(course_id, term_id):
    offerings = get_course_offerings(course_id, term_id)

    #no sections at all
    if not offerings:
        return "not_offered"
    
    #At least 1 open section
    if any(offering.get("status")=="Open" for offering in offerings):
        return "open"
    
    #No open sections but at least one waitlist section
    if any(offering.get("status")=="Waitlist Only" for offering in offerings):
        return "waitlist"
    
    #sections exist but are closed
    return "closed"
#get external credits
def get_external_courses(data):
    eq_courses = set()
    for record in data:
        course_id = record.get("equivalent_course_id")
        if course_id is not None:
            eq_courses.add(course_id)

    return eq_courses
#order letter grades to compare it with min_grade
grade_rank = {
    "A":4,
    "B":3,
    "C":2,
    "D":1,
    "F":0
}
#check if the class taken by user pass the minimum grade requirement
def min_grade_satisfaction(user_grade, min_grade):

    #withdraw, incomplete and Fail does not satisfy prereq
    if user_grade in ("F", "W", "I", None):
        return False
    
    #if prereq minimum grade is null in database Pass(P) satisfies prereq
    if user_grade=="P":
        return min_grade is None
    
    if user_grade not in grade_rank:
        return False
    #Pass if the minimum grade is Null and student has anything higher than F
    if min_grade is None:
        return grade_rank[user_grade]> grade_rank["F"]
    if min_grade not in grade_rank:
        return False
    return grade_rank[user_grade]>= grade_rank[min_grade]

#check if the student statisfies all prereqs
def course_prereq_satisfaction(G,prereq_course_id,group_id,completed_courses,external_courses):
    #store data of an edge between prereq course and prereq group
    edge_data = G.get_edge_data(prereq_course_id,group_id)
    if edge_data is None:
        return False

    min_grade = edge_data.get("min_grade")
    #check if this is a negative prerequisite
    negative = edge_data.get(
        "negative_prerequisite",
        False
    )
    #check the student's completed courses
    records = completed_courses.get(
        prereq_course_id,
        []
    )
    #
    completed = len(records) > 0
    #handle negative prereqs
    if negative:
        return (not completed and prereq_course_id not in external_courses)
    #return true if the student has equivalent external credits of the prereq
    if prereq_course_id in external_courses:
        return True
    #return false if the student did not complete a prereq
    if not completed:
        return False
    #check if student pass the minimum grade requirement
    return any(
        min_grade_satisfaction(record["grade"],min_grade)
        for record in records
)

#check recursively if prereq groups are satisfied
def evaluate_group(G, group_id, completed_courses,external_courses):
    #get group attributes from database
    group_data = G.nodes[group_id]
    #store operator of the group
    operator = group_data.get("operator")

    results = []
    #
    for predecessor in G.predecessors(group_id):
        node_data = G.nodes[predecessor]

        #predecessor is another prereq group
        if node_data.get("node_type") == "group":
            result = evaluate_group(
                G,
                predecessor,
                completed_courses,
                external_courses
            )
        #predecessor is a course: evaluate if the prereq is satisfied
        else:
            result = course_prereq_satisfaction(
                G,
                predecessor,
                group_id,
                completed_courses,
                external_courses
            )
        results.append(result)
    #if the root group operator is AND, every group and courses in results has to be true.
    if operator == "AND":
        return all(results)
    #if the root group operator is OR, only one of the groups or courses can be true.
    elif operator == "OR":
        return any(results)
    else:
        raise ValueError(
            f"Unknown operator: {operator}"
        )
#returns missing prereqs if the requirements are not satisfied
def get_unmet_prereqs(G,group_id, completed_courses, external_courses):
    #get attributes from prereq groups
    group_data = G.nodes[group_id]
    #get if the group is an and group or an or group
    operator = group_data.get("operator")

    requirements = []

    for predecessor in G.predecessors(group_id):
        node_data = G.nodes[predecessor]

        #nested prereq groups
        if node_data.get("node_type")=="group":
            child_result = get_unmet_prereqs(G,predecessor, completed_courses, external_courses)
            if child_result is not None:
                requirements.append(child_result)
        #Indivudual prereq course
        else:
            #check if the prereq is satisfied
            satisfied = course_prereq_satisfaction(G,predecessor,group_id,completed_courses,external_courses)
            #add to requirements array if not satisfied
            if not satisfied:
                requirements.append({
                    "type": "course",
                    "course_id": predecessor
                })
    #And group
    if operator == "AND":
        if not requirements:
            return None
        return {
            "type": "group",
            "operator": "AND",
            "requirements": requirements 
        }
    #Or groups
    elif operator =="OR":
        #if the groups is satisfied, there's no unment prereqs
        satisfied = evaluate_group(G,group_id,completed_courses,external_courses)
        if satisfied: 
            return None
        return {
            "type": "group",
            "operator": "OR",
            "requirements": requirements
        }
    else:
        raise ValueError(f"Unknown operator: {operator}")
#takes course id and goes through student class history to validate 
# if the student can take the target class and return eligibility status with reason/message
def course_validation(G, student_id, target_course_id, term_id):
    #if input cours id is invalid
    if target_course_id not in G:
        return {
            "eligible": False,
            "reason": "invalid_course",
            "message": "This course does not exist"
        }
    #get this student's course history from database
    student_history = get_user_data(student_id)

    #filter to only completed courses
    completed_courses = get_completed_courses(student_history)

    #get external credits of the student
    external_credit_data = get_external_credits(student_id)
    eq_courses = get_external_courses(external_credit_data)

    #get is_repeatable information of target class from prereq graph
    target_course_data = G.nodes[target_course_id]
    is_repeatable = target_course_data.get("is_repeatable", False)
    
    #if the target class is completed and not repeatable, 
    # the student cannot take the class
    if(target_course_id in completed_courses and not is_repeatable):
        return {
            "eligible": False,
            "reason": "already_completed",
            "message": "Course was already completed and not repeatable"
        }
    #Check if the course is offered in this term
    offering_status = course_offer_status(target_course_id,term_id)

    if offering_status == "not_offered":
        return {
            "eligible": False,
            "reason": "not_offered",
            "message": "This course is not offered this term"
        }

    if offering_status == "closed":
        return {
            "eligible": False,
            "reason": "offering_closed",
            "message": "This course is offered this term, but all sections are closed"
        }

    if offering_status == "waitlist":
        return {
            "eligible": False,
            "reason": "waitlist_only",
            "message": "This course is currently available by waitlist only"
        }
    
    root_groups = []
    #find root prereq group node that points directly to target course
    for predecessor in G.predecessors(target_course_id):
        #get attributes stored on the node
        node_data = G.nodes[predecessor]
        #check if the predecessor is actually a prereq group
        if node_data.get("node_type")=="group":
            #store group id in root_groups
            root_groups.append(predecessor)
    #no prereq groups = no prereqs
    if not root_groups:
        return {
            "eligible": True,
            "reason": "no_prerequisites",
            "message": "Student is eligible to take this course"
        }
    prereqs_satisfied = all(evaluate_group(G,group_id,completed_courses,eq_courses)
                            for group_id in root_groups)
    if not prereqs_satisfied:
        unmet_requirements = []

        for group_id in root_groups:
            unmet = get_unmet_prereqs(G,group_id,completed_courses,eq_courses)
            if unmet is not None:
                unmet_requirements.append(unmet)
        return {
            "eligible": False,
            "reason": "prerequisites_not_satisfied",
            "message": "Student has not satisfied the course prerequisites",
            "unmet_prerequisites": unmet_requirements
        }
    return {
        "eligible": True,
        "reason": "satisfy_all_prerequisites",
        "message": "Student is eligible to take this course"
    }
