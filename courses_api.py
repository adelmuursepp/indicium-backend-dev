from flask import Blueprint, jsonify, request
from firebase_admin import auth, firestore
from firebase_admin.exceptions import FirebaseError
from http import HTTPStatus
from error_messages import USER_WITH_UID_NOT_FOUND, INVALID_UID
from helpers import check_authenticated, verify_is_teacher

import firebase
import uuid

courses_api = Blueprint("courses_api", __name__)


@courses_api.route("/api/course", methods=["POST"])
@check_authenticated
def add_course():
    """
    Request JSON parameters:
    - course_id: str
    - course: str
    - description: str
    - term: str
    - year: str
    """
    try:
        request_json = request.json
        course_id = str(uuid.uuid4())
        uid = request.user["uid"]

        # check if the user's info is found, if not then break out
        if not firebase.user_doc_exists(uid):
            return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND

        verify_is_teacher(uid)

        course, code = search_course(request_json)
        if code == HTTPStatus.OK:
            return "Course Already Exists!", HTTPStatus.CONFLICT

        # create a course document, with the course, course_id, description, term stored under a uuid
        course_data = create_course_doc(course_id, request_json, uid)
        return course_data, HTTPStatus.OK

    except ValueError:
        return INVALID_UID.format(uid), HTTPStatus.BAD_REQUEST
    except auth.UserNotFoundError:
        return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND
    except FirebaseError as e:
        return e.cause, e.code


@courses_api.route("/api/enroll_course", methods=["POST"])
@check_authenticated
def enroll_course():
    """
    Request JSON parameters:
    - course: str
    - year: str
    - term: str
    """

    try:
        request_json = request.json
        uid = request.user["uid"]

        if not firebase.user_doc_exists(uid):
            return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND
        course_id, code = search_course(request_json)

        if code != HTTPStatus.OK:  # check if the course exists
            return "Course Does Not Exist!", HTTPStatus.NOT_FOUND

        if check_if_enrolled(
            uid, course_id
        ):  # check if the user is already in the course
            return "You are already enrolled in the course!", HTTPStatus.BAD_REQUEST

        user_doc_ref = firebase.users_collection_ref.document(uid)
        user_doc_ref.update({"courses": firestore.ArrayUnion([course_id])})
        courses_doc_ref = firebase.courses_collection_ref.document(course_id)
        courses_doc_ref.update({"students": firestore.ArrayUnion([uid])})
        return "Success", HTTPStatus.OK

    except ValueError:
        return INVALID_UID.format(uid), HTTPStatus.BAD_REQUEST
    except auth.UserNotFoundError:
        return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND
    except FirebaseError as e:
        return e.cause, e.code


@courses_api.route("/api/courses", methods=["GET"])
@check_authenticated
def get_courses():
    try:
        uid = request.user["uid"]
        list_of_courses = []
        # check if the user's info is found, if not then break out
        if not firebase.user_doc_exists(uid):
            return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND

        list_of_courses_codes = (
            firebase.users_collection_ref.document(uid).get().get("courses")
        )  # retrieve the uid for all courses a user is enrolled in
        user_doc_ref = firebase.users_collection_ref.document(uid)

        if list_of_courses_codes == {}:  # if a user has no courses, return empty dict
            return {"courses": []}, HTTPStatus.OK
        for course_id in list_of_courses_codes:
            course_info = get_course(
                course_id
            )  # retrieve the info (term, courseName, description, courseId) for each course
            if (
                course_info == {}
            ):  # if there is no info about a certain course, remove course_id from list of enrolled courses
                user_doc_ref.update({"courses": firestore.ArrayRemove([course_id])})
            else:
                list_of_courses.append(
                    course_info
                )  # append the course into the json response
        return jsonify({"courses": list_of_courses}), HTTPStatus.OK

    except ValueError:
        return INVALID_UID.format(uid), HTTPStatus.BAD_REQUEST
    except auth.UserNotFoundError:
        return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND
    except FirebaseError as e:
        return e.cause, e.code


@courses_api.route("/api/course/<course_id>", methods=["GET"])
@check_authenticated
def get_course_info(course_id: str):
    uid = request.user["uid"]
    if not firebase.user_doc_exists(uid):
        return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND

    if course_id not in firebase.users_collection_ref.document(uid).get().get(
        "courses"
    ):
        return (
            "User not enrolled in course with id {}".format(course_id),
            HTTPStatus.UNAUTHORIZED,
        )

    return (
        firebase.courses_collection_ref.document(course_id).get().to_dict(),
        HTTPStatus.OK,
    )


