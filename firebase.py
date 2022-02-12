from error_messages import (
    INVALID_EMAIL,
    USER_WITH_EMAIL_NOT_FOUND,
    USER_WITH_UID_NOT_FOUND,
    INVALID_UID,
)
from firebase_admin import auth, firestore
from firebase_admin.auth import ExpiredIdTokenError
from firebase_admin.exceptions import FirebaseError
from functools import partial
from http import HTTPStatus
from InvalidUsage import InvalidUsage
from google.api_core.exceptions import InvalidArgument

import firebase_admin
import os
import json

API_KEY = os.environ["FIREBASE_API_KEY"]

firebase_accounts_api = partial(
    "https://identitytoolkit.googleapis.com/v1/accounts:{method}?key={key}".format,
    key=API_KEY,
)

error_messages = {
    "EMAIL_EXISTS": "The email address provided is already in use by another account.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "We have blocked this device due to unusual activity. Try again later.",
    "WEAK_PASSWORD : Password should be at least 6 characters": "Password is weak. Password should be at least 6 characters.",
    "EMAIL_NOT_FOUND": "An account with this email does not exist.",
    "INVALID_PASSWORD": "Invalid password.",
    "USER_DISABLED": "This user account has been disabled by an administrator.",
    "INVALID_EMAIL": "Invalid email address.",
    "MISSING_PASSWORD": "No password entered. Enter a password.",
}

firebase_app = firebase_admin.initialize_app()
db = firestore.client(app=firebase_app)
users_collection_ref = db.collection("users")
courses_collection_ref = db.collection("courses")


def get_token(uid):
    return auth.create_custom_token(uid)


def verify_token(id_token):
    try:
        auth.verify_id_token(id_token, firebase_app, False)
    except Exception:
        raise InvalidUsage(
            message="Invalid token.", status_code=HTTPStatus.UNAUTHORIZED
        )


def get_user_info_from_token(id_token):
    try:
        if id_token == None:
            raise InvalidUsage(
                message="No token provided.", status_code=HTTPStatus.UNAUTHORIZED
            )
        return auth.verify_id_token(id_token, firebase_app, False)
    except ExpiredIdTokenError:
        raise InvalidUsage(
            message="Token expired.", status_code=HTTPStatus.UNAUTHORIZED
        )
    except Exception:
        raise InvalidUsage(
            message="Invalid token.", status_code=HTTPStatus.UNAUTHORIZED
        )


def get_user(uid: str):
    try:
        user_record = auth.get_user(uid, firebase_app)
        user_doc = users_collection_ref.document(uid).get(
            field_paths=["student", "avatar"]
        )
        user_data = {
            "email": user_record.email,
            "name": parse_user_name_from_email(user_record.email),
            "emailVerified": user_record.email_verified,
            "student": user_doc.get("student"),
            "avatar": user_doc.get("avatar"),
            "uid": uid,
        }
        return user_data
    except ValueError:
        raise InvalidUsage(
            message=INVALID_UID.format(uid), status_code=HTTPStatus.BAD_REQUEST
        )
    except auth.UserNotFoundError:
        raise InvalidUsage(
            message=USER_WITH_UID_NOT_FOUND.format(uid),
            status_code=HTTPStatus.NOT_FOUND,
        )
    except FirebaseError as e:
        raise InvalidUsage(message=e.cause, status_code=e.code)


def get_user_by_email(email: str):
    try:
        user_record = auth.get_user_by_email(email, firebase_app)
        return user_record
    except ValueError:
        raise InvalidUsage(
            message=INVALID_EMAIL.format(email), status_code=HTTPStatus.BAD_REQUEST
        )
    except auth.UserNotFoundError:
        raise InvalidUsage(
            message=USER_WITH_EMAIL_NOT_FOUND.format(email),
            status_code=HTTPStatus.NOT_FOUND,
        )
    except FirebaseError as e:
        raise InvalidUsage(message=e.cause, status_code=e.code)


def update_avatar(uid: str, avatar: str):
    try:
        users_collection_ref.document(uid).update({"avatar": avatar})
    except InvalidArgument as e:
        raise InvalidUsage(message=e.message, status_code=e.code)
    except FirebaseError as e:
        raise InvalidUsage(message=e.cause, status_code=e.code)


def update_password(uid: str, new_password: str):
    try:
        auth.update_user(uid, password=new_password)
    except ValueError as e:
        raise InvalidUsage(message=str(e), status_code=HTTPStatus.BAD_REQUEST)
    except auth.UserNotFoundError:
        raise InvalidUsage(
            message=USER_WITH_UID_NOT_FOUND.format(uid),
            status_code=HTTPStatus.NOT_FOUND,
        )
    except FirebaseError as e:
        raise InvalidUsage(message=e.cause, status_code=e.code)


def create_user_doc(uid: str, student: bool, avatar: str):
    try:
        user_doc_ref = users_collection_ref.document(uid)
        if not student:
            user_doc_ref.set(
                {"uid": uid, "student": student, "courses": [], "avatar": avatar}
            )
        if student:
            user_doc_ref.set(
                {
                    "uid": uid,
                    "student": student,
                    "courses": [],
                    "avatar": avatar,
                    "scores": [],
                }
            )

    except FirebaseError as e:
        raise InvalidUsage(message=e.cause, status_code=e.code)


def user_doc_exists(uid: str):
    user_doc_ref = users_collection_ref.document(uid)
    doc = user_doc_ref.get()
    return doc.exists


def create_students(students: list):
    student_uids = []
    for student in students:
        if "name" not in student:
            raise InvalidUsage(
                "No student name provided " + student, HTTPStatus.BAD_REQUEST
            )
        elif student["name"] == "":
            raise InvalidUsage(
                "Student name is empty: " + student, HTTPStatus.BAD_REQUEST
            )
        elif "email" not in student:
            raise InvalidUsage(
                "No student email provided " + student, HTTPStatus.BAD_REQUEST
            )
        elif student["email"] == "":
            raise InvalidUsage(
                "Student email is empty: " + student, HTTPStatus.BAD_REQUEST
            )

    for student in students:
        try:
            uid = auth.create_user(
                display_name=student["name"], email=student["email"]
            ).uid
            create_user_doc(uid, student=True, avatar="")
        except auth.EmailAlreadyExistsError:
            uid = get_user_by_email(student["email"]).uid
        student_uids.append(uid)
    return student_uids


def parse_user_name_from_email(email: str):
    info = email.split("@")[0]
    first_name, last_name = info.split(".")
    name = first_name.capitalize() + " " + last_name.capitalize()
    return name


def create_group(course_id: str, assignment_id: str, group_id: str, group_name: str):
    try:
        group_document_ref = (
            courses_collection_ref.document(course_id)
            .collection("assignments")
            .document(assignment_id)
            .collection("groups")
            .document(group_id)
        )

        data = {"groupId": group_id, "groupName": group_name, "students": []}
        group_document_ref.set(data)
        return data
    except FirebaseError as e:
        raise InvalidUsage(message=e.cause, status_code=e.code)


def delete_assignment(course_id: str, assignment_id):
    assignment_doc_ref = (
        courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
    )
    group_docs = assignment_doc_ref.collection("groups").stream()
    for doc in group_docs:
        doc.reference.delete()
    assignment_doc_ref.delete()


def delete_group(course_id: str, assignment_id: str, group_id: str):
    pass
