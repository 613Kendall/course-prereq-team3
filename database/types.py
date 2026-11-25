from pydantic import BaseModel
from typing import Optional, Literal

# More table types can be added later if needed


class Course(BaseModel):
    course_id: int
    department_id: Optional[int]
    course_identifier: Optional[str]
    course_prefix: Optional[str]
    course_title: Optional[str]
    course_description: Optional[str]
    credits: Optional[float]
    course_level: Optional[str]
    is_repeatable: Optional[bool]


class Prerequisite(BaseModel):
    prerequisite_id: int
    prerequisite_group_id: Optional[int]
    prerequisite_course_id: Optional[int]
    negative_prerequisite: Optional[bool]
    min_grade: Optional[str]
    concurrent_allowed: Optional[bool]


class PrerequisiteGroup(BaseModel):
    prerequisite_group_id: int
    course_id: Optional[int]
    group_operator: Literal['AND', 'OR']
    parent_group_id: Optional[int]


class Department(BaseModel):
    department_id: int
    school_id: Optional[int]
    department_name: Optional[str]

class User(BaseModel):
    user_id: str
    first_name: str
    last_name: str
    email: str
    role: str
    created_at: Optional[str]

class student_profile(BaseModel):
    student_id: int
    user_id: str
    student_number: Optional[str] = None
    student_type: Optional[str] = "regular"
    degree_program_id: Optional[int] = None
    admission_year: Optional[int] = None
    catalog_year: Optional[int] = None
    expected_graduation: Optional[str] = None
    created_at: Optional[str] = None
    current_gpa: Optinal[float] = 0.0

class course_history(BaseModel):
    history_id: int
    student_id: int
    course_id: int
    term_id: int
    grade: Optional[str] = None
    status: str = "completed"
    credits_earned: float = 0.0
    created_at: Optional[str] = None

class external_credits(BaseModel):
    external_credit_id: int
    student_id: int
    credit_source: str
    source_institution: str
    original_course_or_exam: str
    original_grade: Optional[str] = None
    exam_score: Optional[int] = None
    original_credits: float = 0.0
    equivalent_course_id: Optional[int] = None
    credits_awarded: float = 0.0
    approval_status: str = "pending"
    policy_or_test_note: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: Optional[str] = None
