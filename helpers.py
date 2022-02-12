from error_messages import (
    STUDENTS_NOT_AUTHORIZED_TO_PERFORM_ACTION,
    TEACHERS_NOT_AUTHORIZED_TO_PERFORM_ACTION,
)
from flask import request, jsonify
from functools import wraps
from http import HTTPStatus
from InvalidUsage import InvalidUsage

import firebase


def check_authenticated(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        id_token = request.cookies.get("idToken")
        firebase.verify_token(id_token)
        user_info = firebase.get_user_info_from_token(id_token)
        uid = user_info["uid"]
        user_info = firebase.get_user(uid)
        data = {
            "uid": uid,
            "email": user_info["email"],
            "email_verified": user_info["emailVerified"],
            "student": user_info["student"],
            "idToken": firebase.get_token(uid).decode(),
        }
        request.user = data
        return f(*args, **kwargs)

    return wrap


def verify_is_student(uid: str):
    user = firebase.get_user(uid)
    if not user["student"]:
        raise InvalidUsage(
            message=TEACHERS_NOT_AUTHORIZED_TO_PERFORM_ACTION,
            status_code=HTTPStatus.UNAUTHORIZED,
        )


def verify_is_teacher(uid: str):
    user = firebase.get_user(uid)
    if user["student"]:
        raise InvalidUsage(
            message=STUDENTS_NOT_AUTHORIZED_TO_PERFORM_ACTION,
            status_code=HTTPStatus.UNAUTHORIZED,
        )
