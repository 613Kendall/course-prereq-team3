import networkx as nx
from database.queries import get_user_data, get_graph_data
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

def course_prereq_satisfaction(G,prereq_course_id,group_id,completed_courses):
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
        return not completed
    #return false if the student did not complete a prereq
    if not completed:
        return False
    #check if student pass the minimum grade requirement
    return any(
        min_grade_satisfaction(record["grade"],min_grade)
        for record in records
)

#check recursively if prereq groups are satisfied
def evaluate_group(G, group_id, completed_courses):
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
                completed_courses
            )
        #predecessor is a course: evaluate if the prereq is satisfied
        else:
            result = course_prereq_satisfaction(
                G,
                predecessor,
                group_id,
                completed_courses
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
#takes course id and goes through student class history to validate 
# if the student can take the target class and return True or False
def course_validation(G, student_id, target_course_id):
    #if input cours id is invalid
    if target_course_id not in G:
        raise ValueError(
            f"Course ID {target_course_id} not found"
        )
    #get this student's course history from database
    student_history = get_user_data(student_id)

    #filter to only completed courses
    completed_courses = get_completed_courses(student_history)

    #get is_repeatable information of target class from prereq graph
    target_course_data = G.nodes[target_course_id]
    is_repeatable = target_course_data.get("is_repeatable", False)
    
    #if the target class is completed and not repeatable, 
    # the student cannot take the class
    if(target_course_id in completed_courses and not is_repeatable):
        return False
    
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
        return True
    
    return all(
        #evaluate all prereqs
        evaluate_group(G, group_id, completed_courses) 
        for group_id in root_groups)