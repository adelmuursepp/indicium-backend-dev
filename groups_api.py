from firebase_admin import firestore
from flask import Blueprint, request
from http import HTTPStatus
from error_messages import ASSIGNMENT_DOES_NOT_EXIST, GROUP_DOES_NOT_EXIST
from helpers import check_authenticated, verify_is_teacher
from random import randrange
from k_modes_model import k_modes

import firebase
import uuid

groups_api = Blueprint("groups_api", __name__)


@groups_api.route("/api/create_group", methods=["POST"])
@check_authenticated
def create_group():
    request_json = request.json
    course_id = request_json["courseId"]
    assignment_id = request_json["assignmentId"]
    group_id = str(uuid.uuid4())
    group_name = request_json["groupName"].strip()

    if (
        not firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
        .get()
        .exists
    ):
        return (
            ASSIGNMENT_DOES_NOT_EXIST.format(assignment_id, course_id),
            HTTPStatus.NOT_FOUND,
        )

    data = firebase.create_group(course_id, assignment_id, group_id, group_name)
    return data, HTTPStatus.OK


@groups_api.route("/api/delete_group", methods=["POST"])
@check_authenticated
def delete_group():
    uid = request.user["uid"]
    verify_is_teacher(uid)

    request_json = request.json
    course_id = request_json["courseId"]
    assignment_id = request_json["assignmentId"]
    group_id = request_json["groupId"]

    group_doc_ref = (
        firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
        .collection("groups")
        .document(group_id)
    )
    if group_doc_ref.get().exists:
        group_doc_ref.delete()

    return "Success", HTTPStatus.OK


@groups_api.route(
    "/api/courses/<course_id>/assignments/<assignment_id>/groups", methods=["GET"]
)
@check_authenticated
def get_groups(course_id: str, assignment_id: str):
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

    groups = [
        group.to_dict() for group in assignment_doc_ref.collection("groups").stream()
    ]

    for group in groups:
        group["students"] = [
            firebase.get_user(student_uid) for student_uid in group["students"]
        ]

    return {"groups": groups}, HTTPStatus.OK


@groups_api.route("/api/join_group", methods=["POST"])
@check_authenticated
def join_group():
    request_json = request.json
    course_id = request_json["courseId"]
    assignment_id = request_json["assignmentId"]
    group_id = request_json["groupId"]

    group_doc_ref = (
        firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
        .collection("groups")
        .document(group_id)
    )

    if not group_doc_ref.get().exists:
        return (
            GROUP_DOES_NOT_EXIST.fomat(group_id, assignment_id, course_id),
            HTTPStatus.NOT_FOUND,
        )

    uid = request.user["uid"]
    find_and_leave_group(course_id, assignment_id, uid)
    group_doc_ref.update({"students": firestore.ArrayUnion([uid])})

    return group_doc_ref.get().to_dict(), HTTPStatus.OK


@groups_api.route("/api/leave_group", methods=["POST"])
@check_authenticated
def leave_group():
    request_json = request.json
    course_id = request_json["courseId"]
    assignment_id = request_json["assignmentId"]
    group_id = request_json["groupId"]

    group_doc_ref = (
        firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
        .collection("groups")
        .document(group_id)
    )

    if not group_doc_ref.get().exists:
        return (
            GROUP_DOES_NOT_EXIST.fomat(group_id, assignment_id, course_id),
            HTTPStatus.NOT_FOUND,
        )

    uid = request.user["uid"]
    group_doc_ref.update({"students": firestore.ArrayRemove([uid])})

    return group_doc_ref.get().to_dict(), HTTPStatus.OK


@groups_api.route("/api/form_groups", methods=["POST"])
@check_authenticated
def form_groups():
    request_json = request.json
    # From request object get kmeans/kmodels/smth
    course_id = request_json["courseId"]
    assignment_id = request_json["assignmentId"]

    # Get all students
    student_uids = (
        firebase.courses_collection_ref.document(course_id)
        .get(field_paths=["students"])
        .to_dict()
        .get("students")
    )

    # Get all groups
    groups_response, _ = get_groups(course_id, assignment_id)
    groups = groups_response["groups"]

    # Get all students not in a group
    students_in_groups = []
    for group in groups:
        students_in_groups.extend([student["uid"] for student in group["students"]])

    students_in_groups = set(students_in_groups)
    all_students = set(student_uids)
    students_not_in_groups = list(all_students - students_in_groups)

    # Get the survey data for all students
    students_data = {}
    for student_uid in students_not_in_groups:
        students_data[student_uid] = get_student_scores(student_uid)

    # Form groups
    size = 2
    num_of_centroids = 5
    if len(students_data) < max(size, num_of_centroids):
        form_group(course_id, assignment_id, students_not_in_groups)
    else:
        for group in k_modes(students_data, size):
            form_group(course_id, assignment_id, group)

    return "Formed groups", HTTPStatus.CREATED


def find_and_leave_group(course_id: str, assignment_id: str, uid: str):
    groups = [
        group.to_dict()
        for group in firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
        .collection("groups")
        .stream()
    ]
    for group in groups:
        if uid in group["students"]:
            leave_group(course_id, assignment_id, group["groupId"], uid)


def leave_group(course_id: str, assignment_id: str, group_id: str, uid: str):
    group_doc_ref = (
        firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
        .collection("groups")
        .document(group_id)
    )
    group_doc_ref.update({"students": firestore.ArrayRemove([uid])})


def form_group(course_id, assignment_id, student_uids):
    group_name = "GROUP {}".format(randrange(100))
    group_id = str(uuid.uuid4())
    firebase.create_group(course_id, assignment_id, group_id, group_name)
    add_students_to_group(course_id, assignment_id, group_id, student_uids)


def get_student_scores(uid):
    """
    Get survey data for uid. If there's no survey data for a student, return neutral scores.
    """
    neutral = 3
    num_questions = 15
    default_scores = [neutral for _ in range(num_questions)]

    user = firebase.users_collection_ref.document(uid).get().to_dict()
    if len(user.get("scores")) > 0:
        return user.get("scores")
    return default_scores


def add_students_to_group(
    course_id: str, assignment_id: str, group_id: str, student_uids: list
):
    group_doc_ref = (
        firebase.courses_collection_ref.document(course_id)
        .collection("assignments")
        .document(assignment_id)
        .collection("groups")
        .document(group_id)
    )
    group_doc_ref.update({"students": firestore.ArrayUnion(student_uids)})
    return group_doc_ref.get().to_dict()