@courses_api.route("/api/leave_course/<course_id>", methods=["DELETE"])
@check_authenticated
def leave_course(course_id: str):
    try:
        uid = request.user["uid"]
        if not firebase.user_doc_exists(uid):
            return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND
        if not check_if_enrolled(
            uid, course_id
        ):  # check if the user is enrolled in the course
            return "You are not enrolled in the course!", HTTPStatus.BAD_REQUEST

        user = firebase.get_user(uid)
        if user["student"]:
            return leave_student_course(uid, course_id)
        return leave_professor_course(uid, course_id)

    except ValueError:
        return INVALID_UID.format(uid), HTTPStatus.BAD_REQUEST
    except auth.UserNotFoundError:
        return USER_WITH_UID_NOT_FOUND.format(uid), HTTPStatus.NOT_FOUND
    except FirebaseError as e:
        return e.cause, e.code


@courses_api.route("/api/get_students/<course_id>", methods=["GET"])
@check_authenticated
def get_students(course_id: str):
    student_uids = (
        firebase.courses_collection_ref.document(course_id)
        .get(field_paths=["students"])
        .to_dict()
        .get("students")
    )
    students = []
    if student_uids:
        students = [firebase.get_user(student_uid) for student_uid in student_uids]
    return {"students": students}, HTTPStatus.OK


@courses_api.route("/api/remove_student", methods=["POST"])
@check_authenticated
def remove_student():
    uid = request.user["uid"]
    request_json = request.json
    course_id = request_json["courseId"]
    student_id = request_json["studentId"]
    verify_is_teacher(uid)
    return leave_student_course(student_id, course_id)


def leave_professor_course(uid: str, course_id: str):
    # check if the course exists in the db
    course = get_course(course_id)
    if course == {}:  # course does not exist
        leave_student_course(
            uid, course_id
        )  # leave the course from the user's perspective (there is no actual course to delete)
    else:
        # remove the course from professor's enrolled courses + remove course from collection
        firebase.users_collection_ref.document(uid).update(
            {"courses": firestore.ArrayRemove([course_id])}
        )
        firebase.courses_collection_ref.document(course_id).delete()
    return "Success", HTTPStatus.OK


def leave_student_course(uid: str, course_id: str):
    # delete the course from user's course collection
    firebase.users_collection_ref.document(uid).update(
        {"courses": firestore.ArrayRemove([course_id])}
    )
    firebase.courses_collection_ref.document(course_id).update(
        {"students": firestore.ArrayRemove([uid])}
    )

    assignment_docs = (
        firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .stream()
    )
    for assignment in assignment_docs:
        group_docs = assignment.reference.collection("groups").stream()
        for group in group_docs:
            group.reference.update({"students": firestore.ArrayRemove([uid])})

    return "Success", HTTPStatus.OK


# Retrieve information (courseId, course, description, term) about a specifc course
def get_course(course_id: str):
    course_doc_ref = firebase.courses_collection_ref.document(course_id)
    doc = course_doc_ref.get()
    if not doc.exists:
        return {}
    course_info = course_doc_ref.get()
    course_data = {
        "courseId": course_info.get("courseId"),
        "course": course_info.get("course"),
        "description": course_info.get("description"),
        "term": course_info.get("term"),
        "year": course_info.get("year"),
    }
    return course_data


# search a course based on given parameters
def search_course(request_json: dict):
    courses = (
        firebase.courses_collection_ref.where(
            "course", "==", request_json["courseName"].strip().upper()
        )
        .where("term", "==", request_json["term"].strip())
        .where("year", "==", request_json["year"].strip())
        .get()
    )
    if courses:
        return courses[0].get("courseId"), HTTPStatus.OK
    return "No Course Found", HTTPStatus.NOT_FOUND


# Check if a user is enrolled into a specific course, returns Boolean accordingly
def check_if_enrolled(uid: str, course_id: str):
    user_courses = firebase.users_collection_ref.document(uid).get().get("courses")
    return course_id in user_courses


# Create course document, with the properties: course_id, course, description
def create_course_doc(course_id: str, request_json: dict, uid: str):
    courses_doc_ref = firebase.courses_collection_ref.document(course_id)
    user_doc_ref = firebase.users_collection_ref.document(uid)
    course_data = {
        "courseId": course_id,
        "course": request_json["courseName"].strip().upper(),
        "description": request_json["description"].strip(),
        "term": request_json["term"],
        "year": request_json["year"].strip(),
    }
    courses_doc_ref.set(course_data)
    user_doc_ref.update({"courses": firestore.ArrayUnion([course_id])})

    return course_data
