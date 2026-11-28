#access libraries
from fastapi import HTTPException, APIRouter
from pydantic import EmailStr, TypeAdapter,ValidationError
from database.init_db import init
from database.types import LoginRq
from userData.user_endpoint_supa import get_user

#connect to route based on team 3 specification
router = APIRouter(prefix="/auth", tags = ["auth"])

#checks for email validation
email_check = TypeAdapter(EmailStr)

#logins a user based on email and password
@router.post("/login")
def login(login_info: LoginRq):

#try email validation based on user input, output error if wrong
    try:

        valid_email = email_check.validate_python(login_info.email)

    except ValidationError:

        raise HTTPException(status_code= 400, detail = "invalid email")

#initilize user
    user = init()

#desplays what is being asked to the user, puts error if it is not correct
    try:

        auth_response = user.auth.sign_in_with_password({"email": valid_email, "password": login_info.password})


    except Exception:

        raise HTTPException(status_code = 401, detail = "invalid email or password")


#gets user id and token, and gets user data from id
    user_id = auth_response.user.id

    access_token = auth_response.session.access_token

    data = get_user(user_id)

#returns user data and token
    return{

        "access_token": access_token,
        "user": data["user"],
        "student_profile": data["student_profile"]

    }