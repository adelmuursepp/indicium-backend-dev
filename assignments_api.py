from flask import Blueprint, request
from firebase_admin import firestore
from http import HTTPStatus
from error_messages import ASSIGNMENT_DOES_NOT_EXIST, COURSE_DOES_NOT_EXIST
from helpers import check_authenticated, verify_is_teacher

import firebase
import uuid

assignments_api = Blueprint("assignments_api", __name__)


@assignments_api.route("/api/create_assignment", methods=["POST"])
@check_authenticated
def create_assignment():
    uid = request.user["uid"]
    verify_is_teacher(uid)

    request_json = request.json
    assignment_id = str(uuid.uuid4())
    course_id = request_json["course_id"].strip()

    if not firebase.courses_collection_ref.document(course_id).get().exists:
        return COURSE_DOES_NOT_EXIST.format(course_id), HTTPStatus.NOT_FOUND

    create_assignment_doc(course_id, assignment_id, request_json)
    return "Success", HTTPStatus.OK


@assignments_api.route("/api/<course_id>/assignments", methods=["GET"])
@check_authenticated
def get_assignments(course_id: str):
    course_doc_ref = firebase.courses_collection_ref.document(course_id)

    if not course_doc_ref.get().exists:
        return COURSE_DOES_NOT_EXIST.fomat(course_id), HTTPStatus.NOT_FOUND

    assignments = [
        assignment.to_dict()
        for assignment in course_doc_ref.collection("assignments").stream()
    ]
    return {"assignments": assignments}, HTTPStatus.OK


@assignments_api.route("/api/<course_id>/assignments/<assignment_id>", methods=["GET"])
@check_authenticated
def get_assignment(course_id: str, assignment_id: str):
    assignment_doc_ref = (
        firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
    )

    if not assignment_doc_ref.get().exists:
        return (
            ASSIGNMENT_DOES_NOT_EXIST.fomat(assignment_id, course_id),
            HTTPStatus.NOT_FOUND,
        )

    return assignment_doc_ref.get().to_dict(), HTTPStatus.OK


@assignments_api.route("/api/delete_assignment", methods=["POST"])
@check_authenticated
def delete_assignment():
    uid = request.user["uid"]
    request_json = request.json
    course_id = request_json["courseId"]
    assignment_id = request_json["assignmentId"]

    verify_is_teacher(uid)
    firebase.delete_assignment(course_id, assignment_id)

    return "Deleted", HTTPStatus.OK


# Create assignment document inside course
def create_assignment_doc(course_id: str, assignment_id: str, request_json: dict):
    courses_doc_ref = firebase.courses_collection_ref.document(course_id)
    assignment_collection_ref = courses_doc_ref.collection("assignments")
    assignment_doc_ref = assignment_collection_ref.document(assignment_id)

    assignment_data = {
        "assignmentId": assignment_id,
        "assignmentName": request_json["name"].strip(),
        "due": request_json["due"].strip(),
    }
    assignment_doc_ref.set(assignment_data)

    students = request_json["students"]
    student_uids = firebase.create_students(students)
    if len(student_uids) > 0:
        courses_doc_ref.update({"students": firestore.ArrayUnion(student_uids)})

    return assignment_data
